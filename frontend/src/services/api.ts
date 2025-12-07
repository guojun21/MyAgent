const API_BASE = 'http://localhost:11241/api';

export interface Workspace {
  id: string;
  name: string;
  path: string;
  active: boolean;
  conversation_count: number;
}

export interface Conversation {
  id: string;
  name: string;
  active: boolean;
  message_count: number;
  last_active: string;
}

export const api = {
  getWorkspaces: async (): Promise<Workspace[]> => {
    const res = await fetch(`${API_BASE}/workspaces`);
    const json = await res.json();
    return json.data;
  },

  switchWorkspace: async (wsId: string) => {
    await fetch(`${API_BASE}/workspaces/${wsId}/switch`, { method: 'POST' });
  },

  getConversations: async (): Promise<Conversation[]> => {
    const res = await fetch(`${API_BASE}/conversations`);
    const json = await res.json();
    return json.data;
  },

  createConversation: async (workspaceId: string) => {
    const res = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: workspaceId })
    });
    return await res.json();
  },

  switchConversation: async (convId: string) => {
    await fetch(`${API_BASE}/conversations/${convId}/switch`, { method: 'POST' });
  },

  sendMessage: async (message: string, conversationId: string) => {
    const res = await fetch(`${API_BASE}/agent/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id: conversationId })
    });
    return await res.json();
  },

  getContext: async (conversationId: string) => {
    const res = await fetch(`${API_BASE}/context/${conversationId}`);
    const json = await res.json();
    return json.data;
  },
  
  compactContext: async (conversationId: string) => {
      await fetch(`${API_BASE}/context/${conversationId}/compact`, { method: 'POST' });
  },
  
  renameWorkspace: async (wsId: string, newName: string) => {
      await fetch(`${API_BASE}/workspaces/${wsId}/rename`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ new_name: newName })
      });
  },
  
  renameConversation: async (convId: string, newName: string) => {
      await fetch(`${API_BASE}/conversations/${convId}/rename`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ new_name: newName })
      });
  }
};

