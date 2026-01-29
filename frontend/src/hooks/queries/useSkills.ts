/**
 * Skill Queries - React Query hooks for skill-related API calls
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { CreateSkillRequest, UpdateSkillRequest } from '@/lib/api';
import { queryKeys } from '@/lib/query/queryClient';

/**
 * Fetch all skills
 */
export function useSkills() {
  return useQuery({
    queryKey: queryKeys.skills,
    queryFn: api.getSkills,
    staleTime: 1000 * 60 * 5
  });
}

/**
 * Fetch single skill by ID
 */
export function useSkill(skillId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.skill(skillId!),
    queryFn: () => api.getSkill(skillId!),
    enabled: !!skillId,
    staleTime: 1000 * 60 * 5
  });
}

/**
 * Create new skill
 */
export function useCreateSkill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (skillData: CreateSkillRequest) => api.createSkill(skillData),
    onSuccess: (newSkill) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.skills });
      queryClient.setQueryData(queryKeys.skill(newSkill.id), newSkill);
    }
  });
}

/**
 * Update skill
 */
export function useUpdateSkill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSkillRequest }) =>
      api.updateSkill(id, data),
    onSuccess: (updatedSkill) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.skills });
      queryClient.setQueryData(queryKeys.skill(updatedSkill.id), updatedSkill);
    }
  });
}

/**
 * Delete skill
 */
export function useDeleteSkill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (skillId: string) => api.deleteSkill(skillId),
    onSuccess: (_, skillId) => {
      queryClient.removeQueries({ queryKey: queryKeys.skill(skillId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.skills });
    }
  });
}
