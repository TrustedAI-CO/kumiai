/**
 * Design System - Unified styling for the Multi-Agent System
 * Inspired by: Anthropic, OpenAI, Google, Apple
 *
 * Philosophy: Clean, Minimal, Functional
 */

// ============================================================================
// COLOR PALETTE
// ============================================================================
// Note: This project uses shadcn/ui's default color system with CSS variables.
// Colors are defined in src/index.css and referenced via Tailwind classes.
// Available colors: background, foreground, primary, secondary, muted, accent,
// destructive, border, input, ring, card, popover.
// Each color has a DEFAULT and foreground variant (e.g., primary, primary-foreground).
// ============================================================================

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  fontFamily: {
    sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    mono: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, Consolas, monospace',
  },

  fontSize: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '1rem',       // 16px
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '1.875rem',  // 30px
    '4xl': '2.25rem',   // 36px
  },

  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },

  lineHeight: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  },
};

// ============================================================================
// SPACING
// ============================================================================

export const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
};

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const radius = {
  none: '0',
  sm: '0.25rem',    // 4px
  base: '0.5rem',   // 8px
  md: '0.75rem',    // 12px
  lg: '1rem',       // 16px
  xl: '1.5rem',     // 24px
  full: '9999px',
};

// ============================================================================
// BORDER WIDTH
// ============================================================================

export const borderWidth = {
  0: '0',
  1: '1px',
  2: '2px',
  4: '4px',
  8: '8px',
  default: '1px',
};

// ============================================================================
// SHADOWS
// ============================================================================

export const shadows = {
  none: 'none',
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  base: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
};

// ============================================================================
// TRANSITIONS
// ============================================================================

export const transitions = {
  fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  base: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
};

// ============================================================================
// LAYOUT
// ============================================================================

export const breakpoints = {
  sm: 640,   // Small devices (mobile landscape)
  md: 768,   // Medium devices (tablets)
  lg: 1024,  // Large devices (desktop)
  xl: 1280,  // Extra large devices
  '2xl': 1536, // 2X Extra large devices
};

export const layout = {
  // Sidebar widths (responsive)
  sidebar: {
    desktop: '20%',      // >= lg breakpoint
    tablet: '30%',       // md to lg
    mobile: '100%',      // < md (overlay mode)
  },

  // PM Chat panel
  pmChat: {
    desktop: '400px',    // >= lg breakpoint
    mobile: '100%',      // < lg (full-screen overlay)
  },

  // Mobile-specific
  mobile: {
    bottomNavHeight: '64px',
    headerHeight: '56px',
    touchTarget: '44px',  // Minimum touch target size
    drawerMaxWidth: '85vw', // Mobile drawer max width
  },

  // Desktop-specific
  desktop: {
    headerHeight: '64px',
    sidebarMinWidth: '240px',
    sidebarMaxWidth: '400px',
  },

  // Legacy (for backward compatibility during migration)
  sidebarWidth: '20%',
};

// ============================================================================
// COMPONENT STYLES (Class Names)
// ============================================================================

export const components = {
  // Buttons
  button: {
    base: 'inline-flex items-center justify-center font-medium transition-all rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2',

    variants: {
      primary: 'bg-background border-2 border-primary text-primary hover:bg-muted focus:ring-ring',
      secondary: 'bg-background border-2 border-border text-foreground hover:bg-muted focus:ring-ring',
      outline: 'border-2 border-border bg-background text-foreground hover:bg-muted focus:ring-ring',
      ghost: 'text-foreground hover:bg-muted focus:ring-ring',
      danger: 'bg-background border-2 border-destructive text-destructive hover:bg-destructive/10 focus:ring-destructive',
    },

    sizes: {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg',
    },
  },

  // Input fields
  input: {
    base: 'w-full rounded-lg border transition-all focus:outline-none focus:ring-2 focus:ring-ring focus:border-input',
    default: 'bg-background border-border text-foreground placeholder-muted-foreground',
    disabled: 'bg-muted border-border text-muted-foreground cursor-not-allowed',

    sizes: {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-4 py-3 text-lg',
    },
  },

  // Cards
  card: {
    base: 'bg-card rounded-lg border border-border',
    hover: 'hover:border-border/80 hover:shadow-sm transition-all',
    interactive: 'cursor-pointer hover:border-border/80 hover:shadow-md transition-all',
    padding: {
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    },
  },

  // Navigation
  nav: {
    item: {
      base: 'flex items-center gap-2 px-3 py-2 font-medium transition-all',
      active: 'bg-accent text-accent-foreground',
      inactive: 'text-muted-foreground hover:bg-muted hover:text-foreground',
    },
  },

  // Headers
  header: {
    page: 'bg-background border-b border-border px-6 py-4',
    title: 'text-2xl font-semibold text-foreground',
    subtitle: 'text-sm text-muted-foreground mt-1',
  },

  // Badges/Tags
  badge: {
    base: 'inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium',
    variants: {
      primary: 'bg-primary/10 text-primary',
      secondary: 'bg-secondary text-secondary-foreground',
      success: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      error: 'bg-destructive/10 text-destructive',
    },
  },

  // List items
  listItem: {
    base: 'p-4 cursor-pointer transition-all',
    hover: 'hover:bg-muted',
    selected: 'bg-accent border-l-4 border-primary',
    divider: 'border-b border-border',
  },
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export const cn = (...classes: (string | undefined | null | false)[]) => {
  return classes.filter(Boolean).join(' ');
};

export const getButtonClass = (
  variant: keyof typeof components.button.variants = 'primary',
  size: keyof typeof components.button.sizes = 'md'
) => {
  return cn(
    components.button.base,
    components.button.variants[variant],
    components.button.sizes[size]
  );
};

export const getInputClass = (
  size: keyof typeof components.input.sizes = 'md',
  disabled = false
) => {
  return cn(
    components.input.base,
    disabled ? components.input.disabled : components.input.default,
    components.input.sizes[size]
  );
};

export const getCardClass = (interactive = false, padding: keyof typeof components.card.padding = 'md') => {
  return cn(
    components.card.base,
    interactive ? components.card.interactive : components.card.hover,
    components.card.padding[padding]
  );
};
