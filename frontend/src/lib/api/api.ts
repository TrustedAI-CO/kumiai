// API client for backend
import type { McpServer } from '@/types';

// Use environment variable or construct from current hostname
const getApiBase = () => {
  // Check if we have an environment variable
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // Use configurable port from environment or default
  const port = import.meta.env.VITE_API_PORT || '7892';

  // If running in browser, use current hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    return `http://${hostname}:${port}`;
  }

  // Fallback to localhost
  return `http://localhost:${port}`;
};

const API_BASE = getApiBase();

// Export API_BASE for use in other modules
export { API_BASE };

/**
 * Helper to build API URLs with the correct base
 */
export const apiUrl = (path: string): string => {
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${normalizedPath}`;
};

export interface AgentInstance {
  instance_id: string;
  agent_id?: string;  // Agent string ID (e.g., 'product-manager')
  pid?: number;
  role?: 'pm' | 'specialist' | 'assistant' | 'agent_assistant' | 'skill_assistant';
  status: 'idle' | 'thinking' | 'working' | 'waiting' | 'completed' | 'error' | 'cancelled' | 'initializing';
  current_session_description?: string;
  project_id: string;
  project_path: string;
  session_id?: string;
  started_at: string;
  output_lines: number;
  // Kanban workflow stage
  kanban_stage?: 'backlog' | 'active' | 'waiting' | 'blocked' | 'review' | 'done';
  // Actual capabilities from Claude's init message
  actual_tools?: string[];
  selected_specialists?: string[];  // Team members selected for this agent
  actual_mcp_servers?: any[];
  actual_skills?: string[];
  auto_started?: boolean;  // Whether session was auto-started in background
  // Timestamps from backend (optional for backward compatibility)
  created_at?: string;
  updated_at?: string;
  context?: {  // Session context (from backend)
    description?: string;
    kanban_stage?: string;
    project_path?: string;
    [key: string]: any;
  };
}

export interface SpawnAgentRequest {
  team_member_ids: string[];  // Specialists to make available
  project_id?: string;  // If not provided, defaults to "default" project
  project_path: string;
  session_description: string;
  model?: string;
  system_prompt_append?: string;  // Additional instructions to append to system prompt
  role?: 'pm' | 'specialist' | 'assistant' | 'agent_assistant' | 'skill_assistant';
  auto_start?: boolean;  // If true, starts execution in background immediately
  kanban_stage?: string;  // Add missing kanban_stage field
}

// New session creation request (matches backend CreateSessionRequest)
export interface CreateSessionRequest {
  agent_id: string;  // Agent string ID (e.g., 'product-manager')
  project_id?: string;  // UUID of the project
  session_type: string;  // pm, specialist, assistant
  context?: Record<string, any>;  // Initial session context
}

export interface SessionMessage {
  id: string;
  instance_id: string;
  role: 'user' | 'assistant' | 'tool' | 'system';
  content: string;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  timestamp: string;
  cost_usd?: number;
  is_streaming: boolean;
  agent_id?: string;  // Source of truth for which agent sent the message
  agent_name?: string;  // Display name of the sending agent
  from_instance_id?: string;  // Session ID where message originated (for cross-session routing)
}

export interface SendMessageRequest {
  content: string;
  query_type?: 'normal' | 'interrupt';
  agent_id?: string;
  agent_name?: string;
}

export interface SendMessageResponse {
  status: 'queued';
  queue_size: number;
  processing: boolean;
}

export interface QueueStatus {
  queue_size: number;
  is_processing: boolean;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  path: string;  // Required by backend
  pm_agent_id?: string;  // Backend uses pm_agent_id (agent string IDs, not character UUIDs)
  pm_session_id?: string;
  team_member_ids?: string[];  // List of agent IDs assigned to this project
  created_at: string;  // Backend uses snake_case
  updated_at: string;  // Backend uses snake_case
  deleted_at?: string;  // Soft delete timestamp
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  path: string;  // Required by backend
  pm_agent_id?: string;  // Backend expects pm_agent_id (agent string IDs, not character UUIDs)
  team_member_ids?: string[];  // List of agent IDs to assign to this project
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  pm_id?: string;
  team_member_ids?: string[];
  is_archived?: boolean;
}

export const api = {
  async launchSession(req: SpawnAgentRequest): Promise<AgentInstance> {
    // Use unified /sessions/launch endpoint for all roles
    const res = await fetch(`${API_BASE}/api/v1/sessions/launch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    const session = await res.json();
    // Map backend SessionDTO fields to frontend AgentInstance fields
    return {
      ...session,
      instance_id: session.id || session.instance_id,  // Map id to instance_id (support both legacy and new)
      role: session.session_type || session.role,  // Map session_type to role (support both legacy and new)
    };
  },

  async createSession(req: CreateSessionRequest): Promise<AgentInstance> {
    // Use new /sessions endpoint
    const res = await fetch(`${API_BASE}/api/v1/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    const session = await res.json();
    // Map backend SessionDTO fields to frontend AgentInstance fields
    return {
      ...session,
      instance_id: session.id,  // Map id to instance_id
      role: session.session_type,  // Map session_type to role
    };
  },

  async getSessions(projectId?: string): Promise<AgentInstance[]> {
    const params = projectId ? `?project_id=${projectId}` : '';
    const res = await fetch(`${API_BASE}/api/v1/sessions${params}`);
    const sessions = await res.json();
    // Map backend SessionDTO fields to frontend AgentInstance fields
    return sessions.map((s: any) => ({
      ...s,
      instance_id: s.id,  // Map id to instance_id
      role: s.session_type,  // Map session_type to role
    }));
  },

  async getSession(sessionId: string): Promise<AgentInstance> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`);
    const session = await res.json();
    // Map backend SessionDTO fields to frontend AgentInstance fields
    return {
      ...session,
      instance_id: session.id,  // Map id to instance_id
      role: session.session_type,  // Map session_type to role
    };
  },

  async getSessionMessages(sessionId: string, limit: number = 100): Promise<SessionMessage[]> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/messages?limit=${limit}`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    // Backend now returns paginated result - extract items array
    return data.items || data;
  },

  streamSessionOutput(sessionId: string, onEvent: (event: any) => void) {
    console.log(`[STREAM] Connecting to: ${API_BASE}/api/v1/sessions/${sessionId}/stream`);
    const eventSource = new EventSource(`${API_BASE}/api/v1/sessions/${sessionId}/stream`);

    eventSource.onopen = () => {
      console.log('[STREAM] Connection opened');
    };

    eventSource.onmessage = (e) => {
      console.log('[STREAM] Message received:', e.data);
      try {
        const event = JSON.parse(e.data);
        console.log('[STREAM] Parsed event:', event);
        onEvent(event);

        // Close on complete or error
        if (event.type === 'complete' || event.type === 'error') {
          console.log('[STREAM] Stream ended:', event.type);
          eventSource.close();
        }
      } catch (parseError) {
        console.error('[STREAM] Failed to parse event:', parseError, 'Raw data:', e.data);
      }
    };

    eventSource.onerror = (error) => {
      console.error('[STREAM] EventSource error:', error);
      console.error('[STREAM] EventSource readyState:', eventSource.readyState);
      // Send error event to handler
      onEvent({ type: 'error', data: { error: 'Connection error' } });
      eventSource.close();
    };

    return () => {
      console.log('[STREAM] Closing connection');
      eventSource.close();
    };
  },

  async sendMessageToSession(
    sessionId: string,
    request: SendMessageRequest | string
  ): Promise<SendMessageResponse> {
    // Convert to query request format
    const query = typeof request === 'string' ? request : request.content;

    console.log(`[API] Sending message to session ${sessionId}:`, query);
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        stream: true,
      }),
    });
    if (!res.ok) {
      const error = await res.text();
      console.error('[API] Failed to send message:', error);
      throw new Error(error);
    }

    // The /query endpoint returns SSE stream, not JSON
    // Return a mock response for compatibility
    console.log('[API] Message sent to query endpoint (SSE stream)');
    return {
      status: 'queued',
      queue_size: 0,
      processing: true,
    };
  },

  async getQueueStatus(sessionId: string): Promise<QueueStatus> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/queue-status`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async cancelSession(sessionId: string): Promise<void> {
    await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/interrupt`, {
      method: 'POST',
    });
  },

  async updateSessionStage(sessionId: string, stage: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/stage`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage }),
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async deleteSession(sessionId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
  },


  // Project Management
  async getProjects(includeArchived: boolean = false): Promise<Project[]> {
    const params = new URLSearchParams();
    if (includeArchived) {
      params.append('include_archived', 'true');
    }
    const url = `${API_BASE}/api/v1/projects${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getProject(projectId: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async createProject(req: CreateProjectRequest): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/v1/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateProject(projectId: string, req: UpdateProjectRequest): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async deleteProject(projectId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async unarchiveProject(projectId: string): Promise<{ message: string; project_id: string }> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/unarchive`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async permanentlyDeleteProject(projectId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/permanent`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async recreateSession(sessionId: string): Promise<AgentInstance> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/recreate`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Project File Management
  async getProjectFileContent(projectId: string, filePath: string): Promise<{ content: string; path: string; readonly: boolean }> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/files/content?file_path=${encodeURIComponent(filePath)}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateProjectFileContent(projectId: string, filePath: string, content: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/files/content`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath, content }),
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async deleteProjectFile(projectId: string, filePath: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/files?file_path=${encodeURIComponent(filePath)}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async downloadProjectFile(projectId: string, filePath: string): Promise<Blob> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/files/download?file_path=${encodeURIComponent(filePath)}`);
    if (!res.ok) throw new Error(await res.text());
    return res.blob();
  },

  // Session File Management
  async getSessionFileContent(sessionId: string, filePath: string): Promise<{ content: string; path: string; readonly: boolean }> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/files/content?file_path=${encodeURIComponent(filePath)}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateSessionFileContent(sessionId: string, filePath: string, content: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/files/content`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath, content }),
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async deleteSessionFile(sessionId: string, filePath: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/files?file_path=${encodeURIComponent(filePath)}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async downloadSessionFile(sessionId: string, filePath: string): Promise<Blob> {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/files/download?file_path=${encodeURIComponent(filePath)}`);
    if (!res.ok) throw new Error(await res.text());
    return res.blob();
  },

  // Skill Management
  async getSkills(): Promise<SkillMetadata[]> {
    const res = await fetch(`${API_BASE}/api/v1/skills`);
    return res.json();
  },

  async getSkill(skillId: string): Promise<SkillDefinition> {
    const res = await fetch(`${API_BASE}/api/v1/skills/${skillId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async searchSkills(query: string): Promise<SkillSearchResponse> {
    const res = await fetch(`${API_BASE}/api/v1/skills/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async createSkill(req: CreateSkillRequest): Promise<SkillDefinition> {
    const res = await fetch(`${API_BASE}/api/v1/skills`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateSkill(skillId: string, req: UpdateSkillRequest): Promise<SkillDefinition> {
    const res = await fetch(`${API_BASE}/api/v1/skills/${skillId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async syncSkill(skillId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/skills/${skillId}/sync`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async deleteSkill(skillId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/skills/${skillId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async importSkill(req: ImportSkillRequest): Promise<ImportSkillResponse> {
    const res = await fetch(`${API_BASE}/api/v1/skills/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getMcpServers(): Promise<McpServer[]> {
    const res = await fetch(`${API_BASE}/api/v1/mcp/servers`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getCustomTools(): Promise<CustomTool[]> {
    const res = await fetch(`${API_BASE}/api/v1/skills/tools/custom`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async promptEditSkill(skillId: string | null, prompt: string): Promise<{ agent_id: string; message: string; status: string }> {
    const res = await fetch(`${API_BASE}/api/v1/skills/prompt-edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skill_id: skillId, prompt }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getSkillFiles(skillId: string): Promise<SkillFileNode[]> {
    const res = await fetch(`${API_BASE}/api/v1/skills/${skillId}/files`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    // Add 'type' field based on 'is_directory'
    return data.map((file: any) => ({
      ...file,
      type: file.is_directory ? 'directory' : 'file'
    }));
  },

  async getSkillFileContent(skillId: string, filePath: string): Promise<{ content: string; path: string }> {
    const res = await fetch(`${API_BASE}/api/v1/skills/${skillId}/files/content?file_path=${encodeURIComponent(filePath)}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateSkillFileContent(skillId: string, filePath: string, content: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/skills/${skillId}/files/content`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath, content }),
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async deleteSkillFile(skillId: string, filePath: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/skills/${skillId}/files?file_path=${encodeURIComponent(filePath)}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async renameSkillFile(skillId: string, oldPath: string, newPath: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/skills/${skillId}/files/rename`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old_path: oldPath, new_path: newPath }),
    });
    if (!res.ok) throw new Error(await res.text());
  },

  // Agent Management (file-based with CLAUDE.md)
  async getAgents(): Promise<Agent[]> {
    const res = await fetch(`${API_BASE}/api/v1/agents`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getAgent(agentId: string): Promise<Agent> {
    const res = await fetch(`${API_BASE}/api/v1/agents/${agentId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async searchAgents(tags: string[], matchAll: boolean = false): Promise<Agent[]> {
    const tagsParam = tags.join(',');
    const res = await fetch(`${API_BASE}/api/v1/agents/search?tags=${encodeURIComponent(tagsParam)}&match_all=${matchAll}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async createAgent(req: CreateAgentRequest): Promise<Agent> {
    const res = await fetch(`${API_BASE}/api/v1/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateAgent(agentId: string, req: UpdateAgentRequest): Promise<Agent> {
    const res = await fetch(`${API_BASE}/api/v1/agents/${agentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async deleteAgent(agentId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/agents/${agentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
  },

  // Agent File Management
  async getAgentFiles(agentId: string): Promise<SkillFileNode[]> {
    const res = await fetch(`${API_BASE}/api/v1/agents/${agentId}/files`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    // Add 'type' field based on 'is_directory'
    return data.map((file: any) => ({
      ...file,
      type: file.is_directory ? 'directory' : 'file'
    }));
  },

  async getAgentFileContent(agentId: string, filePath: string): Promise<{ file_path: string; content: string; size: number }> {
    const res = await fetch(`${API_BASE}/api/v1/agents/${agentId}/files/content?file_path=${encodeURIComponent(filePath)}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateAgentFileContent(agentId: string, filePath: string, content: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/agents/${agentId}/files/content`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath, content }),
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async deleteAgentFile(agentId: string, filePath: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/agents/${agentId}/files?file_path=${encodeURIComponent(filePath)}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
  },

  // Agent Content Loading (for AI context)
  async loadAgentContent(agentId: string): Promise<string> {
    const res = await fetch(`${API_BASE}/api/v1/agents/${agentId}/content`);
    if (!res.ok) throw new Error(await res.text());
    return res.text();
  },

  async loadAgentSupportingDoc(agentId: string, docPath: string): Promise<string> {
    const res = await fetch(`${API_BASE}/api/v1/agents/${agentId}/docs/${encodeURIComponent(docPath)}`);
    if (!res.ok) throw new Error(await res.text());
    return res.text();
  },

  // User Profile API
  async getUserProfile(): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/api/v1/profile`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateUserProfile(data: UpdateUserProfileRequest): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/api/v1/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Onboarding
  async getOnboardingStatus(): Promise<OnboardingStatusResponse> {
    const res = await fetch(`${API_BASE}/api/v1/onboarding/status`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async setupDemo(team: 'dev' | 'research' | 'content'): Promise<SetupDemoResponse> {
    const res = await fetch(`${API_BASE}/api/v1/onboarding/setup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async resetOnboarding(): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/onboarding/reset`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async resetApp(): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/system/reset`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(await res.text());
  },
};

export interface SkillMetadata {
  id: string;
  name: string;
  description: string;
  file_path: string;
  tags: string[];
  icon: string;
  icon_color: string;
}

export interface SkillDefinition {
  id: string;
  name: string;
  description: string;
  file_path: string;
  tags: string[];
  content?: string;
  license?: string;
  icon: string;
  icon_color: string;
}

export interface SkillSearchResult {
  skill: SkillMetadata;
  score: number;
  match_field: string;
  match_text: string;
}

export interface SkillSearchResponse {
  query: string;
  results: SkillSearchResult[];
}

export interface CreateSkillRequest {
  id?: string;
  name: string;
  description?: string;
  file_path?: string;
  tags?: string[];
  content?: string;
  license?: string;
  icon?: string;
  iconColor?: string;
}

export interface UpdateSkillRequest {
  name?: string;
  description?: string;
  file_path?: string;
  tags?: string[];
  content?: string;
  license?: string;
  icon?: string;
  iconColor?: string;
}

export interface ImportSkillRequest {
  source: string;
  skill_id?: string;
}

export interface ImportSkillResponse {
  skill: SkillDefinition;
  status: string;
  message: string;
}

// McpServer is now exported from @/types

export interface CustomTool {
  id: string;
  provider: string;
  category: string;
  name: string;
  description: string;
  input_schema: Record<string, any>;
}

// Agent types (file-based with CLAUDE.md)
export interface Agent {
  id: string;
  name: string;
  description?: string;
  file_path: string;
  default_model: string;
  tags: string[];
  skills: string[];
  allowed_tools: string[];
  allowed_mcps: string[];
  icon_color: string;
}

export interface CreateAgentRequest {
  name: string;
  description?: string;
  id?: string;
  file_path?: string;
  default_model?: string;
  tags?: string[];
  skills?: string[];
  allowed_tools?: string[];
  allowed_mcps?: string[];
  icon_color?: string;
}

export interface UpdateAgentRequest {
  name?: string;
  description?: string;
  default_model?: string;
  tags?: string[];
  skills?: string[];
  allowed_tools?: string[];
  allowed_mcps?: string[];
  icon_color?: string;
}

// File info for agent/skill file trees
export interface SkillFileNode {
  path: string;
  name: string;
  type: 'file' | 'directory';
  size: number;
  is_directory: boolean;
  modified_at: string;
}

// Legacy agent types (deprecated - kept for backward compatibility)
export interface UserProfile {
  id: string;
  avatar?: string | null;
  description?: string | null;
  preferences?: Record<string, any> | null;
}

export interface UpdateUserProfileRequest {
  avatar?: string | null;
  description?: string | null;
  preferences?: Record<string, any> | null;
}

export interface SetupDemoResponse {
  project_name: string;
  skills_created: string[];
  agents_created: string[];
  message: string;
}

export interface OnboardingStatusResponse {
  completed: boolean;
  team: string | null;
}
