/**
 * Agent Queries - React Query hooks for agent-related API calls
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AgentInstance, CreateAgentRequest, UpdateAgentRequest } from '@/lib/api';
import { queryKeys } from '@/lib/query/queryClient';
import type { Agent } from '@/types';

/**
 * Fetch all agents
 */
export function useAgents() {
  return useQuery({
    queryKey: queryKeys.agents,
    queryFn: api.getAgents,
    staleTime: 1000 * 60 * 5
  });
}

/**
 * Fetch single agent by ID
 */
export function useAgent(agentId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.agent(agentId!),
    queryFn: () => api.getAgent(agentId!),
    enabled: !!agentId,
    staleTime: 1000 * 60 * 5
  });
}

/**
 * Fetch all agent instances
 * TODO: Implement getAgentInstances API method
 */
// export function useAgentInstances(projectId?: string) {
//   return useQuery({
//     queryKey: queryKeys.agentInstances,
//     queryFn: () => api.getAgentInstances(projectId),
//     staleTime: 1000 * 30 // 30 seconds - instances change frequently
//   });
// }

/**
 * Fetch single agent instance
 * TODO: Implement getAgentInstance API method
 */
// export function useAgentInstance(instanceId: string | undefined) {
//   return useQuery({
//     queryKey: queryKeys.agentInstance(instanceId!),
//     queryFn: () => api.getAgentInstance(instanceId!),
//     enabled: !!instanceId,
//     staleTime: 1000 * 30
//   });
// }

/**
 * Create new agent
 */
export function useCreateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (agentData: CreateAgentRequest) => api.createAgent(agentData),
    onSuccess: (newAgent) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents });
      queryClient.setQueryData(queryKeys.agent(newAgent.id), newAgent);
    }
  });
}

/**
 * Update agent
 */
export function useUpdateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateAgentRequest }) =>
      api.updateAgent(id, data),
    onSuccess: (updatedAgent) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents });
      queryClient.setQueryData(queryKeys.agent(updatedAgent.id), updatedAgent);
    }
  });
}

/**
 * Delete agent
 */
export function useDeleteAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (agentId: string) => api.deleteAgent(agentId),
    onSuccess: (_, agentId) => {
      queryClient.removeQueries({ queryKey: queryKeys.agent(agentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.agents });
    }
  });
}

/**
 * Create agent instance
 * TODO: Implement createAgentInstance API method
 */
// export function useCreateAgentInstance() {
//   const queryClient = useQueryClient();

//   return useMutation({
//     mutationFn: (data: {
//       agent_id: string;
//       project_id: string;
//       task_description?: string;
//     }) => api.createAgentInstance(data),
//     onSuccess: () => {
//       queryClient.invalidateQueries({ queryKey: queryKeys.agentInstances });
//     }
//   });
// }

/**
 * Delete agent instance
 * TODO: Implement deleteAgentInstance API method
 */
// export function useDeleteAgentInstance() {
//   const queryClient = useQueryClient();

//   return useMutation({
//     mutationFn: (instanceId: string) => api.deleteAgentInstance(instanceId),
//     onSuccess: (_, instanceId) => {
//       queryClient.removeQueries({ queryKey: queryKeys.agentInstance(instanceId) });
//       queryClient.invalidateQueries({ queryKey: queryKeys.agentInstances });
//     }
//   });
// }
