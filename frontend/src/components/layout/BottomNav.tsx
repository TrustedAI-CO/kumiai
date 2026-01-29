import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { useMemo } from 'react';
import { Layout, Users, Boxes } from 'lucide-react';
import { cn } from '@/lib/utils';
import { layout } from '@/styles/design-system';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  isWorkspace?: boolean;
}

export function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Get current project ID from URL or localStorage
  const currentProjectId = useMemo(() => {
    const urlProject = searchParams.get('project');
    if (urlProject) return urlProject;

    try {
      return localStorage.getItem('currentProjectId');
    } catch (error) {
      return null;
    }
  }, [searchParams]);

  const navItems: NavItem[] = [
    {
      path: currentProjectId ? `/?project=${currentProjectId}` : '/',
      label: 'Workspace',
      icon: Layout,
      isWorkspace: true
    },
    { path: '/agents', label: 'Agents', icon: Users },
    { path: '/skills', label: 'Skills', icon: Boxes },
  ];

  const isActive = (item: NavItem) => {
    // For Workspace, check if we're on the root path
    if (item.isWorkspace) {
      return location.pathname === '/';
    }
    // Extract the pathname from item.path (remove query params)
    const itemPathname = item.path.split('?')[0];
    return location.pathname === itemPathname || location.pathname.startsWith(itemPathname + '/');
  };

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 lg:hidden z-50 safe-area-inset-bottom"
      style={{ height: layout.mobile.bottomNavHeight }}
    >
      <div className="flex items-center justify-around h-full px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item);

          return (
            <button
              key={item.label}
              onClick={() => navigate(item.path)}
              className={cn(
                'flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg transition-all',
                'min-w-[60px] min-h-[44px]', // Touch target
                active
                  ? 'text-primary'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              )}
              aria-label={item.label}
              aria-current={active ? 'page' : undefined}
            >
              <Icon className={cn('w-5 h-5', active && 'stroke-[2.5]')} />
              <span className={cn('type-caption font-medium', active && 'font-semibold')}>
                {item.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
