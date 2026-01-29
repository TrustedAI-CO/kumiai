import { useState, useEffect, useMemo } from 'react';
import { Plus, Zap, Download } from 'lucide-react';
import { api, SkillMetadata } from '@/lib/api';
import { ItemCard, DeleteButton } from '@/ui';
import { ListLayout } from '@/components/layout/ListLayout';
import { cn } from '@/lib/utils';
import { getSkillIcon } from '@/constants/skillIcons';

interface SkillsListProps {
  currentSkillId?: string;
  onSelectSkill: (skillId: string) => void;
  onDeleteSkill: (skillId: string) => void;
  onCreateSkill: () => void;
  onImportSkill: () => void;
  isMobile?: boolean;
  reloadTrigger?: number;
}

export function SkillsList({
  currentSkillId,
  onSelectSkill,
  onDeleteSkill,
  onCreateSkill,
  onImportSkill,
  isMobile = false,
  reloadTrigger
}: SkillsListProps) {
  const [skills, setSkills] = useState<SkillMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadSkills();
  }, []);

  useEffect(() => {
    if (reloadTrigger !== undefined) {
      loadSkills();
    }
  }, [reloadTrigger]);

  const loadSkills = async () => {
    setLoading(true);
    try {
      const data = await api.getSkills();
      setSkills(data);
    } catch (error) {
      console.error('Failed to load skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredSkills = useMemo(() =>
    skills.filter(skill =>
      skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    ),
    [skills, searchQuery]
  );

  return (
    <ListLayout
      searchQuery={searchQuery}
      onSearchChange={setSearchQuery}
      searchPlaceholder="Search skills..."
      loading={loading}
      isEmpty={filteredSkills.length === 0}
      emptyIcon={Zap}
      emptyTitle={searchQuery ? 'No skills found' : 'No skills yet'}
      emptyDescription={searchQuery ? 'Try a different search term' : 'Create one to get started'}
      actionButtons={[
        { icon: Download, onClick: onImportSkill, title: 'Import Skill', variant: 'secondary' },
        { icon: Plus, onClick: onCreateSkill, title: 'New Skill', variant: 'primary' }
      ]}
      isMobile={isMobile}
    >
      <div className={cn("flex flex-col gap-2")}>
        {filteredSkills.map((skill) => {
          const IconComponent = getSkillIcon(skill.icon);
          return (
            <div
              key={skill.id}
              className="group relative"
            >
              <ItemCard
                id={skill.id}
                name={skill.name}
                description={skill.description}
                icon={<IconComponent className="w-5 h-5 text-white" />}
                iconColor={skill.icon_color}
                onClick={() => onSelectSkill(skill.id)}
                isSelected={currentSkillId === skill.id}
              />
              <DeleteButton
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSkill(skill.id);
                }}
                title={`Delete ${skill.name}`}
              />
            </div>
          );
        })}
      </div>
    </ListLayout>
  );
}
