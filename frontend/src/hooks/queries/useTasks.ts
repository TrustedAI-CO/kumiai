import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { queryKeys } from '@/lib/query/queryClient';
import type { Task, CreateTaskRequest, UpdateTaskRequest } from '@/types/task';

export function useTasks(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.tasks(projectId!),
    queryFn: () => api.getProjectTasks(projectId!),
    enabled: !!projectId,
    staleTime: 1000 * 60 * 2,
  });
}

export function useTask(taskId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.task(taskId!),
    queryFn: () => api.getTask(taskId!),
    enabled: !!taskId,
  });
}

export function useCreateTask(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: CreateTaskRequest) => api.createTask(projectId, req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks(projectId) });
    },
  });
}

export function useUpdateTask(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, req }: { taskId: string; req: UpdateTaskRequest }) =>
      api.updateTask(taskId, req),
    onMutate: async ({ taskId, req }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.tasks(projectId) });
      const previous = queryClient.getQueryData<Task[]>(queryKeys.tasks(projectId));
      queryClient.setQueryData<Task[]>(queryKeys.tasks(projectId), (old = []) =>
        old.map(t => t.id === taskId ? { ...t, ...req } : t)
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.tasks(projectId), context.previous);
      }
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.task(updated.id), updated);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks(projectId) });
    },
  });
}

export function useDeleteTask(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => api.deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks(projectId) });
    },
  });
}
