import { useState, useEffect } from 'react';
import { X, Users, Search, FileText, Loader2, ArrowRight } from 'lucide-react';
import { StandardModal } from '@/components/ui';

interface WelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSetupTeam: (team: 'dev' | 'research' | 'content') => Promise<void>;
}

type OnboardingStep = 'welcome' | 'template';

export function WelcomeModal({ isOpen, onClose, onSetupTeam }: WelcomeModalProps) {
  const [step, setStep] = useState<OnboardingStep>('welcome');
  const [selectedTeam, setSelectedTeam] = useState<'dev' | 'research' | 'content' | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Reset to welcome step when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep('welcome');
      setSelectedTeam(null);
    }
  }, [isOpen]);

  const teams = [
    {
      id: 'dev' as const,
      name: 'Development Team',
      description: 'Build features end-to-end with frontend, backend, and testing',
      icon: Users,
      iconColor: 'text-blue-600',
      iconBgColor: 'bg-blue-100',
      agents: ['Frontend Developer', 'Backend Developer', 'QA Tester'],
    },
    {
      id: 'research' as const,
      name: 'Research Team',
      description: 'Research, analyze, and synthesize information into insights',
      icon: Search,
      iconColor: 'text-purple-600',
      iconBgColor: 'bg-purple-100',
      agents: ['Research Analyst', 'Data Analyst', 'Report Writer'],
    },
    {
      id: 'content' as const,
      name: 'Content Team',
      description: 'Create documentation and content collaboratively',
      icon: FileText,
      iconColor: 'text-green-600',
      iconBgColor: 'bg-green-100',
      agents: ['Technical Writer', 'Content Writer', 'Editor'],
    },
  ];

  const handleSetup = async () => {
    if (!selectedTeam) return;

    setIsLoading(true);
    try {
      await onSetupTeam(selectedTeam);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <StandardModal isOpen={isOpen} onClose={onClose} size="medium" disableEscapeKey>
      {step === 'welcome' ? (
        <>
          {/* Welcome Step - Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors p-1 hover:bg-muted rounded-lg z-10"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Welcome Step - Centered Content */}
          <div className="flex-1 overflow-y-auto p-8 flex flex-col items-center justify-center">
            <div className="max-w-3xl w-full space-y-8">
              {/* Logo */}
              <div className="flex justify-center">
                <div className="w-32 h-32 rounded-2xl bg-white p-4 flex items-center justify-center">
                  <img src="/logo.png" alt="KumiAI Logo" className="w-full h-full object-contain" />
                </div>
              </div>

              {/* Welcome Text */}
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold text-foreground">
                  Welcome to KumiAI
                </h2>
                <p className="text-base text-muted-foreground">
                  Your AI-powered multi-agent collaboration platform
                </p>
              </div>

              {/* Features */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
                <div className="p-6 rounded-xl bg-card border border-border">
                  <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center mb-4 mx-auto">
                    <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 className="font-semibold text-foreground mb-2 text-center">Agent Orchestration</h3>
                  <p className="text-sm text-muted-foreground text-center">
                    Coordinate multiple AI agents to collaborate seamlessly on complex workflows
                  </p>
                </div>

                <div className="p-6 rounded-xl bg-card border border-border">
                  <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center mb-4 mx-auto">
                    <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                    </svg>
                  </div>
                  <h3 className="font-semibold text-foreground mb-2 text-center">Project Management</h3>
                  <p className="text-sm text-muted-foreground text-center">
                    Track tasks and manage workflows with real-time updates and visual boards
                  </p>
                </div>

                <div className="p-6 rounded-xl bg-card border border-border">
                  <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center mb-4 mx-auto">
                    <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                    </svg>
                  </div>
                  <h3 className="font-semibold text-foreground mb-2 text-center">Customizable Agents</h3>
                  <p className="text-sm text-muted-foreground text-center">
                    Build tailored agents with custom skills and capabilities for your unique needs
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Welcome Step - Footer */}
          <div className="p-6 bg-muted/30 border-t border-border flex items-center justify-end gap-4">
            <button
              onClick={() => setStep('template')}
              className="
                px-8 py-2.5 bg-primary text-primary-foreground rounded-lg font-medium text-sm
                hover:bg-primary/90 hover:shadow-lg transition-all
                flex items-center gap-2
              "
            >
              Next
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </>
      ) : (
        <>
          {/* Template Selection Step - Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors p-1 hover:bg-muted rounded-lg z-10"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Template Selection Step - Content */}
          <div className="flex-1 overflow-y-auto p-8 space-y-5">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Choose Your Team Template
              </h3>
              <p className="text-sm text-muted-foreground">
                Start with a pre-configured team to see multi-agent collaboration in action
              </p>
            </div>

            <div className="space-y-3">
              {teams.map((team) => {
                const Icon = team.icon;
                const isSelected = selectedTeam === team.id;

                return (
                  <button
                    key={team.id}
                    onClick={() => setSelectedTeam(team.id)}
                    className={`
                      group w-full text-left p-5 rounded-xl border-2 transition-all duration-200
                      ${isSelected
                        ? 'border-primary bg-primary/5 shadow-lg shadow-primary/10'
                        : 'border-border hover:border-primary/30 bg-card hover:shadow-md'
                      }
                    `}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`
                        p-3 rounded-xl transition-all duration-200 ${team.iconBgColor} ${team.iconColor}
                        ${isSelected ? 'shadow-md' : ''}
                      `}>
                        <Icon className="w-7 h-7" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-foreground text-base mb-1">{team.name}</h3>
                        <p className="text-sm text-muted-foreground leading-relaxed mb-3">{team.description}</p>
                        <div className="flex flex-wrap gap-2">
                          {team.agents.map((agent) => (
                            <span
                              key={agent}
                              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
                                isSelected
                                  ? 'bg-primary/10 text-primary'
                                  : 'bg-muted text-muted-foreground'
                              }`}
                            >
                              {agent}
                            </span>
                          ))}
                        </div>
                      </div>
                      {isSelected && (
                        <div className="flex-shrink-0 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                          <svg className="w-3 h-3 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Template Selection Step - Footer */}
          <div className="p-6 bg-muted/30 border-t border-border flex items-center justify-between gap-4">
            <button
              onClick={onClose}
              className="px-5 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-background rounded-lg transition-all"
            >
              Skip for now
            </button>
            <button
              onClick={handleSetup}
              disabled={!selectedTeam || isLoading}
              className="
                px-8 py-2.5 bg-primary text-primary-foreground rounded-lg font-medium text-sm
                hover:bg-primary/90 hover:shadow-lg transition-all
                disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none
                flex items-center gap-2
              "
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Setting up your team...
                </>
              ) : (
                <>
                  Get Started
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </>
      )}
    </StandardModal>
  );
}
