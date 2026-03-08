export type TaskStatus = 'open' | 'in_progress' | 'done' | 'archived';

export interface Task {
  id: string;
  project_id: string;
  name: string;
  description?: string | null;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskRequest {
  name: string;
  description?: string;
}

export interface UpdateTaskRequest {
  name?: string;
  description?: string;
  status?: TaskStatus;
}
