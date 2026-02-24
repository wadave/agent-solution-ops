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

// components/ChatUI.tsx
'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Menu, Settings, HelpCircle, ChevronRight, MessageSquare } from 'lucide-react';
import Image from 'next/image';
import { Message, Session, StreamEvent, MessageEvent, Conversation } from '@/types/chat';
import { api } from '@/services/api';
import { useGoogleAuth } from '@/app/providers/GoogleAuthProvider';
import { EventView, StreamEventView } from './EventViews';

export default function ChatUI() {
  const { isAuthenticated, isLoading: authLoading, error: authError, userProfile, setUserProfile } = useGoogleAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      type: 'bot',
      content: (process.env.NEXT_PUBLIC_AGENT_INTRO_MESSAGE || 'Hi there! What can I help you with today?').replace(/"/g, ''),
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [streamingEvents, setStreamingEvents] = useState<StreamEvent[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      // Only initialize if we don't have a session yet (first load)
      if (!session) {
        initializeSession();
      }
    }
  }, [isAuthenticated, authLoading]); // Removed session dependency to avoid loop, but added check inside

  const initializeSession = async () => {
    try {
      const userId = `user_${Date.now()}`;
      const newSession = await api.createSession(userId);
      setSession(newSession);
      console.log('Session initialized:', newSession);

      // Now that a token has been acquired for the session, fetch user info
      const token = await api.getCurrentToken();
      if (token && !userProfile) {
        fetchUserInfo(token);
      }
    } catch (error) {
      console.error('Failed to initialize session:', error);
      if (error instanceof Error && error.message.includes('401')) {
        setError('Authentication required. Google sign-in will prompt automatically.');
      } else {
        setError('Failed to connect to the agent. Please refresh the page.');
      }
    }
  };

  const fetchUserInfo = async (token: string) => {
    try {
      const response = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error('Failed to fetch user info');
      }
      const data = await response.json();
      setUserProfile({ name: data.name, picture: data.picture });
    } catch (error) {
      console.error('Error fetching user profile:', error);
      // Do not block the UI for this, just log the error
    }
  };

  const saveCurrentConversation = () => {
    if (!session) return;
    
    // Don't save if it's just the intro message
    if (messages.length <= 1 && messages[0].type === 'bot') return;

    setConversations(prev => {
      const existingIndex = prev.findIndex(c => c.id === session.session_id);
      // Use first user message as title, or timestamp
      const title = messages.find(m => m.type === 'user')?.content.slice(0, 30) || `Conversation ${new Date().toLocaleTimeString()}`;
      
      const updatedConv: Conversation = {
        id: session.session_id,
        title: existingIndex >= 0 ? prev[existingIndex].title : title,
        messages: messages,
        session: session,
        timestamp: new Date()
      };

      if (existingIndex >= 0) {
        const newConvs = [...prev];
        newConvs[existingIndex] = updatedConv;
        return newConvs;
      } else {
        return [updatedConv, ...prev];
      }
    });
  };

  const handleNewConversation = async () => {
    saveCurrentConversation();
    setMessages([{
      id: Date.now(),
      type: 'bot',
      content: (process.env.NEXT_PUBLIC_AGENT_INTRO_MESSAGE || 'Hi there! What can I help you with today?').replace(/"/g, ''),
      timestamp: new Date(),
    }]);
    setSession(null);
    await initializeSession();
  };

  const handleLoadConversation = (conv: Conversation) => {
    if (session?.session_id === conv.id) return; // Already loaded
    saveCurrentConversation();
    setMessages(conv.messages);
    setSession(conv.session);
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading || !session) return;

    const userMessage: Message = {
      id: Date.now(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    const loadingMessage: Message = {
      id: Date.now() + 1,
      type: 'bot',
      content: 'loading',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      const botMessageId = Date.now() + 2;

      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== loadingMessage.id);
        return [...filtered, {
          id: botMessageId,
          type: 'bot',
          content: '',
          timestamp: new Date(),
        }];
      });

      setIsWaitingForResponse(true);
      setStreamingEvents([]); // Clear previous events

      const accumulatedEvents: StreamEvent[] = [];

      await api.sendMessageStream(
        session.user_id,
        session.session_id,
        userMessage.content,
        (event: StreamEvent) => {
          accumulatedEvents.push(event);
          setStreamingEvents([...accumulatedEvents]);

          if (event.type === 'end') {
            setIsWaitingForResponse(false);

            let finalContent = '';
            const messageEvents: MessageEvent[] = [];
            for (const ev of accumulatedEvents) {
              if (ev.type === 'agent_transfer') {
                messageEvents.push({
                  type: 'agent_transfer',
                  agentName: ev.transfer_to_agent || 'unknown',
                });
              } else if (ev.type === 'tool_start') {
                messageEvents.push({
                  type: 'tool_start',
                  tool: ev.tool || 'unknown',
                });
              } else if (ev.type === 'tool_response') {
                const isError = ev.response?.isError || false;
                messageEvents.push({
                  type: 'tool_response',
                  tool: ev.tool || 'unknown',
                  response: ev.response,
                  isError: isError,
                });
              } else if (ev.type === 'content' && ev.content) {
                finalContent += ev.content;
              }
            }

            setMessages(prev => prev.map(msg =>
              msg.id === botMessageId
                ? { ...msg, content: finalContent, events: messageEvents }
                : msg
            ));
            setStreamingEvents([]); // Clear events after processing
          } else if (event.type === 'error') {
            setError(`Error: ${event.error}`);
            setIsWaitingForResponse(false);
            setStreamingEvents([]);
          }
        }
      );
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));

      // Check if it's an auth error
      if (error instanceof Error && error.message.includes('401')) {
        setError('Authentication expired. Please refresh the page to sign in again.');
      } else {
        setMessages(prev => [...prev, {
          id: Date.now(),
          type: 'bot',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date(),
        }]);
        setError(error instanceof Error ? error.message : 'An error occurred');
      }
    } finally {
      setIsLoading(false);
      setIsWaitingForResponse(false);
    }
  };

  const formatContent = (content: string) => {
    // ... (keep your existing formatContent function as is)
    // Helper function to parse inline markdown (bold, italic, code)
    const parseInlineMarkdown = (text: string): React.ReactNode[] => {
      const elements: React.ReactNode[] = [];
      let lastIndex = 0;

      // Combined regex for all inline patterns
      const inlineRegex = /(\*{2,3}(.+?)\*{2,3}|\*(.+?)\*|`(.+?)`)/g;

      let match;
      while ((match = inlineRegex.exec(text)) !== null) {
        // Add text before the match
        if (match.index > lastIndex) {
          elements.push(text.slice(lastIndex, match.index));
        }

        if (match[2]) {
          // Bold + Italic (***text***)
          elements.push(
            <strong key={`bi-${match.index}`} className="italic">
              {match[2]}
            </strong>
          );
        } else if (match[3]) {
          // Bold (**text**)
          elements.push(
            <strong key={`b-${match.index}`}>
              {match[3]}
            </strong>
          );
        } else if (match[4]) {
          // Italic (*text*)
          elements.push(
            <em key={`i-${match.index}`}>
              {match[4]}
            </em>
          );
        } else if (match[5]) {
          // Code (`text`)
          elements.push(
            <code key={`c-${match.index}`} className="px-1 py-0.5 bg-gray-100 rounded text-sm">
              {match[5]}
            </code>
          );
        }

        lastIndex = match.index + match[0].length;
      }

      // Add remaining text
      if (lastIndex < text.length) {
        elements.push(text.slice(lastIndex));
      }

      return elements.length > 0 ? elements : [text];
    };

    return content.split('\n').map((line, i) => {
      // Handle headers
      if (line.startsWith('### ')) {
        return (
          <h3 key={i} className="text-lg font-semibold mt-4 mb-2">
            {parseInlineMarkdown(line.slice(4))}
          </h3>
        );
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={i} className="text-xl font-semibold mt-4 mb-2">
            {parseInlineMarkdown(line.slice(3))}
          </h2>
        );
      }
      if (line.startsWith('# ')) {
        return (
          <h1 key={i} className="text-2xl font-semibold mt-4 mb-2">
            {parseInlineMarkdown(line.slice(2))}
          </h1>
        );
      }

      // Handle code blocks
      if (line.startsWith('```')) {
        // This is simplified - in production you'd want to handle multi-line code blocks
        return (
          <div key={i} className="bg-gray-100 p-2 rounded my-2 font-mono text-sm">
            {line.slice(3)}
          </div>
        );
      }

      // Handle blockquotes
      if (line.startsWith('> ')) {
        return (
          <blockquote key={i} className="border-l-4 border-gray-300 pl-4 my-2 italic">
            {parseInlineMarkdown(line.slice(2))}
          </blockquote>
        );
      }

      // Handle bullet points with * or -
      if (line.match(/^[-*]\s+/)) {
        const bulletContent = line.replace(/^[-*]\s+/, '');
        return (
          <div key={i} className="flex items-start ml-4 mb-1">
            <span className="mr-2 mt-1">•</span>
            <span className="flex-1">{parseInlineMarkdown(bulletContent)}</span>
          </div>
        );
      }

      // Handle numbered lists
      if (line.match(/^\d+\.\s+/)) {
        const listContent = line.replace(/^\d+\.\s+/, '');
        const number = line.match(/^(\d+)\./)?.[1];
        return (
          <div key={i} className="flex items-start ml-4 mb-1">
            <span className="mr-2">{number}.</span>
            <span className="flex-1">{parseInlineMarkdown(listContent)}</span>
          </div>
        );
      }

      // Handle bullet points with • character (backward compatibility)
      if (line.startsWith('• ')) {
        return (
          <div key={i} className="flex items-start ml-4 mb-1">
            <span className="mr-2">•</span>
            <span className="flex-1">{parseInlineMarkdown(line.slice(2))}</span>
          </div>
        );
      }

      // Handle horizontal rules
      if (line.match(/^---+\$/) || line.match(/^\*\*\*+$/)) {
        return <hr key={i} className="my-4 border-gray-300" />;
      }

      // Handle tool indicators (your custom patterns)
      if (line.startsWith('🔧')) {
        return (
          <div key={i} className="text-blue-600 font-medium mb-1">
            {parseInlineMarkdown(line)}
          </div>
        );
      }

      if (line.startsWith('✅')) {
        return (
          <div key={i} className="text-green-600 mb-1">
            {parseInlineMarkdown(line)}
          </div>
        );
      }

      if (line.startsWith('❌')) {
        return (
          <div key={i} className="text-red-600 mb-1">
            {parseInlineMarkdown(line)}
          </div>
        );
      }

      // Regular paragraph
      const trimmedLine = line.trim();
      if (trimmedLine) {
        return (
          <div key={i} className="mb-1">
            {parseInlineMarkdown(line)}
          </div>
        );
      }

      // Empty line
      return <div key={i} className="h-4" />;
    });
  };

  // Show loading state while auth is initializing
  if (authLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-xl">Initializing...</div>
      </div>
    );
  }

  // Show error if auth failed
  if (authError) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">Authentication Error</div>
          <div className="text-gray-600">{authError}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Reload Page
          </button>
        </div>
      </div>
    );
  }

  // Your existing chat UI JSX continues here...
  return (
    <div className="flex h-screen bg-white">
      {/* Keep all your existing JSX exactly as is */}
      {/* Sidebar */}
      <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col">
        {/* ... rest of your component ... */}
        <div className="p-4 border-b border-gray-200">
          <button 
            onClick={handleNewConversation}
            className="w-full flex items-center justify-between px-4 py-3 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <span className="text-sm font-medium text-gray-700">New conversation</span>
            <ChevronRight className="w-4 h-4 text-gray-400" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Conversations</h3>
            <div className="space-y-1">
              {conversations.map((conv) => (
                <div 
                  key={conv.id}
                  onClick={() => handleLoadConversation(conv)}
                  className={`flex items-center px-3 py-2 rounded-lg cursor-pointer ${
                    session?.session_id === conv.id ? 'bg-blue-50' : 'hover:bg-gray-100'
                  }`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${
                    session?.session_id === conv.id ? 'bg-blue-100' : 'bg-gray-200'
                  }`}>
                    <MessageSquare className={`w-4 h-4 ${
                      session?.session_id === conv.id ? 'text-blue-600' : 'text-gray-500'
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${
                      session?.session_id === conv.id ? 'text-blue-600' : 'text-gray-900'
                    }`}>
                      {conv.title}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {conv.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
              {conversations.length === 0 && (
                 <p className="text-sm text-gray-400 px-3 py-2">No saved conversations</p>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-center p-4 bg-gray-100 rounded-lg">
            <div className="text-center">
              {/* Logo placeholder */}
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button className="p-2 hover:bg-gray-100 rounded-lg mr-4">
                <Menu className="w-5 h-5 text-gray-600" />
              </button>
              <div>
                <h1 className="text-lg font-medium text-gray-900" style={{ fontFamily: 'Google Sans, Roboto, sans-serif' }}>{(process.env.NEXT_PUBLIC_AGENT_NAME || 'ADK Agent').replace(/"/g, '')}</h1>
                <p className="text-sm text-gray-500">{(process.env.NEXT_PUBLIC_AGENT_DESCRIPTION || 'I\'m here to help!').replace(/"/g, '')}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button className="p-2 hover:bg-gray-100 rounded-lg">
                <HelpCircle className="w-5 h-5 text-gray-600" />
              </button>
              <button className="p-2 hover:bg-gray-100 rounded-lg">
                <Settings className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {(error || authError) && (
          <div className="bg-red-50 border-b border-red-200 px-6 py-3">
            <div className="flex items-center text-red-700">
              <span className="text-sm">{error || authError}</span>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto bg-white">
          <div className="max-w-3xl mx-auto py-8 px-6">
            {messages.map((message) => (
              <div key={message.id} className="mb-8">
                <div className="flex items-start">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 flex-shrink-0 ${
                    message.type === 'user'
                      ? 'bg-blue-500'
                      : 'bg-gray-100'
                  }`}>
                    {message.type === 'user' ? (
                      userProfile?.picture ? (
                        <Image
                          src={userProfile.picture}
                          alt="User Avatar"
                          width={32}
                          height={32}
                          className="rounded-full object-cover"
                        />
                      ) : (
                        <span className="text-white text-sm font-medium">U</span>
                      )
                    ) : (
                      <Image
                        src="/assets/adk_logo.png"
                        alt="Agent Avatar"
                        width={24}
                        height={24}
                        className="rounded-full"
                      />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900 mb-1">
                      {message.type === 'user' ? 'You' : 'Agent'}
                    </div>
                    <div className="text-gray-700">
                      {(message.content === 'loading' || (message.type === 'bot' && message.content === '' && isWaitingForResponse && messages[messages.length - 1].id === message.id)) ? (
                        <div className="flex items-center space-x-1">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-red-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '450ms' }}></div>
                          </div>
                        </div>
                      ) : (
                        <div className="prose prose-sm max-w-none">
                          {message.events && message.events.map((event, index) => (
                            <EventView key={index} event={event} />
                          ))}
                          {formatContent(message.content)}
                        </div>
                      )}
                      {isWaitingForResponse && messages[messages.length - 1].id === message.id && (
                        <div className="mt-2">
                          {streamingEvents.map((event, index) => (
                            <StreamEventView key={index} event={event} />
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white px-6 py-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-end space-x-4">
              <div className="flex-1">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Type a message..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={1}
                  disabled={isLoading || !session}
                />
              </div>
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading || !session}
                className={`p-3 rounded-lg transition-all ${
                  input.trim() && !isLoading && session
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <div className="mt-2 text-xs text-gray-500 text-center">
              {/* Footer text */}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
