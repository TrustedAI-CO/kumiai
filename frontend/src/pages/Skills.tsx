import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, SkillMetadata, SkillDefinition, SkillFileNode } from '@/lib/api';
import { Plus, Edit2, Trash2, Save, X, FileText, Zap, Package, Settings, ChevronRight, ChevronDown, File, Folder, FileEdit, Download, AlertCircle, CheckCircle, Wrench } from 'lucide-react';
import { Button } from '@/components/ui/primitives/button';
import { Input } from '@/components/ui/primitives/input';
import { Textarea } from '@/components/ui/primitives/textarea';
import { Card } from '@/components/ui/primitives/card';
import { ModalActionButton } from '@/ui';
import { LoadingState, Sheet, SheetContent, StandardModal, AdaptiveModal, EmptyState } from '@/components/ui';
import { cn } from '@/styles/design-system';
import { getSkillIcon, ICON_OPTIONS } from '@/constants/skillIcons';
import { SkillAssistantChat } from '@/components/features/skills';
import { SkillsList } from '@/components/features/skills';
import { MainLayout } from '@/components/layout';
import { MainHeader } from '@/components/layout';
import { SidebarNav } from '@/components/layout';
import { SidebarFooter } from '@/components/layout';
import { FileTree } from '@/components/features/files';
import type { ChatContext } from '@/types/chat';
import { paths } from '@/lib/utils/config';
import { useIsMobile, useIsDesktop, useToast } from '@/hooks';
import { buildFileTree, formatFileSize, type FileTreeNode } from '@/lib/utils';

interface SkillsProps {
  onChatContextChange?: (context: ChatContext) => void;
}

export default function Skills({ onChatContextChange }: SkillsProps) {
  const [skills, setSkills] = useState<SkillMetadata[]>([]);
  const [selectedSkill, setSelectedSkill] = useState<SkillDefinition | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showIconPicker, setShowIconPicker] = useState(false);
  const iconButtonRef = useRef<HTMLButtonElement>(null);

  const [skillFiles, setSkillFiles] = useState<SkillFileNode[]>([]);
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [isCreatingFile, setIsCreatingFile] = useState(false);
  const [newFilePath, setNewFilePath] = useState('');
  const [isRenamingFile, setIsRenamingFile] = useState(false);
  const [renameNewPath, setRenameNewPath] = useState('');
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [importSource, setImportSource] = useState('');
  const [importSkillId, setImportSkillId] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [importStatus, setImportStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createSkillName, setCreateSkillName] = useState('');
  const [newSkillTag, setNewSkillTag] = useState('');
  const [skillsReloadTrigger, setSkillsReloadTrigger] = useState(0);

  const isMobile = useIsMobile();
  const isDesktop = useIsDesktop();
  const toast = useToast();

  // Form state
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    description: '',
    license: 'MIT',
    content: '',
    icon: 'zap',
    iconColor: '#4A90E2',
    tags: [] as string[],
  });

  // Track pending changes
  const [pendingChanges, setPendingChanges] = useState<{
    name?: string;
    description?: string;
    tags?: string[];
    fileContent?: string;
  }>({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    loadSkills();

    // Set chat context to skill library on mount
    if (onChatContextChange) {
      onChatContextChange({
        role: 'skill_assistant',
        name: 'Skill Library',
        description: 'Manage skills - create new skills, modify existing ones, or delete skills. Skills are stored in ~/.kumiai/skills/ directory, each with a SKILL.md configuration file. IMPORTANT: Skills are now pure documentation with NO tool declarations. See ~/.kumiai/skills/_template/ for the correct file format. Each skill has YAML frontmatter with name, description, tags, icon, and iconColor fields.',
        data: {
          project_path: paths.skillLibrary,
        },
      });
    }
  }, []);

  // Reset pending changes when skill changes
  useEffect(() => {
    setPendingChanges({});
    setHasUnsavedChanges(false);
  }, [selectedSkill?.id]);

  const loadSkills = async () => {
    try {
      const data = await api.getSkills();
      setSkills(data);
      // Auto-select first skill if available and nothing is selected
      if (data.length > 0 && !selectedSkill) {
        loadSkill(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSkill = async (skillId: string) => {
    try {
      const skill = await api.getSkill(skillId);
      setSelectedSkill(skill);
      setFormData({
        id: skill.id,
        name: skill.name,
        description: skill.description,
        license: skill.license || 'MIT',
        content: skill.content || '',
        icon: skill.icon || 'zap',
        iconColor: skill.icon_color ?? '#4A90E2',
        tags: skill.tags || [],
      });

      // Load file tree
      const files = await api.getSkillFiles(skillId);
      setSkillFiles(files);

      // Build file tree from flat file list
      const tree = buildFileTree(files);
      setFileTree(tree);

      // Auto-select SKILL.md (case-insensitive)
      const skillMd = files.find(f => f.name.toLowerCase() === 'skill.md');
      if (skillMd) {
        handleFileSelect(skillId, skillMd.path);
      }
    } catch (error) {
      console.error('Failed to load skill:', error);
    }
  };

  const handleFileSelect = async (skillId: string, filePath: string) => {
    try {
      setSelectedFile(filePath);
      const result = await api.getSkillFileContent(skillId, filePath);
      setFileContent(result.content);
    } catch (error) {
      console.error('Failed to load file:', error);
    }
  };

  const handleFileSave = async () => {
    if (!selectedSkill || !selectedFile) return;

    try {
      await api.updateSkillFileContent(selectedSkill.id, selectedFile, fileContent);
    } catch (error) {
      console.error('Failed to save file:', error);
    }
  };

  const handleUpdateIconOrColor = async () => {
    if (!selectedSkill) return;

    try {
      await api.updateSkill(selectedSkill.id, {
        icon: formData.icon,
        iconColor: formData.iconColor,
      });
      // Reload the skill to update the display
      await loadSkill(selectedSkill.id);
      await loadSkills(); // Also update the list
    } catch (error) {
      console.error('Failed to update icon/color:', error);
      toast.error('Failed to update icon/color', 'Error');
    }
  };

  const handleUpdateSkillField = (field: string, value: any) => {
    if (!selectedSkill) return;

    setPendingChanges(prev => ({
      ...prev,
      [field]: value
    }));
    setHasUnsavedChanges(true);
  };

  const handleUpdateAllChanges = async () => {
    if (!selectedSkill || !hasUnsavedChanges) return;

    try {
      // Update skill metadata if there are changes
      if (Object.keys(pendingChanges).some(key => key !== 'fileContent')) {
        const metadataChanges: any = {};
        if (pendingChanges.name !== undefined) metadataChanges.name = pendingChanges.name;
        if (pendingChanges.description !== undefined) metadataChanges.description = pendingChanges.description;
        if (pendingChanges.tags !== undefined) metadataChanges.tags = pendingChanges.tags;

        if (Object.keys(metadataChanges).length > 0) {
          await api.updateSkill(selectedSkill.id, metadataChanges);
        }
      }

      // Save file content if changed
      if (pendingChanges.fileContent !== undefined && selectedFile) {
        await api.updateSkillFileContent(selectedSkill.id, selectedFile, pendingChanges.fileContent);
      }

      // Reload the skill to update the display
      await loadSkill(selectedSkill.id);
      await loadSkills();

      // Clear pending changes
      setPendingChanges({});
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Failed to update skill:', error);
      toast.error('Failed to update skill', 'Error');
    }
  };

  const handleCreateFile = async () => {
    if (!selectedSkill || !newFilePath.trim()) return;

    try {
      // Create the file with empty content
      await api.updateSkillFileContent(selectedSkill.id, newFilePath, '');

      // Reload file tree
      const files = await api.getSkillFiles(selectedSkill.id);
      setSkillFiles(files);
      setFileTree(buildFileTree(files));

      // Select the newly created file
      setSelectedFile(newFilePath);
      setFileContent('');

      // Reset new file state
      setIsCreatingFile(false);
      setNewFilePath('');
    } catch (error) {
      console.error('Failed to create file:', error);
      toast.error('Failed to create file', 'Error');
    }
  };

  const handleDeleteFile = async () => {
    if (!selectedSkill || !selectedFile) return;
    if (selectedFile === 'skill.md') return; // Don't allow deleting skill.md

    if (!confirm(`Are you sure you want to delete "${selectedFile}"?`)) return;

    try {
      await api.deleteSkillFile(selectedSkill.id, selectedFile);

      // Reload file tree
      const files = await api.getSkillFiles(selectedSkill.id);
      setSkillFiles(files);
      setFileTree(buildFileTree(files));

      // Clear selection
      setSelectedFile(null);
      setFileContent('');
    } catch (error) {
      console.error('Failed to delete file:', error);
      toast.error('Failed to delete file', 'Error');
    }
  };

  const handleRenameFile = async () => {
    if (!selectedSkill || !selectedFile || !renameNewPath.trim()) return;

    try {
      await api.renameSkillFile(selectedSkill.id, selectedFile, renameNewPath);

      // Reload file tree
      const files = await api.getSkillFiles(selectedSkill.id);
      setSkillFiles(files);
      setFileTree(buildFileTree(files));

      // Select the renamed file
      setSelectedFile(renameNewPath);

      // Reset rename state
      setIsRenamingFile(false);
      setRenameNewPath('');
    } catch (error) {
      console.error('Failed to rename file:', error);
      toast.error('Failed to rename file', 'Error');
    }
  };

  const generateSkillId = () => {
    return 'skill-' + Math.random().toString(36).substring(2, 10);
  };

  const handleCreate = () => {
    // Show dialog to get skill name
    setCreateSkillName('');
    setShowCreateDialog(true);
  };

  const handleConfirmCreate = async () => {
    if (!createSkillName.trim()) {
      toast.warning('Please enter a skill name', 'Validation Error');
      return;
    }

    const skillId = createSkillName
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');

    try {
      // Create skill with user-provided name
      await api.createSkill({
        id: skillId,
        name: createSkillName,
        description: 'A new skill',
        license: 'MIT',
        icon: 'zap',
        iconColor: '#4A90E2',
        tags: [],
      });

      // Close dialog
      setShowCreateDialog(false);
      setCreateSkillName('');

      // Reload skills list
      await loadSkills();
      setSkillsReloadTrigger(prev => prev + 1); // Trigger reload

      // Small delay to ensure file system sync
      await new Promise(resolve => setTimeout(resolve, 100));

      // Load the newly created skill
      await loadSkill(skillId);
    } catch (error) {
      console.error('Failed to create skill:', error);
      toast.error('Failed to create skill. Please try again.', 'Error');
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSave = async () => {
    // Files are auto-saved, this function is no longer needed
    // Kept for backward compatibility but does nothing
    console.log('Save called - files are auto-saved');
  };

  const handleCancel = () => {
    // No form to cancel anymore - files are auto-saved
    setIsCreating(false);
    setIsEditing(false);
  };

  const handleDelete = async (skillId: string) => {
    if (!confirm('Are you sure you want to delete this skill?')) return;

    try {
      await api.deleteSkill(skillId);
      await loadSkills();
      setSkillsReloadTrigger(prev => prev + 1); // Trigger reload
      if (selectedSkill?.id === skillId) {
        setSelectedSkill(null);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to delete skill: ' + errorMessage, 'Error');
    }
  };

  const handleImport = async () => {
    if (!importSource.trim()) {
      setImportStatus({ type: 'error', message: 'Please enter a GitHub URL or local path' });
      return;
    }

    setIsImporting(true);
    setImportStatus(null);

    try {
      const response = await api.importSkill({
        source: importSource,
        skill_id: importSkillId.trim() || undefined,
      });

      setImportStatus({ type: 'success', message: response.message || 'Skill imported successfully!' });

      // Wait a moment to show success message
      setTimeout(async () => {
        // Reload skills list
        await loadSkills();

        // Select the newly imported skill
        await loadSkill(response.skill.id);

        // Close modal and reset
        setIsImportModalOpen(false);
        setImportSource('');
        setImportSkillId('');
        setImportStatus(null);
      }, 1500);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setImportStatus({ type: 'error', message: errorMessage });
    } finally {
      setIsImporting(false);
    }
  };

  const handleOpenImportModal = () => {
    setIsImportModalOpen(true);
    setImportSource('');
    setImportSkillId('');
    setImportStatus(null);
  };

  const handleCloseImportModal = () => {
    if (!isImporting) {
      setIsImportModalOpen(false);
      setImportSource('');
      setImportSkillId('');
      setImportStatus(null);
    }
  };


  // Handler for selecting skill
  const handleSelectSkill = async (skillId: string) => {
    await loadSkill(skillId);
    setIsCreating(false);
    setIsEditing(false);
  };


  return (
    <MainLayout
      leftSidebarNav={<SidebarNav />}
      leftSidebarContent={
        <SkillsList
          currentSkillId={selectedSkill?.id}
          onSelectSkill={handleSelectSkill}
          onDeleteSkill={handleDelete}
          onCreateSkill={handleCreate}
          onImportSkill={handleOpenImportModal}
          isMobile={isMobile}
          reloadTrigger={skillsReloadTrigger}
        />
      }
      leftSidebarFooter={<SidebarFooter />}
      rightSidebarContent={
        <SkillAssistantChat
          isOpen={true}
          onToggle={() => {}}
          skillId={selectedSkill?.id}
          skillName={selectedSkill?.name}
          onSkillUpdated={async () => {
            // Reload skills list and refresh current skill if one is selected
            try {
              const skillsBefore = skills.map(s => s.id);
              const updatedSkills = await api.getSkills();
              setSkills(updatedSkills);
              const newSkills = updatedSkills.filter(s => !skillsBefore.includes(s.id));
              let skillToReload = selectedSkill?.id;
              if (newSkills.length > 0 && !selectedSkill) {
                skillToReload = newSkills[0].id;
              }
              if (skillToReload) {
                await loadSkill(skillToReload);
                if (selectedFile) {
                  const result = await api.getSkillFileContent(skillToReload, selectedFile);
                  setFileContent(result.content);
                }
              }
            } catch (error) {
              console.error('Failed to reload skills:', error);
            }
          }}
          className="bg-gray-50"
        />
      }
    >
      {({ leftSidebarOpen, rightSidebarOpen, toggleLeftSidebar, toggleRightSidebar }) => (
      <div className="flex-1 flex flex-col overflow-hidden bg-white">
        <MainHeader
          breadcrumb={selectedSkill ? "Skills" : undefined}
          title={selectedSkill?.name || "Skills"}
          leftSidebarOpen={leftSidebarOpen}
          onToggleLeftSidebar={toggleLeftSidebar}
          rightSidebarOpen={rightSidebarOpen}
          onToggleRightSidebar={toggleRightSidebar}
          actions={
            selectedSkill && (
              <Button
                onClick={handleUpdateAllChanges}
                disabled={!hasUnsavedChanges}
                size="sm"
                className="text-sm font-medium"
              >
                Update
              </Button>
            )
          }
        />
        <div className="flex-1 flex overflow-hidden bg-white">
        {/* Mobile: Skill List Sheet */}
        <Sheet open={isMobile && !selectedSkill} onOpenChange={() => {}}>
          <SheetContent side="left" className="w-full p-0">
            <div className="flex flex-col h-full">
              <SkillsList
                currentSkillId={selectedSkill?.id}
                onSelectSkill={handleSelectSkill}
                onDeleteSkill={handleDelete}
                onCreateSkill={handleCreate}
                onImportSkill={handleOpenImportModal}
                isMobile={true}
                reloadTrigger={skillsReloadTrigger}
              />
            </div>
          </SheetContent>
        </Sheet>

        {/* Skill Detail / Editor */}
        <div className={cn(
          "flex-1 flex flex-col min-w-0 overflow-hidden bg-white",
          // On mobile, only show when a skill is selected or creating
          isMobile
            ? (selectedSkill || isCreating ? "flex" : "hidden")
            : "flex"
        )}>
          {(selectedSkill || isCreating) ? (
            <>
              {/* Mobile Back Button */}
              {(selectedSkill || isCreating) && (
                <div className="lg:hidden flex-shrink-0 border-b border-gray-200 bg-white px-4 py-3">
                  <button
                    onClick={() => {
                      setSelectedSkill(null);
                      setIsCreating(false);
                      setIsEditing(false);
                    }}
                    className="flex items-center gap-2 text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    <ChevronRight className="w-5 h-5 rotate-180" />
                    <span className="type-label">Back to Skills</span>
                  </button>
                </div>
              )}

              {/* File Editor - Skills are file-based, edit SKILL.md directly */}
              <div className="flex-1 overflow-y-auto px-4 lg:px-6 pb-6 scrollbar-hide">
                {/* Skill Header */}
                <div className="flex items-center gap-3 h-12">
                  <button
                    ref={iconButtonRef}
                    onClick={() => {
                      // Sync formData with current skill before opening picker
                      if (selectedSkill) {
                        setFormData({
                          ...formData,
                          icon: selectedSkill.icon || 'zap',
                          iconColor: selectedSkill.icon_color || '#4A90E2',
                        });
                      }
                      setShowIconPicker(!showIconPicker);
                    }}
                    className="relative group flex-shrink-0"
                    type="button"
                  >
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center transition-all group-hover:ring-2 group-hover:ring-ring ${selectedSkill?.icon_color ? '' : 'bg-gray-100'}`}
                      style={selectedSkill?.icon_color ? { backgroundColor: selectedSkill.icon_color } : undefined}
                    >
                      {(() => {
                        const IconComponent = getSkillIcon(selectedSkill?.icon || 'zap');
                        return <IconComponent className="w-5 h-5 text-white" />;
                      })()}
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded-lg transition-all">
                      <Edit2 className="w-3 h-3 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </button>
                  <div className="flex-1 min-w-0">
                    <h3 className="type-title text-gray-900 truncate">{selectedSkill?.name}</h3>
                    <p className="type-caption text-gray-500 truncate">{selectedSkill?.id}</p>
                  </div>
                </div>

                {/* Skill Details */}
                <div className="py-4 space-y-3">
                  <div>
                    <label className="block type-caption text-gray-600 mb-1">Name</label>
                    <Input
                      value={pendingChanges.name !== undefined ? pendingChanges.name : (selectedSkill?.name || '')}
                      onChange={(e) => handleUpdateSkillField('name', e.target.value)}
                      placeholder="Skill name"
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block type-caption text-gray-600 mb-1">Description</label>
                    <Textarea
                      value={pendingChanges.description !== undefined ? pendingChanges.description : (selectedSkill?.description || '')}
                      onChange={(e) => handleUpdateSkillField('description', e.target.value)}
                      placeholder="Skill description"
                      rows={2}
                      className="px-3 py-2 resize-none"
                    />
                  </div>

                  <div>
                    <label className="block type-caption text-gray-600 mb-1">Tags</label>
                    <Input
                      value={newSkillTag}
                      onChange={(e) => setNewSkillTag(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && newSkillTag.trim() && selectedSkill) {
                          const currentTags = pendingChanges.tags !== undefined ? pendingChanges.tags : selectedSkill.tags;
                          const updatedTags = [...currentTags, newSkillTag.trim()];
                          handleUpdateSkillField('tags', updatedTags);
                          setNewSkillTag('');
                        }
                      }}
                      placeholder="Add tag..."
                      className="w-full"
                    />
                    {(() => {
                      const displayTags = pendingChanges.tags !== undefined ? pendingChanges.tags : selectedSkill?.tags;
                      return displayTags && displayTags.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {displayTags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 type-caption"
                            >
                              {tag}
                              <button
                                onClick={() => {
                                  const currentTags = pendingChanges.tags !== undefined ? pendingChanges.tags : selectedSkill!.tags;
                                  const newTags = currentTags.filter(t => t !== tag);
                                  handleUpdateSkillField('tags', newTags);
                                }}
                                className="hover:text-red-600 transition-colors"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </span>
                          ))}
                        </div>
                      );
                    })()}
                  </div>
                </div>

                {/* Files Section */}
                <div className="border-t border-gray-200 pt-4 mt-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="type-label text-gray-700">Files</h3>
                  </div>

                  <div className="flex gap-4 h-[600px]">
                    {/* File Tree */}
                    <div className="w-56 border-r border-gray-200 pr-4 overflow-y-auto scrollbar-hide">
                      {fileTree.map((node) => (
                        <FileTree
                          key={node.path}
                          node={node}
                          selectedPath={selectedFile}
                          onSelect={(path) => handleFileSelect(selectedSkill!.id, path)}
                        />
                      ))}
                    </div>

                    {/* File Editor */}
                    <div className="flex-1 flex flex-col">
                      {selectedFile ? (
                        <>
                          <div className="flex items-center gap-2 mb-2 type-body-sm text-gray-600">
                            <File className="w-4 h-4" />
                            <span className="font-mono">{selectedFile}</span>
                          </div>
                          <Textarea
                            value={pendingChanges.fileContent !== undefined ? pendingChanges.fileContent : fileContent}
                            onChange={(e) => {
                              setPendingChanges(prev => ({ ...prev, fileContent: e.target.value }));
                              setHasUnsavedChanges(true);
                            }}
                            className="flex-1 w-full px-4 py-2 font-mono type-body-sm resize-none scrollbar-hide"
                          />
                        </>
                      ) : (
                        <EmptyState
                          icon={FileText}
                          title="Select a file to edit"
                          centered
                        />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : loading ? (
            <LoadingState message="Loading..." />
          ) : (
            <EmptyState
              icon={Zap}
              title="Select a skill to view details"
              description="or create a new one to get started"
              centered
            />
          )}
        </div>

        {/* Import Modal */}
        <StandardModal
          isOpen={isImportModalOpen}
          onClose={handleCloseImportModal}
          size="small"
        >
                  {/* Header */}
                  <div className="px-4 lg:px-6 py-2.5 lg:py-3 border-b border-gray-200 flex items-center justify-between">
                    <h2 className="text-base font-semibold text-gray-900">
                      Import Skill
                    </h2>
                    <button
                      onClick={handleCloseImportModal}
                      disabled={isImporting}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                    >
                      <Plus className="w-5 h-5 text-gray-500 rotate-45" />
                    </button>
                  </div>

                  {/* Form */}
                  <div className="p-4 lg:p-6 space-y-4">
                    <div>
                      <label className="block type-label text-gray-700 mb-1">
                        Source URL or Path <span className="text-red-600">*</span>
                      </label>
                      <Input
                        value={importSource}
                        onChange={(e) => setImportSource(e.target.value)}
                        placeholder="https://github.com/user/repo/tree/branch/.claude/skills/skill-name"
                        disabled={isImporting}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !isImporting) {
                            handleImport();
                          }
                        }}
                      />
                      <p className="type-caption text-gray-500 mt-1">
                        GitHub URL, custom repo, or local path
                      </p>
                    </div>

                    <div>
                      <label className="block type-label text-gray-700 mb-1">
                        Custom Skill ID
                      </label>
                      <Input
                        value={importSkillId}
                        onChange={(e) => setImportSkillId(e.target.value)}
                        placeholder="my-custom-skill-id"
                        disabled={isImporting}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !isImporting) {
                            handleImport();
                          }
                        }}
                      />
                    </div>

                    {/* Status Message */}
                    {importStatus && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={cn(
                          "flex items-start gap-3 p-4 rounded-lg",
                          importStatus.type === 'success'
                            ? "bg-green-50 border border-green-200"
                            : "bg-red-50 border border-red-200"
                        )}
                      >
                        {importStatus.type === 'success' ? (
                          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        ) : (
                          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <p className={cn(
                            "type-label",
                            importStatus.type === 'success' ? "text-green-900" : "text-red-900"
                          )}>
                            {importStatus.type === 'success' ? 'Success!' : 'Error'}
                          </p>
                          <p className={cn(
                            "type-body-sm mt-1",
                            importStatus.type === 'success' ? "text-green-700" : "text-red-700"
                          )}>
                            {importStatus.message}
                          </p>
                        </div>
                      </motion.div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="px-4 py-4 flex justify-center">
                    <ModalActionButton
                      onClick={handleImport}
                      disabled={isImporting || !importSource.trim()}
                      loading={isImporting}
                      icon={Download}
                    >
                      {isImporting ? 'Importing...' : 'Import'}
                    </ModalActionButton>
                  </div>
        </StandardModal>

        {/* Icon Picker Popup */}
        <AnimatePresence>
          {showIconPicker && iconButtonRef.current && (
            <>
              {/* Invisible overlay to close on outside click */}
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowIconPicker(false)}
              />
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                transition={{ duration: 0.15 }}
                className="fixed z-50 bg-white rounded-xl border border-gray-200 shadow-xl p-5 w-96"
                style={{
                  top: `${iconButtonRef.current.getBoundingClientRect().bottom + 8}px`,
                  left: `${iconButtonRef.current.getBoundingClientRect().left}px`,
                }}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <h3 className="type-title text-gray-900">Select Icon</h3>
                  <button
                    onClick={() => setShowIconPicker(false)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </div>

                {/* Icon Grid */}
                <div className="grid grid-cols-6 gap-2 mb-4">
                  {ICON_OPTIONS.map(({ value, label, Icon }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => {
                        setFormData({ ...formData, icon: value });
                      }}
                      className={cn(
                        "aspect-square p-3 rounded-lg border-2 flex items-center justify-center transition-all hover:border-primary/40 hover:bg-muted/50",
                        formData.icon === value
                          ? "border-primary bg-muted/50 shadow-sm"
                          : "border-gray-200 bg-white"
                      )}
                      title={label}
                      aria-label={`Select ${label} icon`}
                      aria-pressed={formData.icon === value}
                      role="radio"
                      aria-checked={formData.icon === value}
                    >
                      <Icon className={cn(
                        "w-6 h-6 transition-colors",
                        formData.icon === value ? "text-primary" : "text-gray-600"
                      )} />
                    </button>
                  ))}
                </div>

                {/* Separator */}
                <div className="border-t border-gray-200 mb-4"></div>

                {/* Color Selector */}
                <div className="space-y-3">
                  <label className="block type-label text-gray-700">
                    Icon Background Color
                  </label>
                  <div className="grid grid-cols-8 gap-1.5">
                    {[
                      '#4A90E2', // blue
                      '#E24A90', // pink
                      '#90E24A', // green
                      '#E2904A', // orange
                      '#4AE290', // teal
                      '#904AE2', // purple
                      '#E2E24A', // yellow
                      '#4A4AE2', // indigo
                      '#E24A4A', // red
                      '#4AE2E2', // cyan
                      '#8B5CF6', // violet
                      '#10B981', // emerald
                      '#F59E0B', // amber
                      '#EF4444', // crimson
                      '#EC4899', // magenta
                      '#78716c', // stone
                    ].map((color) => (
                      <button
                        key={color}
                        type="button"
                        onClick={() => setFormData({ ...formData, iconColor: color })}
                        className={cn(
                          "w-7 h-7 rounded-md border-2 transition-all hover:scale-110",
                          formData.iconColor === color
                            ? "border-gray-900 ring-2 ring-offset-1 ring-gray-400"
                            : "border-gray-200"
                        )}
                        style={{ backgroundColor: color }}
                        title={color}
                        aria-label={`Select ${color} color${formData.iconColor === color ? ' (selected)' : ''}`}
                        aria-pressed={formData.iconColor === color}
                      >
                        <span className="sr-only">{formData.iconColor === color && 'Selected'}</span>
                      </button>
                    ))}
                  </div>

                  {/* Custom Color Input */}
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={formData.iconColor}
                      onChange={(e) => setFormData({ ...formData, iconColor: e.target.value })}
                      className="w-12 h-10 rounded-lg border border-gray-300 cursor-pointer"
                      aria-label="Pick custom icon color"
                    />
                    <Input
                      type="text"
                      value={formData.iconColor}
                      onChange={(e) => setFormData({ ...formData, iconColor: e.target.value })}
                      placeholder="#4A90E2"
                      className="flex-1 type-body-sm font-mono"
                    />
                  </div>
                </div>

                {/* Done Button */}
                <button
                  onClick={async () => {
                    await handleUpdateIconOrColor();
                    setShowIconPicker(false);
                  }}
                  className="w-full mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary transition-colors type-label"
                >
                  Done
                </button>
              </motion.div>
            </>
          )}
        </AnimatePresence>

      {/* Skill Assistant Chat Toggle Button */}
      {/* Create Skill Modal */}
      <AdaptiveModal
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        size="small"
      >
                {/* Header */}
                <div className="px-4 lg:px-6 py-2.5 lg:py-3 border-b border-gray-200 flex items-center justify-between">
                  <h2 className="text-base font-semibold text-gray-900">
                    New Skill
                  </h2>
                  <button
                    onClick={() => setShowCreateDialog(false)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <Plus className="w-5 h-5 text-gray-500 rotate-45" />
                  </button>
                </div>

                {/* Form */}
                <div className="p-4 lg:p-6 space-y-4">
                  <div>
                    <label className="block type-label text-gray-700 mb-1">
                      Skill Name <span className="text-red-600">*</span>
                    </label>
                    <Input
                      value={createSkillName}
                      onChange={(e) => setCreateSkillName(e.target.value)}
                      placeholder="e.g., Database Query Helper"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && createSkillName.trim()) {
                          handleConfirmCreate();
                        } else if (e.key === 'Escape') {
                          setShowCreateDialog(false);
                        }
                      }}
                    />
                  </div>
                </div>

                {/* Actions */}
                <div className="px-4 py-4 flex justify-center">
                  <ModalActionButton
                    onClick={handleConfirmCreate}
                    disabled={!createSkillName.trim()}
                    icon={Plus}
                  >
                    Create Skill
                  </ModalActionButton>
                </div>
      </AdaptiveModal>
      </div>
      </div>
      )}
    </MainLayout>
  );
}
