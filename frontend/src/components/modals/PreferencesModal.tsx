import { useState, useEffect } from 'react';
import { api, UserProfile as UserProfileType, CredentialsConfigResponse } from '@/lib/api';
import { User, Save, Upload, X, Settings, AlertTriangle, Key, Cloud, Check } from 'lucide-react';
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

  // Credentials state
  const [credConfig, setCredConfig] = useState<CredentialsConfigResponse | null>(null);
  const [credProvider, setCredProvider] = useState<'anthropic' | 'bedrock'>('anthropic');
  const [anthropicApiKey, setAnthropicApiKey] = useState('');
  const [awsCredentialsText, setAwsCredentialsText] = useState('');
  const [awsAccessKeyId, setAwsAccessKeyId] = useState('');
  const [awsSecretAccessKey, setAwsSecretAccessKey] = useState('');
  const [awsSessionToken, setAwsSessionToken] = useState('');
  const [awsRegion, setAwsRegion] = useState('us-east-1');
  const [credSaving, setCredSaving] = useState(false);
  const [credSaveSuccess, setCredSaveSuccess] = useState(false);
  const [credParseError, setCredParseError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadProfile();
      loadCredentials();
      setActiveTab(initialTab);
    }
  }, [isOpen, initialTab]);

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
      const prefsText = data.preferences ? JSON.stringify(data.preferences, null, 2) : '';
      setPreferencesText(prefsText);
    } catch (error) {
      console.error('Failed to load user profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCredentials = async () => {
    try {
      const data = await api.getCredentialsConfig();
      setCredConfig(data);
      setCredProvider(data.provider as 'anthropic' | 'bedrock');
      setAwsRegion(data.aws_region || 'us-east-1');
    } catch (error) {
      console.error('Failed to load credentials config:', error);
    }
  };

  const parseAwsCredentialsBlock = (text: string) => {
    setAwsCredentialsText(text);
    setCredParseError('');

    const lines = text.trim().split('\n');
    const result: Record<string, string> = {};

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('[') && trimmed.endsWith(']')) continue;
      if (!trimmed || trimmed.startsWith('#')) continue;

      const eqIndex = trimmed.indexOf('=');
      if (eqIndex === -1) continue;

      const key = trimmed.substring(0, eqIndex).trim();
      const value = trimmed.substring(eqIndex + 1).trim();
      result[key] = value;
    }

    if (result.aws_access_key_id) {
      setAwsAccessKeyId(result.aws_access_key_id);
    }
    if (result.aws_secret_access_key) {
      setAwsSecretAccessKey(result.aws_secret_access_key);
    }
    if (result.aws_session_token) {
      setAwsSessionToken(result.aws_session_token);
    }

    if (text.trim() && !result.aws_access_key_id && !result.aws_secret_access_key) {
      setCredParseError('Could not parse credentials. Expected aws_access_key_id and aws_secret_access_key.');
    }
  };

  const handleSaveCredentials = async () => {
    try {
      setCredSaving(true);
      setCredSaveSuccess(false);

      const req: any = { provider: credProvider };

      if (credProvider === 'anthropic' && anthropicApiKey) {
        req.anthropic_api_key = anthropicApiKey;
      }

      if (credProvider === 'bedrock') {
        if (!awsAccessKeyId || !awsSecretAccessKey) {
          alert('AWS Access Key ID and Secret Access Key are required for Bedrock.');
          setCredSaving(false);
          return;
        }
        req.aws_credentials = {
          aws_access_key_id: awsAccessKeyId,
          aws_secret_access_key: awsSecretAccessKey,
          aws_session_token: awsSessionToken || undefined,
          aws_region: awsRegion,
        };
      }

      const result = await api.saveCredentialsConfig(req);
      setCredConfig(result);
      setCredSaveSuccess(true);
      setTimeout(() => setCredSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save credentials:', error);
      alert('Failed to save credentials configuration.');
    } finally {
      setCredSaving(false);
    }
  };

  const handleClearCredentials = async () => {
    if (!confirm('Clear all stored credentials?')) return;
    try {
      await api.clearCredentials();
      setAnthropicApiKey('');
      setAwsAccessKeyId('');
      setAwsSecretAccessKey('');
      setAwsSessionToken('');
      setAwsCredentialsText('');
      setCredProvider('anthropic');
      await loadCredentials();
    } catch (error) {
      console.error('Failed to clear credentials:', error);
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
        const base64 = reader.result as string;
        setFormData({ ...formData, avatar: base64 });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await api.resetApp();
      alert('App reset successfully. Reloading...');

      // Clear localStorage
      localStorage.clear();

      // Reload the page after a short delay
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
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
        {/* Left Sidebar - Tabs */}
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
                    activeTab === tab.id
                      ? 'bg-gray-200 text-gray-900'
                      : 'text-gray-700 hover:bg-gray-100'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right Content Area */}
        <div className="flex-1 flex flex-col bg-white px-6">
          {/* Header */}
          <div className="flex items-center justify-between py-3 border-b border-gray-200">
            <h3 className="text-base font-semibold text-gray-900">
              {activeTab === 'profile' ? 'User Profile' : 'Settings'}
            </h3>
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto py-4">
            {loading ? (
              <LoadingState message="Loading..." />
            ) : (
              <>
                {activeTab === 'profile' && (
                  <div className="space-y-4">
                    {/* Avatar Section */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Avatar
                      </label>
                      <div className="flex items-center gap-3">
                        {formData.avatar ? (
                          <img
                            src={formData.avatar}
                            alt="Avatar"
                            className="w-16 h-16 rounded-full object-cover border-2 border-gray-200"
                          />
                        ) : (
                          <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center">
                            <User className="w-8 h-8 text-gray-400" />
                          </div>
                        )}
                        <div>
                          <label className="cursor-pointer">
                            <div className={cn(components.button.base, components.button.variants.secondary, "inline-flex items-center gap-1.5 text-sm")}>
                              <Upload className="w-3.5 h-3.5" />
                              Upload
                            </div>
                            <input
                              type="file"
                              accept="image/*"
                              onChange={handleAvatarChange}
                              className="hidden"
                            />
                          </label>
                          <p className="text-xs text-gray-500 mt-1.5">
                            JPG, PNG, or GIF. Max 2MB.
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Description Section */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Description
                      </label>
                      <Textarea
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        placeholder="Tell about yourself: who you are, what you do, your background, etc."
                        rows={3}
                        className="resize-none text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        This will be included in the AI's system prompt.
                      </p>
                    </div>

                    {/* Preferences Section */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Preferences (JSON)
                      </label>
                      <Textarea
                        value={preferencesText}
                        onChange={(e) => setPreferencesText(e.target.value)}
                        placeholder='{"communicationStyle": "concise", "tone": "casual"}'
                        className="font-mono text-xs resize-none"
                        rows={4}
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        JSON format preferences for AI interactions.
                      </p>
                    </div>
                  </div>
                )}

                {activeTab === 'settings' && (
                  <div className="space-y-6">
                    {/* API Configuration Section */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <Key className="w-4 h-4" />
                        API Configuration
                      </h4>

                      {/* Provider Toggle */}
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Provider
                        </label>
                        <div className="flex gap-2">
                          <button
                            onClick={() => setCredProvider('anthropic')}
                            className={cn(
                              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border transition-colors',
                              credProvider === 'anthropic'
                                ? 'bg-gray-900 text-white border-gray-900'
                                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                            )}
                          >
                            <Key className="w-3.5 h-3.5" />
                            Anthropic Direct
                          </button>
                          <button
                            onClick={() => setCredProvider('bedrock')}
                            className={cn(
                              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border transition-colors',
                              credProvider === 'bedrock'
                                ? 'bg-gray-900 text-white border-gray-900'
                                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                            )}
                          >
                            <Cloud className="w-3.5 h-3.5" />
                            AWS Bedrock
                          </button>
                        </div>
                      </div>

                      {/* Anthropic Direct Fields */}
                      {credProvider === 'anthropic' && (
                        <div className="space-y-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Anthropic API Key
                            </label>
                            <input
                              type="password"
                              value={anthropicApiKey}
                              onChange={(e) => setAnthropicApiKey(e.target.value)}
                              placeholder={credConfig?.anthropic_api_key_masked || 'sk-ant-...'}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                              Leave empty to use the ANTHROPIC_API_KEY environment variable.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* AWS Bedrock Fields */}
                      {credProvider === 'bedrock' && (
                        <div className="space-y-3">
                          {/* Paste Textarea */}
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Paste AWS Credentials
                            </label>
                            <Textarea
                              value={awsCredentialsText}
                              onChange={(e) => parseAwsCredentialsBlock(e.target.value)}
                              placeholder={'[profile_name]\naws_access_key_id=AKIA...\naws_secret_access_key=...\naws_session_token=...'}
                              className="font-mono text-xs resize-none"
                              rows={4}
                            />
                            {credParseError && (
                              <p className="text-xs text-red-500 mt-1">{credParseError}</p>
                            )}
                            <p className="text-xs text-gray-500 mt-1">
                              Paste your AWS credentials block. Fields below will be auto-filled.
                            </p>
                          </div>

                          {/* Individual Fields */}
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              AWS Access Key ID
                            </label>
                            <input
                              type="text"
                              value={awsAccessKeyId}
                              onChange={(e) => setAwsAccessKeyId(e.target.value)}
                              placeholder={credConfig?.aws_access_key_id_masked || 'AKIA...'}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              AWS Secret Access Key
                            </label>
                            <input
                              type="password"
                              value={awsSecretAccessKey}
                              onChange={(e) => setAwsSecretAccessKey(e.target.value)}
                              placeholder="Enter secret access key"
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              AWS Session Token <span className="text-gray-400">(optional)</span>
                            </label>
                            <input
                              type="password"
                              value={awsSessionToken}
                              onChange={(e) => setAwsSessionToken(e.target.value)}
                              placeholder="Enter session token"
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              AWS Region
                            </label>
                            <select
                              value={awsRegion}
                              onChange={(e) => setAwsRegion(e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent bg-white"
                            >
                              <option value="us-east-1">us-east-1 (N. Virginia)</option>
                              <option value="us-east-2">us-east-2 (Ohio)</option>
                              <option value="us-west-2">us-west-2 (Oregon)</option>
                              <option value="eu-west-1">eu-west-1 (Ireland)</option>
                              <option value="eu-west-2">eu-west-2 (London)</option>
                              <option value="eu-west-3">eu-west-3 (Paris)</option>
                              <option value="eu-central-1">eu-central-1 (Frankfurt)</option>
                              <option value="ap-southeast-1">ap-southeast-1 (Singapore)</option>
                              <option value="ap-southeast-2">ap-southeast-2 (Sydney)</option>
                              <option value="ap-northeast-1">ap-northeast-1 (Tokyo)</option>
                            </select>
                          </div>
                        </div>
                      )}

                      {/* Status and Actions */}
                      <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
                        <div className="flex items-center gap-2">
                          {credSaveSuccess ? (
                            <span className="flex items-center gap-1 text-sm text-green-600">
                              <Check className="w-4 h-4" />
                              Saved
                            </span>
                          ) : credConfig && (
                            <span className={cn(
                              'text-xs px-2 py-1 rounded-full',
                              (credConfig.provider === 'bedrock' && credConfig.aws_configured) ||
                              (credConfig.provider === 'anthropic' && credConfig.anthropic_configured)
                                ? 'bg-green-100 text-green-700'
                                : 'bg-gray-100 text-gray-600'
                            )}>
                              {(credConfig.provider === 'bedrock' && credConfig.aws_configured) ||
                               (credConfig.provider === 'anthropic' && credConfig.anthropic_configured)
                                ? 'Configured'
                                : 'Not configured'}
                            </span>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleClearCredentials}
                          >
                            Clear
                          </Button>
                          <Button
                            size="sm"
                            onClick={handleSaveCredentials}
                            disabled={credSaving}
                            loading={credSaving}
                          >
                            {credSaving ? 'Saving...' : 'Save Configuration'}
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Divider */}
                    <hr className="border-gray-200" />

                    {/* Reset Application Section */}
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
                            <h5 className="text-sm font-medium text-yellow-900 mb-1">
                              Warning
                            </h5>
                            <p className="text-sm text-yellow-800 mb-3">
                              This will reset the application and delete all data including:
                            </p>
                            <ul className="list-disc list-inside text-sm text-yellow-800 space-y-1 mb-3">
                              <li>Database (sessions, messages, etc.)</li>
                              <li>Skills</li>
                              <li>Agents</li>
                              <li>User settings</li>
                            </ul>
                            <p className="text-sm text-yellow-800 mb-4">
                              <strong>Projects will be preserved</strong> and will not be deleted.
                            </p>
                            <Button
                              variant="destructive"
                              onClick={() => setShowConfirm(true)}
                              size="sm"
                            >
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
                            <h5 className="text-sm font-medium text-red-900 mb-2">
                              Confirm Reset
                            </h5>
                            <p className="text-sm text-red-800 mb-4">
                              Are you absolutely sure you want to reset the application? This action cannot be undone.
                            </p>
                            <div className="flex gap-2">
                              <Button
                                variant="destructive"
                                onClick={handleReset}
                                disabled={isResetting}
                                size="sm"
                              >
                                {isResetting ? 'Resetting...' : 'Reset Application'}
                              </Button>
                              <Button
                                variant="outline"
                                onClick={() => setShowConfirm(false)}
                                disabled={isResetting}
                                size="sm"
                              >
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

          {/* Save Button - Sticky Footer */}
          {activeTab === 'profile' && !loading && (
            <div className="flex justify-start py-3 border-t border-gray-200 bg-white">
              <Button
                onClick={handleSave}
                disabled={saving}
                loading={saving}
                icon={<Save className="w-4 h-4" />}
              >
                {saving ? 'Updating...' : 'Update'}
              </Button>
            </div>
          )}
        </div>
      </div>
    </StandardModal>
  );
}
