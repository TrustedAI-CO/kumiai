/**
 * UI Components Library
 *
 * Reusable components following shadcn/ui design system
 */

// ========================================
// Re-export all primitives (shadcn/ui)
// ========================================
export * from './primitives';

// ========================================
// Re-export all composite components
// ========================================
export * from './composite';

// ========================================
// Legacy direct exports (for backward compatibility)
// TODO: Remove these once all imports updated to use @/ui
// ========================================
export { Button, buttonVariants } from './primitives/button';
export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent } from './primitives/card';
export { Input } from './primitives/input';
export { Label } from './primitives/label';
export { Textarea } from './primitives/textarea';
export { Badge, badgeVariants } from './primitives/badge';
export { Separator } from './primitives/separator';
export { Skeleton } from './primitives/skeleton';
export {
  Dialog,
  DialogPortal,
  DialogOverlay,
  DialogClose,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from './primitives/dialog';
export {
  Sheet,
  SheetPortal,
  SheetOverlay,
  SheetTrigger,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetFooter,
  SheetTitle,
  SheetDescription,
} from './primitives/sheet';
export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuGroup,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
} from './primitives/dropdown-menu';
export { ToggleGroup, ToggleGroupItem } from './primitives/toggle-group';
export {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from './primitives/tooltip';
export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
} from './primitives/table';

// Custom component type exports
export type { ModalSize } from './composite/StandardModal';
export type { Toast, ToastType, ToastPosition } from './composite/Toast';
