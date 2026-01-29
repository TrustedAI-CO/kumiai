/**
 * UI Constants
 */

// Layout
export const LAYOUT = {
  LIST_WIDTH: 'w-[30%]',
  DETAIL_WIDTH: 'w-[70%]',
  SKILL_LIST_HEIGHT: 'h-80',
} as const;

// Skill Display
export const SKILL = {
  MAX_VISIBLE_ICONS: 5,
  MAX_BADGE_DISPLAY: 4,
} as const;

// Empty States
export const EMPTY_STATE_MESSAGE = {
  NO_SKILLS: 'No skills selected',
  NO_SKILLS_FOUND: 'No skills found',
  ALL_SKILLS_ADDED: 'All skills added',
  ALL_ADDED: 'All skills added',
  NO_RESULTS: 'No skills found',
  NO_AGENTS: 'No agents yet',
  NO_AGENTS_FOUND: 'No agents found',
} as const;

// Built-in Agents (for filtering)
export const BUILT_IN_AGENTS = [
  'general-purpose',
  'statusline-setup',
  'Explore',
  'Plan',
  'code-reviewer',
  'product-owner-analyst',
  'rapid-prototype-tester',
  'solution-architect',
  'email-assistant',
  'notion-personal',
] as const;
