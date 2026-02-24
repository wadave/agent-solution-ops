/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */



import { Session, StreamEvent } from '@/types/chat';

// Google Agent Engine configuration
const AGENT_ENGINE_URL = (process.env.NEXT_PUBLIC_AGENT_ENGINE_URL || 'unset').replace(/"/g, '');
if (AGENT_ENGINE_URL === 'unset') {
  console.warn('Warning: NEXT_PUBLIC_AGENT_ENGINE_URL is not set. Please set it in your environment variables.');
}

const GOOGLE_CLOUD_SCOPE = 'https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email';

// Google token client instance
let tokenClient: TokenClient | null = null;
let accessToken: string | null = null;
let tokenExpiresAt: number | null = null;

// Initialize Google OAuth2 token client
export function initializeGoogleAuth(clientId: string): void {
  if (typeof window === 'undefined' || !window.google) {
    throw new Error('Google Identity Services library not loaded');
  }

  tokenClient = window.google.accounts.oauth2.initTokenClient({
    client_id: clientId,
    scope: GOOGLE_CLOUD_SCOPE,
    callback: (response: TokenResponse) => {
      if (response.error) {
        console.error('Token error:', response);
        throw new Error(response.error);
      }

      accessToken = response.access_token;
      // Token expires in response.expires_in seconds
      tokenExpiresAt = Date.now() + (parseInt(response.expires_in) * 1000) - 60000; // Refresh 1 minute early
    },
  });
}

// Get a valid access token, refreshing if necessary
async function getAccessToken(): Promise<string> {
  return new Promise((resolve, reject) => {
    // Check if we have a valid token
    if (accessToken && tokenExpiresAt && Date.now() < tokenExpiresAt) {
      resolve(accessToken);
      return;
    }

    // Need to get a new token
    if (!tokenClient) {
      reject(new Error('Google Auth not initialized. Call initializeGoogleAuth first.'));
      return;
    }

    // Set up one-time callback for this request
    const originalCallback = tokenClient.callback;
    tokenClient.callback = (response: TokenResponse) => {
      if (response.error) {
        reject(new Error(response.error));
        return;
      }

      accessToken = response.access_token;
      tokenExpiresAt = Date.now() + (parseInt(response.expires_in) * 1000) - 60000;

      // Restore original callback
      tokenClient!.callback = originalCallback;

      resolve(accessToken);
    };

    // Request the token
    tokenClient.requestAccessToken();
  });
}

// Alternative: Use Google Sign-In for more seamless experience
export async function signInWithGoogle(): Promise<void> {
  if (!tokenClient) {
    throw new Error('Google Auth not initialized. Call initializeGoogleAuth first.');
  }

  return new Promise((resolve, reject) => {
    const originalCallback = tokenClient!.callback;

    tokenClient!.callback = (response: TokenResponse) => {
      if (response.error) {
        reject(new Error(response.error));
        return;
      }

      accessToken = response.access_token;
      tokenExpiresAt = Date.now() + (parseInt(response.expires_in) * 1000) - 60000;

      // Restore original callback
      tokenClient!.callback = originalCallback;

      resolve();
    };

    // This will show the Google consent screen
    tokenClient?.requestAccessToken({ prompt: 'consent' });
  });
}

// Revoke the token and clear stored credentials
export function signOut(): void {
  if (accessToken) {
    window.google.accounts.oauth2.revoke(accessToken, () => {
      accessToken = null;
      tokenExpiresAt = null;
      console.log('Access token revoked');
    });
  }
}

export const api = {
  // Create a new session
  createSession: async (userId: string): Promise<Session> => {
    try {
      const token = await getAccessToken();

      const response = await fetch(`${AGENT_ENGINE_URL}:query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          class_method: 'create_session',
          input: {
            user_id: userId,
          }
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const data = await response.json();
      console.log('Session response:', data);

      // Handle double-nested output structure
      const sessionData = data.output?.output || data.output || data;

      // Return properly formatted session
      return {
        session_id: sessionData.id,
        user_id: sessionData.userId,
        ...sessionData
      } as Session;
    } catch (error) {
      console.error('Error creating session:', error);
      throw error;
    }
  },

  // Send message with streaming response
  sendMessageStream: async (
    userId: string,
    sessionId: string,
    message: string,
    onEvent: (event: StreamEvent) => void
  ): Promise<void> => {
    try {
      const token = await getAccessToken();

      const response = await fetch(`${AGENT_ENGINE_URL}:streamQuery`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          class_method: 'stream_query',
          input: {
            user_id: userId,
            session_id: sessionId,
            message: message,
            ui_oauth_token: token,
          }
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Split by newlines and process complete lines
        const lines = buffer.split('\n');

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          // Skip empty lines
          if (!line.trim()) continue;

          console.log(`line: ${line}`)

          try {
            // Parse the JSON response
            const data = JSON.parse(line);

            // Extract text content from the response structure
            if (data?.content?.parts[0]?.text) {
              console.log(`data.content: ${data.content.parts[0].text}`)
              onEvent({
                type: 'content',
                content: data.content.parts[0].text,
                metadata: {
                  author: data.author,
                  id: data.id,
                  timestamp: data.timestamp || new Date().toISOString(),
                  usage: data.usage_metadata
                },
                timestamp: data.timestamp || new Date().toISOString(),
              } as StreamEvent);
            }

            if (data?.content?.parts[0]?.function_response) {
              console.log(`data.function_response`)
              if (data.content.parts[0].function_response.name == 'transfer_to_agent') {
                onEvent({
                  type: 'agent_transfer',
                  author: data.author,
                  transfer_to_agent: data.actions?.transfer_to_agent,
                  metadata: {
                    author: data.author,
                    id: data.id,
                    timestamp: data.timestamp || new Date().toISOString(),
                    usage: data.usage_metadata
                  },
                  timestamp: data.timestamp || new Date().toISOString(),
                } as StreamEvent);
              } else {
                onEvent({
                  type: 'tool_response',
                  tool: data.content.parts[0].function_response.name,
                  response: data.content.parts[0].function_response.response,
                  timestamp: new Date().toISOString(),
                } as StreamEvent);
              }
            }

            if (data?.content?.parts[0]?.function_call) {
              console.log(`data.function_call`)
              onEvent({
                  type: 'tool_start',
                  tool: data.content.parts[0].function_call.name,
                  toolId: data.content.parts[0].function_call.id,
                  timestamp: new Date().toISOString(),
              } as StreamEvent);
            }

            // Handle tool calls if present
            if (data.tool_calls) {
              console.log(`tool_calls:`)
              for (const toolCall of data.tool_calls) {
                onEvent({
                  type: 'tool_start',
                  tool: toolCall.name,
                  toolId: toolCall.id,
                  timestamp: data.timestamp || new Date().toISOString(),
                } as StreamEvent);
              }
            }

            // Handle custom metadata for a2a responses
            if (data.custom_metadata?.['a2a:response']?.history) {
              for (const message of data.custom_metadata['a2a:response'].history) {
                if (message.role === 'agent' && message.parts) {
                  for (const part of message.parts) {
                    if (part.kind === 'data' && part.metadata?.adk_type === 'function_call') {
                      onEvent({
                        type: 'tool_start',
                        tool: part.data.name,
                        timestamp: new Date().toISOString(),
                      } as StreamEvent);
                    } else if (part.kind === 'data' && part.metadata?.adk_type === 'function_response') {
                      onEvent({
                        type: 'tool_response',
                        tool: part.data.name,
                        response: part.data.response,
                        timestamp: new Date().toISOString(),
                      } as StreamEvent);
                    }
                  }
                }
              }
            }

            // Handle A2A specific error messages
            if (data.error_message && data.custom_metadata?.['a2a:error']) {
              onEvent({
                type: 'error',
                error: data.error_message,
                timestamp: new Date().toISOString(),
              } as StreamEvent);
            }

          } catch (e) {
            console.error('Error parsing response line:', e, 'Line:', line);
          }
        }
      }

      // Process any remaining data in buffer
      if (buffer.trim()) {
        try {
          const data = JSON.parse(buffer);
          if (data.content && data.content.parts && data.content.parts[0] && data.content.parts[0].text) {
            onEvent({
              type: 'content',
              content: data.content.parts[0].text,
              metadata: {
                author: data.author,
                id: data.id,
                timestamp: data.timestamp || new Date().toISOString(),
                usage: data.usage_metadata
              },
              timestamp: data.timestamp || new Date().toISOString(),
            } as StreamEvent);
          }
        } catch (e) {
          console.error('Error parsing final buffer:', e);
        }
      }
      onEvent({
        type: 'end',
        timestamp: new Date().toISOString(),
      } as StreamEvent);
    } catch (error) {
      console.error('Error in sendMessageStream:', error);
      throw error;
    }
  },

  // Check if user is authenticated
  isAuthenticated: (): boolean => {
    return accessToken !== null && tokenExpiresAt !== null && Date.now() < tokenExpiresAt;
  },

  // Get current access token (for debugging)
  getCurrentToken: (): string | null => {
    return accessToken;
  },
};

// TypeScript declarations for Google Identity Services
declare global {
  interface Window {
    google: {
      accounts: {
        oauth2: {
          initTokenClient: (config: TokenClientConfig) => TokenClient;
          revoke: (accessToken: string, callback: () => void) => void;
        };
      };
    };
  }
}

interface TokenClientConfig {
  client_id: string;
  scope: string;
  callback: (response: TokenResponse) => void;
  prompt?: string;
  enable_serial_consent?: boolean;
}

interface TokenClient {
  callback: (response: TokenResponse) => void;
  requestAccessToken: (overrideConfig?: { prompt?: string }) => void;
}

interface TokenResponse {
  access_token: string;
  expires_in: string;
  error?: string;
  error_description?: string;
}
