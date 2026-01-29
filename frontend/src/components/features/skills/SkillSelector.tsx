import { GenericListSelector } from '@/ui';
import { getSkillIcon } from '@/constants/skillIcons';
import type { Skill } from '@/types/skill';

interface SkillSelectorProps {
  availableSkills: Skill[];
  selectedSkillIds: string[];
  onAddSkill: (skillId: string) => void;
  onRemoveSkill: (skillId: string) => void;
  isEditing: boolean;
}

/**
 * Skill selector component using the generic list selector.
 * Displays available skills and allows adding/removing them.
 */
export function SkillSelector({
  availableSkills,
  selectedSkillIds,
  onAddSkill,
  onRemoveSkill,
  isEditing,
}: SkillSelectorProps) {
  return (
    <GenericListSelector
      availableItems={availableSkills}
      selectedItemIds={selectedSkillIds}
      onAddItem={onAddSkill}
      onRemoveItem={onRemoveSkill}
      isEditing={isEditing}
      searchPlaceholder="Search skills to add"
      emptySelectedMessage="No skills added yet"
      renderIcon={(skill) => {
        const IconComponent = getSkillIcon(skill.icon);
        return <IconComponent className="w-4 h-4 text-white" />;
      }}
      getIconColor={(skill) => skill.icon_color}
    />
  );
}
