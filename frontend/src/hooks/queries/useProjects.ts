/**
 * Project Queries - React Query hooks for project-related API calls
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { CreateProjectRequest } from '@/lib/api';
import { queryKeys } from '@/lib/query/queryClient';
import type { Project } from '@/types';

/**
 * Fetch all projects
 */
export function useProjects() {
  return useQuery({
    queryKey: queryKeys.projects,
    queryFn: () => api.getProjects(),
    staleTime: 1000 * 60 * 5 // 5 minutes
  });
}

/**
 * Fetch single project by ID
 */
export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.project(projectId!),
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId, // Only fetch if projectId exists
    staleTime: 1000 * 60 * 5
  });
}

/**
 * Create new project
 */
export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (req: CreateProjectRequest) => api.createProject(req),
    onSuccess: (newProject) => {
      // Invalidate projects list to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });

      // Optimistically add to cache
      queryClient.setQueryData(queryKeys.project(newProject.id), newProject);
    }
  });
}

/**
 * Delete project
 */
export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => api.deleteProject(projectId),
    onSuccess: (_, projectId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: queryKeys.project(projectId) });

      // Invalidate projects list
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    }
  });
}
