import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Specific aliases must come before general ones
      '@/features/projects': path.resolve(__dirname, './src/components/features/projects/index.ts'),
      '@/features/agents': path.resolve(__dirname, './src/components/features/agents/index.ts'),
      '@/features/chat': path.resolve(__dirname, './src/components/features/chat/index.ts'),
      '@/features/files': path.resolve(__dirname, './src/components/features/files/index.ts'),
      '@/features/kanban': path.resolve(__dirname, './src/components/features/kanban/index.ts'),
      '@/features/sessions': path.resolve(__dirname, './src/components/features/sessions/index.ts'),
      '@/features/skills': path.resolve(__dirname, './src/components/features/skills/index.ts'),
      '@/features': path.resolve(__dirname, './src/components/features'),
      '@/ui': path.resolve(__dirname, './src/components/ui'),
      '@/layout': path.resolve(__dirname, './src/components/layout'),
      '@/modals': path.resolve(__dirname, './src/components/modals'),
      '@/api': path.resolve(__dirname, './src/lib/api'),
      '@/services': path.resolve(__dirname, './src/lib/services'),
      '@/utils': path.resolve(__dirname, './src/lib/utils'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/lib': path.resolve(__dirname, './src/lib'),
      '@/stores': path.resolve(__dirname, './src/stores'),
      '@/types': path.resolve(__dirname, './src/types'),
      '@/styles': path.resolve(__dirname, './src/styles'),
      '@/constants': path.resolve(__dirname, './src/constants'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0', // Listen on all network interfaces
    port: 1420,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:7892',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
    },
  },
},
});
