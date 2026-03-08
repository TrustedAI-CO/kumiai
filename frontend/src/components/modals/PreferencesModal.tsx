import { useState, useEffect } from 'react';
import { api, UserProfile as UserProfileType, CLIBackendsResponse, CLIUsageResponse, CLIUsageInfo, LiveUsageResponse, LiveUsageEntry } from '@/lib/api';
import { User, Save, Upload, X, Settings, AlertTriangle, Info, Cpu, CheckCircle2, XCircle, Zap, Clock, Gauge, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/primitives/button';
import { Textarea } from '@/components/ui/primitives/textarea';
import { LoadingState, StandardModal } from '@/components/ui';
import { cn, components } from '@/styles/design-system';

interface PreferencesModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: 'profile' | 'settings';
}

type TabType = 'profile' | 'settings';

const CLI_THEMES: Record<string, {
  gradient: string;
  border: string;
  text: string;
  accent: string;
  badge: string;
  badgeText: string;
  bar: string;
  glow: string;
  displayName: string;
  logo: string;
}> = {
  claude: {
    gradient: 'from-amber-50 via-orange-50 to-amber-100/50',
    border: 'border-amber-200/80',
    text: 'text-amber-950',
    accent: 'text-amber-600',
    badge: 'bg-amber-500',
    badgeText: 'text-white',
    bar: 'bg-gradient-to-r from-amber-400 to-orange-400',
    glow: 'shadow-amber-200/50',
    displayName: 'Claude Code',
    logo: 'A',
  },
  codex: {
    gradient: 'from-emerald-50 via-teal-50 to-emerald-100/50',
    border: 'border-emerald-200/80',
    text: 'text-emerald-950',
    accent: 'text-emerald-600',
    badge: 'bg-emerald-500',
    badgeText: 'text-white',
    bar: 'bg-gradient-to-r from-emerald-400 to-teal-400',
    glow: 'shadow-emerald-200/50',
    displayName: 'OpenAI Codex',
    logo: 'O',
  },
  gemini: {
    gradient: 'from-blue-50 via-indigo-50 to-blue-100/50',
    border: 'border-blue-200/80',
    text: 'text-blue-950',
    accent: 'text-blue-600',
    badge: 'bg-blue-500',
    badgeText: 'text-white',
    bar: 'bg-gradient-to-r from-blue-400 to-indigo-400',
    glow: 'shadow-blue-200/50',
    displayName: 'Google Gemini',
    logo: 'G',
  },
  opencode: {
    gradient: 'from-violet-50 via-purple-50 to-violet-100/50',
    border: 'border-violet-200/80',
    text: 'text-violet-950',
    accent: 'text-violet-600',
    badge: 'bg-violet-500',
    badgeText: 'text-white',
    bar: 'bg-gradient-to-r from-violet-400 to-purple-400',
    glow: 'shadow-violet-200/50',
    displayName: 'OpenCode',
    logo: 'OC',
  },
};

function formatNumber(n: number | null | undefined): string {
  if (n == null) return '-';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toString();
}

function formatResetTime(isoStr: string): string {
  const reset = new Date(isoStr);
  const now = new Date();
  const diffMs = reset.getTime() - now.getTime();
  if (diffMs <= 0) return 'now';
  const mins = Math.floor(diffMs / 60000);
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  const remainMins = mins % 60;
  if (hrs < 24) return remainMins > 0 ? `${hrs}h ${remainMins}m` : `${hrs}h`;
  const days = Math.floor(hrs / 24);
  return `${days}d ${hrs % 24}h`;
}

function UsageProgressBar({ label, utilization, resetsAt, theme }: {
  label: string;
  utilization: number;
  resetsAt: string | null;
  theme: typeof CLI_THEMES['claude'];
}) {
  const pct = Math.round(utilization * 100);
  const barColor = pct >= 80 ? 'bg-red-500' : pct >= 50 ? 'bg-amber-400' : theme.bar;
  const textColor = pct >= 80 ? 'text-red-400 font-bold' : pct >= 50 ? 'text-amber-500' : 'text-gray-500';

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-gray-500 font-medium">{label}</span>
        <span className="flex items-center gap-1.5">
          <span className={cn('text-[10px] font-semibold tabular-nums', textColor)}>{pct}%</span>
          {resetsAt && (
            <span className="text-[9px] text-gray-400 flex items-center gap-0.5">
              <Clock className="w-2.5 h-2.5" />
              {formatResetTime(resetsAt)}
            </span>
          )}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-gray-200/60 overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-700', barColor)}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
    </div>
  );
}

function CLIUsageCard({ usage, backendVersion, liveUsage }: { usage: CLIUsageInfo; backendVersion?: string | null; liveUsage?: LiveUsageEntry }) {
  const theme = CLI_THEMES[usage.name] || CLI_THEMES.claude;
  const isInstalled = usage.installed;
  const rl = usage.rate_limits;

  return (
    <div
      className={cn(
        'rounded-2xl border transition-all duration-300 overflow-hidden',
        isInstalled ? `bg-gradient-to-br ${theme.gradient}` : 'bg-gray-50/80',
        isInstalled ? theme.border : 'border-gray-200',
        isInstalled ? `shadow-sm hover:shadow-lg ${theme.glow}` : 'opacity-50'
      )}
    >
      {/* Header Bar */}
      <div className="px-4 pt-4 pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Logo Circle */}
            <div className={cn(
              'w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm shadow-sm',
              isInstalled ? `${theme.badge} ${theme.badgeText}` : 'bg-gray-300 text-gray-500'
            )}>
              {theme.logo}
            </div>
            <div>
              <h5 className={cn('text-sm font-bold tracking-tight', isInstalled ? theme.text : 'text-gray-400')}>
                {theme.displayName}
              </h5>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={cn(
                  'text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-full',
                  isInstalled ? `${theme.badge}/10 ${theme.accent}` : 'bg-gray-200 text-gray-400'
                )}>
                  {usage.plan}
                </span>
                {backendVersion && (
                  <span className="text-[10px] font-mono text-gray-400">{backendVersion}</span>
                )}
              </div>
            </div>
          </div>
          {/* Status Dot */}
          <div className="flex items-center gap-1.5">
            {isInstalled ? (
              <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-100/80">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                <span className="text-[10px] font-medium text-green-700">Active</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-gray-100">
                <div className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                <span className="text-[10px] font-medium text-gray-500">Offline</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {isInstalled && (
        <div className="px-4 pb-4 space-y-3">
          {/* Model Chip */}
          {usage.configured_model && (
            <div className="flex items-center gap-2">
              <Cpu className={cn('w-3 h-3', theme.accent)} />
              <span className={cn('text-xs font-mono font-semibold', theme.accent)}>{usage.configured_model}</span>
            </div>
          )}

          {/* Live Usage Bars */}
          {liveUsage && !liveUsage.error && liveUsage.windows.length > 0 && (
            <div className="bg-white/50 backdrop-blur-sm rounded-xl p-3 space-y-2">
              <div className="flex items-center gap-1.5 mb-1">
                <Gauge className="w-3 h-3 text-gray-500" />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">Usage</span>
              </div>
              {liveUsage.windows.map((w) => (
                <UsageProgressBar
                  key={w.label}
                  label={w.label}
                  utilization={w.utilization}
                  resetsAt={w.resets_at}
                  theme={theme}
                />
              ))}
            </div>
          )}

          {/* Error / Unauthenticated */}
          {liveUsage?.error === 'unauthenticated' && (
            <div className="bg-white/40 rounded-xl px-3 py-2">
              <span className="text-[10px] text-gray-400 italic">Sign in to view usage</span>
            </div>
          )}
          {liveUsage?.error && liveUsage.error !== 'unauthenticated' && liveUsage.error !== 'not_implemented' && (
            <div className="bg-white/40 rounded-xl px-3 py-2">
              <span className="text-[10px] text-gray-400 italic">Usage data unavailable</span>
            </div>
          )}

          {/* Fallback: Rate Limits (when no live data) */}
          {(!liveUsage || (liveUsage.error && liveUsage.error !== 'unauthenticated')) && rl && (
            <div className="bg-white/50 backdrop-blur-sm rounded-xl p-3 space-y-2.5">
              <div className="flex items-center gap-1.5 mb-1">
                <Gauge className="w-3 h-3 text-gray-500" />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">Plan Limits</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {rl.requests_per_minute != null && (
                  <LimitPill label="RPM" value={formatNumber(rl.requests_per_minute)} theme={theme} />
                )}
                {rl.requests_per_day != null && (
                  <LimitPill label="RPD" value={formatNumber(rl.requests_per_day)} theme={theme} />
                )}
                {rl.tokens_per_day != null && (
                  <LimitPill label="TPD" value={formatNumber(rl.tokens_per_day)} theme={theme} />
                )}
              </div>
              {rl.reset_window && (
                <div className="flex items-center gap-1.5 pt-1">
                  <Clock className="w-3 h-3 text-gray-400" />
                  <span className="text-[10px] text-gray-500">{rl.reset_window}</span>
                </div>
              )}
            </div>
          )}

          {/* Extra Info */}
          {Object.keys(usage.extra).length > 0 && (
            <div className="space-y-1">
              {Object.entries(usage.extra).map(([key, value]) => (
                <div key={key} className="flex justify-between text-[11px] px-1">
                  <span className="text-gray-500 capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className={cn('font-mono font-medium', theme.accent)}>{String(value)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Dashboard link removed - direct usage display is shown above */}
        </div>
      )}
    </div>
  );
}

function LimitPill({ label, value, theme }: { label: string; value: string; theme: typeof CLI_THEMES['claude'] }) {
  return (
    <div className="flex items-center justify-between bg-white/60 rounded-lg px-2.5 py-1.5">
      <span className="text-[10px] text-gray-500 font-medium">{label}</span>
      <span className={cn('text-xs font-bold font-mono', theme.accent)}>{value}</span>
    </div>
  );
}

export function PreferencesModal({ isOpen, onClose, initialTab = 'profile' }: PreferencesModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>(initialTab);
  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    avatar: '',
    description: '',
    preferences: {} as Record<string, any>,
  });
  const [preferencesText, setPreferencesText] = useState('');
  const [isResetting, setIsResetting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [versionInfo, setVersionInfo] = useState<{ backend_version: string | null; frontend_version: string | null; app_version: string } | null>(null);
  const [cliBackends, setCLIBackends] = useState<CLIBackendsResponse | null>(null);
  const [cliUsage, setCLIUsage] = useState<CLIUsageResponse | null>(null);
  const [liveUsage, setLiveUsage] = useState<LiveUsageResponse | null>(null);
  const [refreshingUsage, setRefreshingUsage] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadProfile();
      setActiveTab(initialTab);
      loadVersionInfo();
      loadCLIBackends();
      loadCLIUsage();
      loadLiveUsage();
    }
  }, [isOpen, initialTab]);

  const loadVersionInfo = async () => {
    try {
      const API_BASE = (await import('@/lib/api')).API_BASE;
      const res = await fetch(`${API_BASE}/api/v1/system/version`);
      if (res.ok) setVersionInfo(await res.json());
    } catch (error) {
      console.error('Failed to load version info:', error);
    }
  };

  const loadCLIBackends = async () => {
    try {
      setCLIBackends(await api.getCLIBackends());
    } catch (error) {
      console.error('Failed to load CLI backends:', error);
    }
  };

  const loadCLIUsage = async () => {
    try {
      setCLIUsage(await api.getCLIUsage());
    } catch (error) {
      console.error('Failed to load CLI usage:', error);
    }
  };

  const loadLiveUsage = async () => {
    try {
      setLiveUsage(await api.getLiveCLIUsage());
    } catch (error) {
      console.error('Failed to load live usage:', error);
    }
  };

  const handleRefreshLiveUsage = async () => {
    if (refreshingUsage) return;
    setRefreshingUsage(true);
    try {
      setLiveUsage(await api.getLiveCLIUsage());
    } catch (error) {
      console.error('Failed to refresh live usage:', error);
    } finally {
      setRefreshingUsage(false);
    }
  };

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await api.getUserProfile();
      setProfile(data);
      setFormData({
        avatar: data.avatar || '',
        description: data.description || '',
        preferences: data.preferences || {},
      });
      setPreferencesText(data.preferences ? JSON.stringify(data.preferences, null, 2) : '');
    } catch (error) {
      console.error('Failed to load user profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      let preferencesObj = {};
      if (preferencesText.trim()) {
        try {
          preferencesObj = JSON.parse(preferencesText);
        } catch (e) {
          alert('Invalid JSON in preferences. Please check your syntax.');
          setSaving(false);
          return;
        }
      }
      const updated = await api.updateUserProfile({
        ...formData,
        preferences: preferencesObj,
      });
      setProfile(updated);
      alert('Profile saved successfully!');
    } catch (error) {
      console.error('Failed to save profile:', error);
      alert('Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData({ ...formData, avatar: reader.result as string });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await api.resetApp();
      alert('App reset successfully. Reloading...');
      localStorage.clear();
      setTimeout(() => { window.location.href = '/'; }, 1000);
    } catch (error) {
      console.error('Failed to reset app:', error);
      alert('Failed to reset app');
      setIsResetting(false);
    }
  };

  const tabs = [
    { id: 'profile' as TabType, label: 'Profile', icon: User },
    { id: 'settings' as TabType, label: 'Settings', icon: Settings },
  ];

  return (
    <StandardModal isOpen={isOpen} onClose={onClose} size="large">
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <div className="w-48 bg-gray-50 border-r border-gray-200 flex flex-col">
          <nav className="flex-1 p-4 space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    activeTab === tab.id ? 'bg-gray-200 text-gray-900' : 'text-gray-700 hover:bg-gray-100'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right Content */}
        <div className="flex-1 flex flex-col bg-white px-6">
          <div className="flex items-center justify-between py-3 border-b border-gray-200">
            <h3 className="text-base font-semibold text-gray-900">
              {activeTab === 'profile' ? 'User Profile' : 'Settings'}
            </h3>
            <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-4">
            {loading ? (
              <LoadingState message="Loading..." />
            ) : (
              <>
                {activeTab === 'profile' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">Avatar</label>
                      <div className="flex items-center gap-3">
                        {formData.avatar ? (
                          <img src={formData.avatar} alt="Avatar" className="w-16 h-16 rounded-full object-cover border-2 border-gray-200" />
                        ) : (
                          <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center">
                            <User className="w-8 h-8 text-gray-400" />
                          </div>
                        )}
                        <div>
                          <label className="cursor-pointer">
                            <div className={cn(components.button.base, components.button.variants.secondary, "inline-flex items-center gap-1.5 text-sm")}>
                              <Upload className="w-3.5 h-3.5" /> Upload
                            </div>
                            <input type="file" accept="image/*" onChange={handleAvatarChange} className="hidden" />
                          </label>
                          <p className="text-xs text-gray-500 mt-1.5">JPG, PNG, or GIF. Max 2MB.</p>
                        </div>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
                      <Textarea
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        placeholder="Tell about yourself: who you are, what you do, your background, etc."
                        rows={3} className="resize-none text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-1">This will be included in the AI's system prompt.</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">Preferences (JSON)</label>
                      <Textarea
                        value={preferencesText}
                        onChange={(e) => setPreferencesText(e.target.value)}
                        placeholder='{"communicationStyle": "concise", "tone": "casual"}'
                        className="font-mono text-xs resize-none" rows={4}
                      />
                      <p className="text-xs text-gray-500 mt-1">JSON format preferences for AI interactions.</p>
                    </div>
                  </div>
                )}

                {activeTab === 'settings' && (
                  <div className="space-y-6">
                    {/* Version */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        <Info className="w-4 h-4" /> Version
                      </h4>
                      <div className="bg-gray-50 rounded-lg p-3 space-y-1.5 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">App</span>
                          <span className="font-mono text-gray-900">{versionInfo?.app_version || '...'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Backend</span>
                          <span className="font-mono text-gray-900">{versionInfo?.backend_version || '...'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Frontend</span>
                          <span className="font-mono text-gray-900">{versionInfo?.frontend_version || '...'}</span>
                        </div>
                      </div>
                    </div>

                    {/* AI Backends Usage */}
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                          <Zap className="w-4 h-4" /> AI Backends
                        </h4>
                        <button
                          onClick={handleRefreshLiveUsage}
                          disabled={refreshingUsage}
                          className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11px] text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors disabled:opacity-50"
                          title="Refresh usage data"
                        >
                          <RefreshCw className={cn('w-3 h-3', refreshingUsage && 'animate-spin')} />
                          Refresh
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        {cliUsage?.backends?.map(usage => {
                          const backend = cliBackends?.backends?.find(b => b.name === usage.name);
                          return (
                            <CLIUsageCard
                              key={usage.name}
                              usage={usage}
                              backendVersion={backend?.version}
                              liveUsage={liveUsage?.usage?.[usage.name]}
                            />
                          );
                        })}
                      </div>
                      {cliBackends && (
                        <div className="mt-3 flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg text-xs">
                          {cliBackends.codeagent_wrapper_installed ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                          ) : (
                            <XCircle className="w-3.5 h-3.5 text-gray-400" />
                          )}
                          <span className="text-gray-600">codeagent-wrapper</span>
                          {cliBackends.codeagent_wrapper_version && (
                            <span className="font-mono text-gray-500 ml-auto">{cliBackends.codeagent_wrapper_version}</span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Reset */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-2">Reset Application</h4>
                      <p className="text-sm text-gray-600 mb-4">
                        Reset the application to its initial state. This will delete all data except projects.
                      </p>
                    </div>

                    {!showConfirm ? (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div className="flex gap-3">
                          <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <h5 className="text-sm font-medium text-yellow-900 mb-1">Warning</h5>
                            <p className="text-sm text-yellow-800 mb-3">This will reset the application and delete all data including:</p>
                            <ul className="list-disc list-inside text-sm text-yellow-800 space-y-1 mb-3">
                              <li>Database (sessions, messages, etc.)</li>
                              <li>Skills</li>
                              <li>Agents</li>
                              <li>User settings</li>
                            </ul>
                            <p className="text-sm text-yellow-800 mb-4"><strong>Projects will be preserved</strong> and will not be deleted.</p>
                            <Button variant="destructive" onClick={() => setShowConfirm(true)} size="sm">
                              I understand, proceed to reset
                            </Button>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="flex gap-3">
                          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <h5 className="text-sm font-medium text-red-900 mb-2">Confirm Reset</h5>
                            <p className="text-sm text-red-800 mb-4">Are you absolutely sure? This action cannot be undone.</p>
                            <div className="flex gap-2">
                              <Button variant="destructive" onClick={handleReset} disabled={isResetting} size="sm">
                                {isResetting ? 'Resetting...' : 'Reset Application'}
                              </Button>
                              <Button variant="outline" onClick={() => setShowConfirm(false)} disabled={isResetting} size="sm">
                                Cancel
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          {activeTab === 'profile' && !loading && (
            <div className="flex justify-start py-3 border-t border-gray-200 bg-white">
              <Button onClick={handleSave} disabled={saving} loading={saving} icon={<Save className="w-4 h-4" />}>
                {saving ? 'Updating...' : 'Update'}
              </Button>
            </div>
          )}
        </div>
      </div>
    </StandardModal>
  );
}
