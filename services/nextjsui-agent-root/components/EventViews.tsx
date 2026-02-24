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

// components/EventViews.tsx
'use client';

import { useState } from 'react';
import { ChevronRight } from 'lucide-react';
import { ToolResponse, AgentTransfer, ToolStart, MessageEvent, StreamEvent } from '@/types/chat';

export const ToolStartView = ({ event }: { event: ToolStart }) => {
  return (
    <div className="my-2 flex items-center">
      <span className="mr-2">🔧</span>
      <span className="text-sm text-gray-600">
        Using tool: {event.tool}
      </span>
    </div>
  );
};

export const ToolResponseView = ({ event }: { event: ToolResponse }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { tool, response, isError } = event;

  const results = response?.result?.structuredContent?.results;
  const sqlQuery = response?.result?.structuredContent?.sql_query;
  const contentToDisplay = results ? results : response;

  return (
    <div className="my-2">
      <div
        className="cursor-pointer flex items-center"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="mr-2">{isError ? '❌' : '✅'}</span>
        <span className={`text-sm ${isError ? 'text-red-600' : 'text-green-600'}`}>
          {tool} completed
        </span>
        <ChevronRight className={`w-4 h-4 ml-1 text-gray-500 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
      </div>
      {isExpanded && (
        <>
          {sqlQuery && (
            <pre className="bg-gray-100 p-2 rounded mt-1 text-xs overflow-x-auto">
              <strong>SQL Query:</strong> {sqlQuery}
            </pre>
          )}
          <pre className="bg-gray-100 p-2 rounded mt-1 text-xs overflow-x-auto">
            {JSON.stringify(contentToDisplay, null, 2)}
          </pre>
        </>
      )}
    </div>
  );
};

export const AgentTransferView = ({ event }: { event: AgentTransfer }) => {
  return (
    <div className="text-blue-600 font-medium mb-1">
      👤 Transfer to agent: {event.agentName}
    </div>
  );
};

export const EventView = ({ event }: { event: MessageEvent }) => {
  switch (event.type) {
    case 'tool_start':
      return <ToolStartView event={event} />;
    case 'tool_response':
      return <ToolResponseView event={event} />;
    case 'agent_transfer':
      return <AgentTransferView event={event} />;
    default:
      return null;
  }
};

export const StreamEventView = ({ event }: { event: StreamEvent }) => {
  switch (event.type) {
    case 'agent_transfer':
      return (
        <div className="text-sm text-gray-500">
          👤 Transfer to agent: {event.transfer_to_agent || 'unknown'}
        </div>
      );
    case 'tool_start':
      return (
        <div className="text-sm text-gray-500">
          🔧 Using tool: {event.tool || 'unknown'}
        </div>
      );
    case 'tool_response': {
      const isError = event.response?.isError;
      const results = event.response?.result?.structuredContent?.results;
      const sqlQuery = event.response?.result?.structuredContent?.sql_query;
      const contentToDisplay = results ? results : event.response;

      return (
        <div className="text-sm text-gray-500">
          <div>{isError ? '❌' : '✅'} {event.tool || 'unknown'} completed</div>
          <pre className="bg-gray-100 p-2 rounded mt-1 text-xs">
            {sqlQuery}
            {JSON.stringify(contentToDisplay, null, 2)}
          </pre>
        </div>
      );
    }

    default:
      return null;
  }
};
