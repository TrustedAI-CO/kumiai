// Core type definitions for the application

export interface McpServer {
  id: string;
  name: string;
  command: string;
  description: string;
  config?: Record<string, unknown>;
  status?: 'active' | 'inactive';
}

export interface SkillMetadata {
  id: string;
  name: string;
  description: string;
  tags: string[];
  icon?: string;
  iconColor?: string;
  category?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Agent {
  id: string;
  name: string;
  agent_id: string;
  description?: string;
  model?: string;
  skills: string[];
  mcp_servers?: string[];
  color?: string;
  status?: 'active' | 'idle' | 'error';
  selected_specialists?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  team_members: string[];
  skills: string[];
  status: 'active' | 'archived' | 'completed';
  created_at?: string;
  updated_at?: string;
}

export interface Session {
  id: string;
  agent_id: string;
  project_id?: string;
  status: 'active' | 'idle' | 'completed' | 'error';
  created_at: string;
  updated_at?: string;
  messages?: Message[];
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

export interface ChatContext {
  agentId?: string;
  sessionId?: string;
  projectId?: string;
  skillId?: string;
}

// Utility types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}
