import { useState, useEffect } from 'react';
import { Settings, HelpCircle } from 'lucide-react';
import { Avatar } from '@/ui';
import { PreferencesModal } from '@/components/modals/PreferencesModal';
import { api, UserProfile } from '@/lib/api';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/primitives/tooltip';

export function SidebarFooter() {
  const [showPreferencesModal, setShowPreferencesModal] = useState(false);
  const [initialTab, setInitialTab] = useState<'profile' | 'settings'>('profile');
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await api.getUserProfile();
      setProfile(data);
    } catch (error) {
      console.error('Failed to load user profile:', error);
    }
  };

  return (
    <>
      <div className="border-t border-border bg-white">
        <TooltipProvider>
          <div className="flex items-center justify-around px-2 py-1">
            {/* Help Icon */}
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={() => window.open('https://docs.kumiai.com', '_blank')}
                  className="p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
                  aria-label="Help"
                >
                  <HelpCircle className="w-5 h-5" />
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Help</p>
              </TooltipContent>
            </Tooltip>

            {/* Settings Icon */}
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={() => {
                    setInitialTab('settings');
                    setShowPreferencesModal(true);
                  }}
                  className="p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
                  aria-label="Settings"
                >
                  <Settings className="w-5 h-5" />
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Settings</p>
              </TooltipContent>
            </Tooltip>

            {/* User Avatar Icon */}
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={() => {
                    setInitialTab('profile');
                    setShowPreferencesModal(true);
                  }}
                  className="p-2 rounded-lg hover:bg-gray-50 transition-colors"
                  aria-label="Open profile"
                >
                  <div className="w-5 h-5">
                    <Avatar
                      seed={profile?.avatar || 'default-user'}
                      size={20}
                    />
                  </div>
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Profile</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </TooltipProvider>
      </div>

      {/* Preferences Modal */}
      <PreferencesModal
        isOpen={showPreferencesModal}
        onClose={() => {
          setShowPreferencesModal(false);
          loadProfile();
        }}
        initialTab={initialTab}
      />
    </>
  );
}
