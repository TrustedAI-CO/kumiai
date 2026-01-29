import {
  Zap,
  Code,
  Database,
  Globe,
  Terminal,
  Wrench,
  Box,
  FileCode,
  Cpu,
  Blocks,
  BookOpen,
  Puzzle,
  Settings,
  Briefcase,
  Binary,
  Calculator,
  FileText,
  Folder,
  LucideIcon,
} from 'lucide-react';

export const SKILL_ICONS: Record<string, LucideIcon> = {
  zap: Zap,
  code: Code,
  database: Database,
  globe: Globe,
  terminal: Terminal,
  wrench: Wrench,
  box: Box,
  fileCode: FileCode,
  cpu: Cpu,
  blocks: Blocks,
  bookOpen: BookOpen,
  puzzle: Puzzle,
  settings: Settings,
  briefcase: Briefcase,
  binary: Binary,
  calculator: Calculator,
  fileText: FileText,
  folder: Folder,
};

export const ICON_OPTIONS = [
  { value: 'zap', label: 'Zap', Icon: Zap },
  { value: 'code', label: 'Code', Icon: Code },
  { value: 'database', label: 'Database', Icon: Database },
  { value: 'globe', label: 'Globe', Icon: Globe },
  { value: 'terminal', label: 'Terminal', Icon: Terminal },
  { value: 'wrench', label: 'Wrench', Icon: Wrench },
  { value: 'box', label: 'Box', Icon: Box },
  { value: 'fileCode', label: 'File Code', Icon: FileCode },
  { value: 'cpu', label: 'CPU', Icon: Cpu },
  { value: 'blocks', label: 'Blocks', Icon: Blocks },
  { value: 'bookOpen', label: 'Book', Icon: BookOpen },
  { value: 'puzzle', label: 'Puzzle', Icon: Puzzle },
  { value: 'settings', label: 'Settings', Icon: Settings },
  { value: 'briefcase', label: 'Briefcase', Icon: Briefcase },
  { value: 'binary', label: 'Binary', Icon: Binary },
  { value: 'calculator', label: 'Calculator', Icon: Calculator },
  { value: 'fileText', label: 'File', Icon: FileText },
  { value: 'folder', label: 'Folder', Icon: Folder },
];

export const getSkillIcon = (iconName?: string): LucideIcon => {
  if (!iconName) return Zap;
  // Case-insensitive lookup
  const normalizedName = iconName.toLowerCase();
  return SKILL_ICONS[normalizedName] || Zap;
};
