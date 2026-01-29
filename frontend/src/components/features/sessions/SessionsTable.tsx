import { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/primitives/table';
import { Input } from '@/components/ui/primitives/input';
import { StatusBadge } from '@/ui';
import { Avatar } from '@/ui';
import { type AgentInstance, type Agent } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/styles/design-system';
import { STATUS_ICONS, getStatusColor } from '@/constants/components';
import { Settings } from 'lucide-react';

interface SessionsTableProps {
  sessions: AgentInstance[];
  agents: Agent[];
  onSessionSelect: (session: AgentInstance) => void;
  fileBasedAgents?: Agent[];
}

const columnHelper = createColumnHelper<AgentInstance>();

export function SessionsTable({ sessions, agents, onSessionSelect, fileBasedAgents }: SessionsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'updated_at', desc: true }, // Default sort by last activity
  ]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const columns = useMemo(() => [
    columnHelper.accessor(
      (row) => row.current_session_description ||
               row.context?.description ||
               row.context?.task_description ||
               'New Session',
      {
        id: 'description',
        size: 400,
        minSize: 200,
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="text-left font-medium text-sm text-gray-700 hover:text-gray-900"
          >
            Description
          </button>
        ),
        cell: ({ row }) => {
          const session = row.original;
          const description = session.current_session_description ||
                            session.context?.description ||
                            session.context?.task_description ||
                            'New Session';

          return (
            <div className="text-sm text-gray-900 truncate">
              {description}
            </div>
          );
        },
      }
    ),
    columnHelper.accessor('agent_id', {
      id: 'pic',
      size: 200,
      minSize: 150,
      header: ({ column }) => (
        <button
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="text-left font-medium text-sm text-gray-700 hover:text-gray-900"
        >
          PIC
        </button>
      ),
      cell: ({ row }) => {
        const session = row.original;
        const agent = agents.find(a => a.id === session.agent_id) ||
                      fileBasedAgents?.find(a => a.id === session.agent_id);

        return (
          <div className="flex items-center gap-2 min-w-0">
            <Avatar
              seed={agent?.name || session.agent_id || 'Unknown'}
              size={24}
              className="w-6 h-6 flex-shrink-0"
              color={agent?.icon_color || '#4A90E2'}
            />
            <span className="text-sm text-gray-700 truncate">
              {agent?.name || session.agent_id || 'Unknown'}
            </span>
          </div>
        );
      },
    }),
    columnHelper.accessor('status', {
      id: 'status',
      size: 120,
      minSize: 100,
      header: ({ column }) => (
        <button
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="text-left font-medium text-sm text-gray-700 hover:text-gray-900"
        >
          Status
        </button>
      ),
      cell: ({ row }) => {
        const status = row.original.status;
        const StatusIcon = STATUS_ICONS[status] || Settings;
        const statusColor = getStatusColor(status);
        return (
          <StatusBadge
            status={status}
            color={statusColor}
            icon={StatusIcon}
            showIcon={false}
            align="left"
          />
        );
      },
    }),
    columnHelper.accessor('created_at', {
      id: 'created_at',
      size: 150,
      minSize: 120,
      header: ({ column }) => (
        <button
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="text-left font-medium text-sm text-gray-700 hover:text-gray-900"
        >
          Created
        </button>
      ),
      cell: ({ row }) => {
        const createdAt = row.original.created_at;
        if (!createdAt) {
          return <span className="text-sm text-gray-400">-</span>;
        }
        try {
          const date = new Date(createdAt);
          return (
            <span className="text-sm text-gray-600 whitespace-nowrap" title={date.toLocaleString()}>
              {formatDistanceToNow(date, { addSuffix: true })}
            </span>
          );
        } catch {
          return <span className="text-sm text-gray-400">-</span>;
        }
      },
    }),
    columnHelper.accessor('updated_at', {
      id: 'updated_at',
      size: 150,
      minSize: 120,
      header: ({ column }) => (
        <button
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="text-left font-medium text-sm text-gray-700 hover:text-gray-900"
        >
          Last Activity
        </button>
      ),
      cell: ({ row }) => {
        const updatedAt = row.original.updated_at;
        if (!updatedAt) {
          return <span className="text-sm text-gray-400">-</span>;
        }
        try {
          const date = new Date(updatedAt);
          return (
            <span className="text-sm text-gray-600 whitespace-nowrap" title={date.toLocaleString()}>
              {formatDistanceToNow(date, { addSuffix: true })}
            </span>
          );
        } catch {
          return <span className="text-sm text-gray-400">-</span>;
        }
      },
    }),
  ], [agents, fileBasedAgents]);

  const table = useReactTable({
    data: sessions,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
  });

  return (
    <div className="flex flex-col h-full">
      {/* Table Card */}
      <div className="flex-1 flex flex-col bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {/* Table */}
        <div className="flex-1 overflow-auto">
          <table className="w-full caption-bottom text-sm table-fixed">
            <TableHeader className="bg-gray-50 border-b border-gray-200">
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id} className="hover:bg-gray-50">
                  {headerGroup.headers.map((header) => (
                    <TableHead
                      key={header.id}
                      className="font-semibold text-gray-900"
                      style={{ width: `${header.getSize()}px` }}
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && 'selected'}
                    onClick={() => onSessionSelect(row.original)}
                    className={cn(
                      "cursor-pointer transition-colors",
                      "hover:bg-muted/50"
                    )}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <TableCell
                        key={cell.id}
                        style={{ width: `${cell.column.getSize()}px` }}
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-24 text-center"
                  >
                    <div className="text-gray-500">
                      <p className="type-body-sm">No sessions found</p>
                      <p className="type-caption text-gray-400 mt-1">
                        Create a new session to get started
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </table>
        </div>

        {/* Footer with search and count */}
        <div className="px-6 py-3 border-t border-gray-200 flex items-center justify-between gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search sessions..."
              value={globalFilter ?? ''}
              onChange={(e) => setGlobalFilter(e.target.value)}
              className="max-w-sm"
            />
          </div>
          <div className="text-sm text-gray-600 whitespace-nowrap">
            {table.getFilteredRowModel().rows.length} session(s)
          </div>
        </div>
      </div>
    </div>
  );
}
