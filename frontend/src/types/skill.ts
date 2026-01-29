/**
 * Skill type definitions
 *
 * Skills are pure documentation - no tool/MCP server declarations.
 * Tool and MCP server requirements are in Agent database.
 *
 * NOTE: Primary skill interfaces are defined in lib/api.ts (SkillMetadata, SkillDefinition)
 * This file only contains the minimal Skill interface for component props.
 */

export interface Skill {
  id: string;
  name: string;
  description: string;
  file_path: string;
  tags: string[];
  icon: string;
  icon_color: string;
}
