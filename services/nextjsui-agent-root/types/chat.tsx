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

export interface ToolStart {
  type: 'tool_start';
  tool: string;
}

export interface ToolResponse {
  type: 'tool_response';
  tool: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  response: any;
  isError: boolean;
}

export interface AgentTransfer {
  type: 'agent_transfer';
  agentName: string;
}

export type MessageEvent = ToolStart | ToolResponse | AgentTransfer;

export interface Message {
  id: number;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  events?: MessageEvent[];
}

export interface Session {
  session_id: string;
  user_id: string;
  created_at: string;
}

export interface StreamEvent {
  type: 'start' | 'content' | 'tool_start' | 'tool_response' | 'tool_end' | 'end' | 'error' | 'agent_transfer';
  author?: string;
  transfer_to_agent?: string;
  content?: string;
  tool?: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  response?: any;
  error?: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  session: Session | null;
  timestamp: Date;
}
