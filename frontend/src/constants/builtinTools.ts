/**
 * Built-in Claude Code tools
 * These are the core tools provided by the Claude Agent SDK
 */

export interface BuiltinTool {
  id: string;
  name: string;
  description: string;
  category: 'file' | 'code' | 'system';
}

export const BUILTIN_TOOLS: BuiltinTool[] = [
  {
    id: 'Read',
    name: 'Read',
    description: 'Read files from the filesystem with line offset and limit options',
    category: 'file',
  },
  {
    id: 'Write',
    name: 'Write',
    description: 'Write or overwrite files to the filesystem',
    category: 'file',
  },
  {
    id: 'Edit',
    name: 'Edit',
    description: 'Perform exact string replacements in files',
    category: 'file',
  },
  {
    id: 'Glob',
    name: 'Glob',
    description: 'Find files by pattern matching (e.g., "**/*.ts")',
    category: 'file',
  },
  {
    id: 'Grep',
    name: 'Grep',
    description: 'Search file contents using regex patterns',
    category: 'code',
  },
  {
    id: 'Bash',
    name: 'Bash',
    description: 'Execute bash commands in a persistent shell session',
    category: 'system',
  },
];
