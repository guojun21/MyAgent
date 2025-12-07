import React, { useState, useEffect, useRef } from 'react';
import { api, Workspace, Conversation } from './services/api';
import { StructuredContext } from './components/StructuredContext/StructuredContext';
import { StructuredContextData } from './types';

interface Message {
  role: string;
  content: string;
  structured_context?: StructuredContextData;
}

function App() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState<string | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load workspaces on mount
  useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    try {
      const list = await api.getWorkspaces();
      // 确保 list 是数组，如果是 undefined/null 则设为空数组
      const safeList = Array.isArray(list) ? list : (list?.workspaces || []);
      setWorkspaces(safeList);
      
      const active = safeList.find(w => w.active);
      if (active) {
        setCurrentWorkspaceId(active.id);
        await loadConversations(active.id);
      } else if (safeList.length > 0) {
        switchWorkspace(safeList[0].id);
      }
    } catch (e) {
      console.error('[App] 加载工作空间失败:', e);
      setWorkspaces([]); // 失败时重置为空数组，防止 map 报错
    }
  };

  const switchWorkspace = async (id: string) => {
    await api.switchWorkspace(id);
    setCurrentWorkspaceId(id);
    await loadConversations(id);
  };

  const loadConversations = async (wsId: string) => {
    try {
      const list = await api.getConversations();
      const safeList = Array.isArray(list) ? list : [];
      setConversations(safeList);

      const active = safeList.find(c => c.active);
      if (active) {
          setCurrentConversationId(active.id);
          loadContext(active.id);
      } else if (safeList.length > 0) {
          switchConversation(safeList[0].id);
      } else {
          setMessages([]);
          setCurrentConversationId(null);
      }
    } catch (e) {
      console.error('[App] 加载会话列表失败:', e);
      setConversations([]);
      }
  };

  const switchConversation = async (id: string) => {
      await api.switchConversation(id);
      setCurrentConversationId(id);
      loadContext(id);
  };

  const createConversation = async () => {
      if (!currentWorkspaceId) return;
      const { conversation_id } = await api.createConversation(currentWorkspaceId);
      loadConversations(currentWorkspaceId); // Reload list
  };

  const loadContext = async (id: string) => {
      const ctx = await api.getContext(id);
      if (ctx && ctx.messages) {
          setMessages(ctx.messages);
      }
  };

  const sendMessage = async () => {
      if (!input.trim() || !currentConversationId) return;
      const userMsg = input;
      setInput('');
      setLoading(true);
      
      // Optimistic update
      const tempUserMsg: Message = { role: 'user', content: userMsg };
      setMessages(prev => [...prev, tempUserMsg]);

      try {
          const res = await api.sendMessage(userMsg, currentConversationId);
          // Reload context to get the full structured response
          // Alternatively, construct it from res.data if structure matches
          loadContext(currentConversationId);
      } catch (e) {
          console.error(e);
          alert('Send failed');
      } finally {
          setLoading(false);
      }
  };

  useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex h-screen bg-gray-100 font-sans text-sm">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 border-b border-gray-700">
            <h2 className="text-lg font-bold mb-2">Workspaces</h2>
            <select 
                className="w-full bg-gray-800 p-2 rounded text-white"
                value={currentWorkspaceId || ''}
                onChange={(e) => switchWorkspace(e.target.value)}
            >
                {Array.isArray(workspaces) && workspaces.map(w => (
                    <option key={w.id} value={w.id}>{w.name}</option>
                ))}
            </select>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2">
            <div className="flex justify-between items-center mb-2 px-2">
                <h3 className="text-gray-400 font-bold text-xs uppercase">Conversations</h3>
                <button onClick={createConversation} className="text-blue-400 hover:text-blue-300 text-xs">+</button>
            </div>
            {Array.isArray(conversations) && conversations.map(c => (
                <div 
                    key={c.id}
                    onClick={() => switchConversation(c.id)}
                    className={`p-2 rounded cursor-pointer mb-1 ${currentConversationId === c.id ? 'bg-blue-600' : 'hover:bg-gray-800'}`}
                >
                    <div className="truncate">{c.name || 'Untitled'}</div>
                    <div className="text-xs text-gray-400">{c.message_count} msgs</div>
                </div>
            ))}
        </div>
      </div>

      {/* Main Chat */}
      <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="h-12 bg-white border-b flex items-center px-4 justify-between">
              <h1 className="font-bold">
                  {conversations.find(c => c.id === currentConversationId)?.name || 'Chat'}
              </h1>
              {loading && <span className="text-blue-500 text-xs">Running...</span>}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-3xl rounded-lg p-3 ${msg.role === 'user' ? 'bg-blue-100' : 'bg-white border border-gray-200'}`}>
                          <div className="font-bold text-xs text-gray-500 mb-1 uppercase">{msg.role}</div>
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                          
                          {/* Render Structured Context if available */}
                          {msg.structured_context && (
                              <StructuredContext data={msg.structured_context} />
                          )}
                      </div>
                  </div>
              ))}
              <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 bg-white border-t">
              <div className="flex gap-2">
                  <textarea 
                      className="flex-1 border rounded p-2 h-20 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Type a message..."
                      value={input}
                      onChange={e => setInput(e.target.value)}
                      onKeyDown={e => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              sendMessage();
                          }
                      }}
                  />
                  <button 
                      disabled={loading}
                      onClick={sendMessage}
                      className="px-6 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                      Send
                  </button>
              </div>
          </div>
      </div>
    </div>
  );
}

export default App;
