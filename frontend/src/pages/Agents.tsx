import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  api,
  Agent,
  UpdateAgentRequest
} from '@/lib/api';
import type { ChatContext } from '@/types/chat';
import type { McpServer, SkillMetadata, FileNode } from '@/types';
import { Plus, Trash2, X, User, Settings, Cpu, Package, ChevronRight, ChevronDown, File, Folder, FileText, FileEdit, Edit2 } from 'lucide-react';
import { FileTree } from '@/components/features/files';
import { buildFileTree, type FileTreeNode } from '@/lib/utils';
import { Button } from '@/components/ui/primitives/button';
import { Input } from '@/components/ui/primitives/input';
import { Textarea } from '@/components/ui/primitives/textarea';
import { Card } from '@/components/ui/primitives/card';
import { ModalActionButton } from '@/ui';
import { LoadingState, Sheet, SheetContent, AdaptiveModal, EmptyState } from '@/components/ui';
import { Avatar } from '@/ui';
import { SkillSelector } from '@/components/features/skills';
import { McpServerSelector } from '@/components/features/agents';
import { AgentAssistantChat } from '@/components/features/agents';
import { AgentsList } from '@/components/features/agents';
import { MainLayout } from '@/components/layout';
import { MainHeader } from '@/components/layout';
import { SidebarNav } from '@/components/layout';
import { SidebarFooter } from '@/components/layout';
import { cn } from '@/lib/utils';
import { getSkillIcon } from '@/constants/skillIcons';
import { paths } from '@/lib/utils/config';
import { useIsMobile, useIsDesktop, useToast } from '@/hooks';

interface AgentsProps {
  onChatContextChange?: (context: ChatContext) => void;
}

export default function Agents({ onChatContextChange }: AgentsProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [showNameDialog, setShowNameDialog] = useState(false);
  const [newAgentName, setNewAgentName] = useState('');
  const [availableSkills, setAvailableSkills] = useState<SkillMetadata[]>([]);
  const [availableMcpServers, setAvailableMcpServers] = useState<McpServer[]>([]);
  const [agentFiles, setAgentFiles] = useState<FileNode[]>([]);
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [newTag, setNewTag] = useState('');
  const [showColorPicker, setShowColorPicker] = useState(false);
  const avatarButtonRef = useRef<HTMLButtonElement>(null);
  const [agentsReloadTrigger, setAgentsReloadTrigger] = useState(0);

  // Responsive hooks
  const isMobile = useIsMobile();
  const isDesktop = useIsDesktop();
  const toast = useToast();

  // Track pending changes
  const [pendingChanges, setPendingChanges] = useState<Partial<Agent> & { fileContent?: string }>({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    loadAgents();
    loadAvailableSkills();
    loadAvailableMcpServers();

    // Set chat context to agents library on mount
    if (onChatContextChange) {
      onChatContextChange({
        role: null,
        name: 'Agent Library',
        description: 'Manage agents - create new agents, modify existing ones, or delete agents. Agents are stored as file-based CLAUDE.md files. Each agent has: name, default_model (sonnet/opus/haiku), tags, skills, allowed_tools, allowed_mcps, and icon_color in YAML frontmatter. Description and personality live in the markdown body of CLAUDE.md.',
        data: {
          project_path: paths.characterLibrary,
        },
      });
    }
  }, []);

  // Reset pending changes when agent changes
  useEffect(() => {
    setPendingChanges({});
    setHasUnsavedChanges(false);
  }, [selectedAgent?.id]);

  const loadAvailableSkills = async () => {
    try {
      const skills = await api.getSkills();
      setAvailableSkills(skills);
    } catch (error) {
      console.error('Failed to load skills:', error);
    }
  };

  const loadAvailableMcpServers = async () => {
    try {
      const servers = await api.getMcpServers();
      setAvailableMcpServers(servers);
    } catch (error) {
      console.error('Failed to load MCP servers:', error);
    }
  };

  const loadAgents = async () => {
    try {
      const data = await api.getAgents();
      setAgents(data);
      // Auto-select first agent if available and nothing is selected
      if (data.length > 0 && !selectedAgent) {
        loadAgent(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAgent = async (agentId: string) => {
    try {
      const agent = await api.getAgent(agentId);
      setSelectedAgent(agent);

      // Load file tree
      try {
        const files = await api.getAgentFiles(agentId);
        setAgentFiles(files);
        setFileTree(buildFileTree(files));

        // Auto-select CLAUDE.md if it exists
        const claudeMd = files.find(f => f.name === 'CLAUDE.md');
        if (claudeMd) {
          handleFileSelect(agentId, claudeMd.path);
        } else {
          setSelectedFile(null);
          setFileContent('');
        }
      } catch (error) {
        // Agent might not have a directory yet
        setAgentFiles([]);
        setFileTree([]);
        setSelectedFile(null);
        setFileContent('');
      }
    } catch (error) {
      console.error('Failed to load agent:', error);
    }
  };

  const handleFileSelect = async (agentId: string, filePath: string) => {
    try {
      setSelectedFile(filePath);
      const result = await api.getAgentFileContent(agentId, filePath);
      setFileContent(result.content);
    } catch (error) {
      console.error('Failed to load file:', error);
    }
  };

  const handleFileSave = async () => {
    if (!selectedAgent || !selectedFile) return;

    try {
      await api.updateAgentFileContent(selectedAgent.id, selectedFile, fileContent);
      // Reload agent metadata if CLAUDE.md was edited, but don't reload the file content
      if (selectedFile === 'CLAUDE.md') {
        const agent = await api.getAgent(selectedAgent.id);
        setSelectedAgent(agent);
        // Don't reload file content to avoid overwriting user's edits
      }
    } catch (error) {
      console.error('Failed to save file:', error);
    }
  };


  const handleCreateAgent = async () => {
    if (!newAgentName.trim()) {
      toast.warning('Agent name is required', 'Validation Error');
      return;
    }

    try {
      const agent = await api.createAgent({ name: newAgentName.trim() });
      setShowNameDialog(false);
      setNewAgentName('');
      await loadAgents();
      setAgentsReloadTrigger(prev => prev + 1); // Trigger reload
      // Select the newly created agent
      await loadAgent(agent.id);
    } catch (error) {
      console.error('Failed to create agent:', error);
      toast.error('Failed to create agent: ' + (error instanceof Error ? error.message : 'Unknown error'), 'Error');
    }
  };

  const handleDelete = async (agentId: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;

    try {
      await api.deleteAgent(agentId);
      await loadAgents();
      setAgentsReloadTrigger(prev => prev + 1); // Trigger reload
      if (selectedAgent?.id === agentId) {
        setSelectedAgent(null);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to delete agent: ' + errorMessage, 'Error');
    }
  };

  const handleUpdateModel = (model: string) => {
    if (!selectedAgent) return;

    setPendingChanges(prev => ({
      ...prev,
      default_model: model
    }));
    setHasUnsavedChanges(true);
  };

  const handleUpdateAgent = (updates: UpdateAgentRequest) => {
    if (!selectedAgent) return;

    setPendingChanges(prev => ({
      ...prev,
      ...updates
    }));
    setHasUnsavedChanges(true);
  };

  const handleUpdateSkills = (skills: string[]) => {
    if (!selectedAgent) return;

    setPendingChanges(prev => ({
      ...prev,
      skills
    }));
    setHasUnsavedChanges(true);
  };

  const handleUpdateMcpServers = (mcps: string[]) => {
    if (!selectedAgent) return;

    setPendingChanges(prev => ({
      ...prev,
      allowed_mcps: mcps
    }));
    setHasUnsavedChanges(true);
  };

  const handleUpdateAllChanges = async () => {
    if (!selectedAgent || !hasUnsavedChanges) return;

    try {
      // Update agent metadata if there are changes
      const metadataChanges: any = {};
      Object.keys(pendingChanges).forEach(key => {
        if (key !== 'fileContent' && pendingChanges[key as keyof typeof pendingChanges] !== undefined) {
          metadataChanges[key] = pendingChanges[key as keyof typeof pendingChanges];
        }
      });

      if (Object.keys(metadataChanges).length > 0) {
        await api.updateAgent(selectedAgent.id, metadataChanges);
      }

      // Save file content if changed
      if (pendingChanges.fileContent !== undefined && selectedFile) {
        await api.updateAgentFileContent(selectedAgent.id, selectedFile, pendingChanges.fileContent);
      }

      // Reload both the selected agent and the agents list to update the card
      await Promise.all([
        loadAgent(selectedAgent.id),
        loadAgents()
      ]);

      // Clear pending changes
      setPendingChanges({});
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Failed to update agent:', error);
      toast.error('Failed to update agent', 'Error');
    }
  };

  const addSkill = (skillId: string) => {
    if (!selectedAgent) return;
    const currentSkills = pendingChanges.skills !== undefined ? pendingChanges.skills : selectedAgent.skills;
    const newSkills = [...currentSkills, skillId];
    handleUpdateSkills(newSkills);
  };

  const removeSkill = (skillId: string) => {
    if (!selectedAgent) return;
    const currentSkills = pendingChanges.skills !== undefined ? pendingChanges.skills : selectedAgent.skills;
    const newSkills = currentSkills.filter(id => id !== skillId);
    handleUpdateSkills(newSkills);
  };

  const addMcpServer = (serverId: string) => {
    if (!selectedAgent) return;
    const currentMcps = pendingChanges.allowed_mcps !== undefined ? pendingChanges.allowed_mcps : selectedAgent.allowed_mcps;
    const newMcps = [...currentMcps, serverId];
    handleUpdateMcpServers(newMcps);
  };

  const removeMcpServer = (serverId: string) => {
    if (!selectedAgent) return;
    const currentMcps = pendingChanges.allowed_mcps !== undefined ? pendingChanges.allowed_mcps : selectedAgent.allowed_mcps;
    const newMcps = currentMcps.filter(id => id !== serverId);
    handleUpdateMcpServers(newMcps);
  };

  // Handler for selecting agent
  const handleSelectAgent = async (agentId: string) => {
    // Load agent (works for both mobile and desktop)
    await loadAgent(agentId);
  };

  return (
    <MainLayout
      leftSidebarNav={<SidebarNav />}
      leftSidebarContent={
        <AgentsList
          currentAgentId={selectedAgent?.id}
          onSelectAgent={handleSelectAgent}
          onDeleteAgent={handleDelete}
          onCreateAgent={() => setShowNameDialog(true)}
          isMobile={isMobile}
          reloadTrigger={agentsReloadTrigger}
        />
      }
      leftSidebarFooter={<SidebarFooter />}
      rightSidebarContent={
        <AgentAssistantChat
          isOpen={true}
          onToggle={() => {}}
          agentId={selectedAgent?.id}
          agentName={selectedAgent?.name}
          onAgentUpdated={() => {
            if (selectedAgent?.id) {
              loadAgent(selectedAgent.id);
            }
          }}
          className="bg-gray-50"
        />
      }
    >
      {({ leftSidebarOpen, rightSidebarOpen, toggleLeftSidebar, toggleRightSidebar }) => (
      <div className="flex-1 flex flex-col overflow-hidden bg-white">
        <MainHeader
          breadcrumb={selectedAgent ? "Agents" : undefined}
          title={selectedAgent?.name || "Agents"}
          leftSidebarOpen={leftSidebarOpen}
          onToggleLeftSidebar={toggleLeftSidebar}
          rightSidebarOpen={rightSidebarOpen}
          onToggleRightSidebar={toggleRightSidebar}
          actions={
            selectedAgent && (
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
        {/* Mobile: Agent List Sheet */}
        <Sheet open={isMobile && !selectedAgent} onOpenChange={() => {}}>
          <SheetContent side="left" className="w-full p-0">
            <div className="flex flex-col h-full">
              <AgentsList
                currentAgentId={selectedAgent?.id}
                onSelectAgent={handleSelectAgent}
                onDeleteAgent={handleDelete}
                onCreateAgent={() => setShowNameDialog(true)}
                isMobile={true}
                reloadTrigger={agentsReloadTrigger}
              />
            </div>
          </SheetContent>
        </Sheet>

        {/* Right: Agent Detail */}
        <div className={cn(
          "flex-1 flex flex-col min-w-0 overflow-hidden bg-white",
          // On mobile, only show when an agent is selected
          isMobile ? (selectedAgent ? "flex" : "hidden") : "flex"
        )}>
        {selectedAgent ? (
          <>
            {/* Mobile Back Button */}
            {selectedAgent && (
              <div className="lg:hidden flex-shrink-0 border-b border-gray-200 bg-white px-4 py-3">
                <button
                  onClick={() => {
                    setSelectedAgent(null);
                  }}
                  className="flex items-center gap-2 text-gray-700 hover:text-gray-900 transition-colors"
                >
                  <ChevronRight className="w-5 h-5 rotate-180" />
                  <span className="type-label">Back to Agents</span>
                </button>
              </div>
            )}

            {/* Detail View */}
            <div className="flex-1 overflow-y-auto px-4 lg:px-6 pb-4 lg:pb-6 scrollbar-hide">
                {/* Agent Header */}
                <div className="flex items-center gap-3 h-12">
                  <button
                    ref={avatarButtonRef}
                    onClick={() => setShowColorPicker(!showColorPicker)}
                    className="relative group flex-shrink-0"
                    type="button"
                    aria-label="Change agent avatar color"
                    aria-expanded={showColorPicker}
                    aria-haspopup="dialog"
                  >
                    <Avatar seed={selectedAgent.id} size={40} className="transition-all group-hover:ring-2 group-hover:ring-ring" color={selectedAgent.icon_color} />
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded-full transition-all">
                      <Edit2 className="w-3 h-3 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </button>
                  <div className="flex-1 min-w-0 relative">
                    <h3 className="type-title text-gray-900 truncate">{selectedAgent.name}</h3>
                    <p className="type-caption text-gray-500 truncate">{selectedAgent.id}</p>

                  </div>

                  {/* Color Picker Popup */}
                  <AnimatePresence>
                    {showColorPicker && (
                        <>
                          {/* Backdrop */}
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black bg-opacity-50 z-40"
                            onClick={() => setShowColorPicker(false)}
                          />

                          {/* Popup */}
                          <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: -10 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: -10 }}
                            transition={{ duration: 0.15 }}
                            className="absolute top-full left-0 mt-2 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 p-4 z-50"
                          >
                            <h4 className="type-subtitle text-gray-900 mb-3">Avatar Color</h4>

                            {/* Color Picker */}
                            <div className="space-y-3">
                              <div className="flex gap-2">
                                <input
                                  type="color"
                                  value={selectedAgent.icon_color}
                                  onChange={(e) => handleUpdateAgent({ icon_color: e.target.value })}
                                  className="h-10 w-16 rounded-lg border border-gray-300 cursor-pointer"
                                  aria-label="Pick avatar color"
                                />
                                <Input
                                  value={selectedAgent.icon_color}
                                  onChange={(e) => handleUpdateAgent({ icon_color: e.target.value })}
                                  placeholder="#4A90E2"
                                  className="flex-1 font-mono type-body-sm"
                                  aria-label="Avatar color hex code"
                                />
                              </div>
                            </div>

                            {/* Done Button */}
                            <button
                              onClick={() => setShowColorPicker(false)}
                              className="w-full mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary transition-colors type-label"
                            >
                              Done
                            </button>
                          </motion.div>
                        </>
                      )}
                    </AnimatePresence>
                </div>

                {/* Agent Details */}
                <div className="py-4 space-y-3">
                  <div>
                    <label className="block type-caption text-gray-600 mb-1">Name</label>
                    <Input
                      value={pendingChanges.name !== undefined ? pendingChanges.name : selectedAgent.name}
                      onChange={(e) => handleUpdateAgent({ name: e.target.value })}
                      placeholder="Agent name"
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block type-caption text-gray-600 mb-1">Description</label>
                    <Textarea
                      value={pendingChanges.description !== undefined ? pendingChanges.description : (selectedAgent.description || '')}
                      onChange={(e) => handleUpdateAgent({ description: e.target.value })}
                      placeholder="Agent description"
                      rows={2}
                      className="px-3 py-2 resize-none"
                    />
                  </div>

                  <div>
                    <label className="block type-caption text-gray-600 mb-1">Default Model</label>
                    <select
                      value={pendingChanges.default_model !== undefined ? pendingChanges.default_model : selectedAgent.default_model}
                      onChange={(e) => handleUpdateModel(e.target.value)}
                      className="flex h-9 w-full rounded-lg border border-input bg-background px-3 py-1 text-base shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring/30 focus-visible:border-input disabled:cursor-not-allowed disabled:opacity-50 md:text-sm"
                    >
                      <option value="haiku">Haiku (Fast)</option>
                      <option value="sonnet">Sonnet (Balanced)</option>
                      <option value="opus">Opus (Powerful)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block type-caption text-gray-600 mb-1">Tags</label>
                    <Input
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && newTag.trim()) {
                          const currentTags = pendingChanges.tags !== undefined ? pendingChanges.tags : selectedAgent.tags;
                          const updatedTags = [...currentTags, newTag.trim()];
                          handleUpdateAgent({ tags: updatedTags });
                          setNewTag('');
                        }
                      }}
                      placeholder="Add tag..."
                      className="w-full"
                    />
                    {(() => {
                      const displayTags = pendingChanges.tags !== undefined ? pendingChanges.tags : selectedAgent.tags;
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
                                  const currentTags = pendingChanges.tags !== undefined ? pendingChanges.tags : selectedAgent.tags;
                                  const newTags = currentTags.filter(t => t !== tag);
                                  handleUpdateAgent({ tags: newTags });
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

                {/* Capabilities Section */}
                <div className="border-t border-gray-200 pt-4 mt-4">
                  <h3 className="type-label text-gray-700 mb-3">Capabilities</h3>
                  <div className="space-y-4">
                    {/* MCP Servers */}
                    <div>
                      <label className="block type-caption text-gray-600 mb-2">MCP Servers</label>
                      <McpServerSelector
                        availableServers={availableMcpServers}
                        selectedServerIds={pendingChanges.allowed_mcps !== undefined ? pendingChanges.allowed_mcps : selectedAgent.allowed_mcps}
                        onAddServer={addMcpServer}
                        onRemoveServer={removeMcpServer}
                        isEditing={true}
                      />
                    </div>

                    {/* Skills */}
                    <div>
                      <label className="block type-caption text-gray-600 mb-2">Skills</label>
                      <SkillSelector
                        availableSkills={availableSkills as any}
                        selectedSkillIds={pendingChanges.skills !== undefined ? pendingChanges.skills : selectedAgent.skills}
                        onAddSkill={addSkill}
                        onRemoveSkill={removeSkill}
                        isEditing={true}
                      />
                    </div>
                  </div>
                </div>

                {/* Files Section */}
                <div className="border-t border-gray-200 pt-4 mt-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="type-label text-gray-700">Files</h3>
                  </div>

                  <div className="flex flex-col lg:flex-row gap-4 h-auto lg:h-[600px]">
                    {/* File Tree */}
                    <div className="w-full lg:w-56 border-b lg:border-b-0 lg:border-r border-gray-200 pb-4 lg:pb-0 lg:pr-4 overflow-y-auto scrollbar-hide max-h-60 lg:max-h-none">
                      {fileTree.length > 0 ? (
                        <>
                          {fileTree.map((node) => (
                            <FileTree
                              key={node.path}
                              node={node}
                              selectedPath={selectedFile}
                              onSelect={(path) => handleFileSelect(selectedAgent.id, path)}
                            />
                          ))}
                        </>
                      ) : (
                        <EmptyState
                          icon={Folder}
                          title="No files yet"
                        />
                      )}
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
            icon={User}
            title="Select an agent"
            description="or create a new one to get started"
            centered
          />
        )}
      </div>

      {/* Create Agent Dialog */}
      <AdaptiveModal
        isOpen={showNameDialog}
        onClose={() => {
          setShowNameDialog(false);
          setNewAgentName('');
        }}
        size="small"
      >
              {/* Header */}
              <div className="px-4 lg:px-6 py-2.5 lg:py-3 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-base font-semibold text-gray-900">
                  New Agent
                </h2>
                <button
                  onClick={() => {
                    setShowNameDialog(false);
                    setNewAgentName('');
                  }}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <Plus className="w-5 h-5 text-gray-500 rotate-45" />
                </button>
              </div>

              {/* Form */}
              <div className="p-4 lg:p-6 space-y-4">
                <div>
                  <label className="block type-label text-gray-700 mb-1">
                    Agent Name <span className="text-red-600">*</span>
                  </label>
                  <Input
                    value={newAgentName}
                    onChange={(e) => setNewAgentName(e.target.value)}
                    placeholder="e.g., Product Manager"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && newAgentName.trim()) {
                        handleCreateAgent();
                      } else if (e.key === 'Escape') {
                        setShowNameDialog(false);
                        setNewAgentName('');
                      }
                    }}
                  />
                </div>
              </div>

              {/* Actions */}
              <div className="px-4 py-4 flex justify-center">
                <ModalActionButton
                  onClick={handleCreateAgent}
                  disabled={!newAgentName.trim()}
                  icon={Plus}
                >
                  Create Agent
                </ModalActionButton>
              </div>
      </AdaptiveModal>
      </div>
      </div>
      )}
    </MainLayout>
  );
}
