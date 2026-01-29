import { Home, Users as UsersIcon, Boxes } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';

export function SidebarNav() {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="border-b border-border bg-white">
      <div className="flex items-center justify-around px-2 py-1">
        {/* Home */}
        <button
          onClick={() => navigate('/')}
          className={cn(
            'flex flex-col items-center gap-1 p-2 rounded-lg transition-colors min-w-[60px]',
            isActive('/')
              ? 'bg-primary/10 text-primary'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
          )}
          aria-label="Workspace"
        >
          <Home className={cn('w-5 h-5', isActive('/') && 'stroke-[2.5]')} />
          <span className={cn('text-xs', isActive('/') ? 'font-semibold' : 'font-medium')}>Workspace</span>
        </button>

        {/* Agents */}
        <button
          onClick={() => navigate('/agents')}
          className={cn(
            'flex flex-col items-center gap-1 p-2 rounded-lg transition-colors min-w-[60px]',
            isActive('/agents')
              ? 'bg-primary/10 text-primary'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
          )}
          aria-label="Agents"
        >
          <UsersIcon className={cn('w-5 h-5', isActive('/agents') && 'stroke-[2.5]')} />
          <span className={cn('text-xs', isActive('/agents') ? 'font-semibold' : 'font-medium')}>Agents</span>
        </button>

        {/* Skills */}
        <button
          onClick={() => navigate('/skills')}
          className={cn(
            'flex flex-col items-center gap-1 p-2 rounded-lg transition-colors min-w-[60px]',
            isActive('/skills')
              ? 'bg-primary/10 text-primary'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
          )}
          aria-label="Skills"
        >
          <Boxes className={cn('w-5 h-5', isActive('/skills') && 'stroke-[2.5]')} />
          <span className={cn('text-xs', isActive('/skills') ? 'font-semibold' : 'font-medium')}>Skills</span>
        </button>
      </div>
    </div>
  );
}
