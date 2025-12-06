/**
 * Vite Configuration - SDLC Orchestrator Frontend
 * Version: 1.2.0 (Sprint 31 Day 2 - Gate G3 Performance)
 *
 * Bundle Optimization Strategy:
 * 1. Route-based code splitting (React.lazy in App.tsx)
 * 2. Vendor chunking (separate large libraries)
 * 3. Tree shaking (ES modules, sideEffects: false)
 * 4. Minification with esbuild (fastest)
 * 5. CSS code splitting
 *
 * Performance Targets (Gate G3):
 * - Initial bundle: <300KB (gzipped)
 * - Dashboard load: <1s
 * - LCP: <2.5s
 * - FCP: <1s
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      // Enable React Fast Refresh for better DX
      fastRefresh: true,
    }),
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/lib': path.resolve(__dirname, './src/lib'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/types': path.resolve(__dirname, './src/types'),
      '@/contexts': path.resolve(__dirname, './src/contexts'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/api': path.resolve(__dirname, './src/api'),
      '@/pages': path.resolve(__dirname, './src/pages'),
      '@/assets': path.resolve(__dirname, './src/assets'),
    },
  },

  server: {
    // Port configurable via VITE_DEV_PORT env var (default: 3000)
    port: parseInt(process.env.VITE_DEV_PORT || '3000'),
    proxy: {
      '/api': {
        // Backend URL configurable via VITE_API_URL env var (default: http://localhost:8000)
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
    // Target modern browsers for smaller bundles
    target: 'es2020',
    // Increase warning limit since we have proper chunking now
    chunkSizeWarningLimit: 300,
    // Enable CSS code splitting
    cssCodeSplit: true,
    // Minification settings
    minify: 'esbuild',
    rollupOptions: {
      output: {
        // Optimized manual chunks strategy
        manualChunks: (id) => {
          // React core bundle (loaded first)
          if (id.includes('node_modules/react/') ||
              id.includes('node_modules/react-dom/') ||
              id.includes('node_modules/react-router-dom/') ||
              id.includes('node_modules/scheduler/')) {
            return 'react-vendor'
          }

          // TanStack Query (data fetching)
          if (id.includes('@tanstack/react-query')) {
            return 'query-vendor'
          }

          // Radix UI components (lazy-loadable UI)
          if (id.includes('@radix-ui/')) {
            return 'radix-vendor'
          }

          // Charts library (only needed on Dashboard/Compliance pages)
          if (id.includes('recharts') || id.includes('d3-')) {
            return 'charts-vendor'
          }

          // Date utilities
          if (id.includes('date-fns')) {
            return 'date-vendor'
          }

          // Icons (tree-shaken but still significant)
          if (id.includes('lucide-react')) {
            return 'icons-vendor'
          }

          // Form handling
          if (id.includes('react-hook-form') ||
              id.includes('@hookform/') ||
              id.includes('zod')) {
            return 'form-vendor'
          }

          // Utility libraries
          if (id.includes('clsx') ||
              id.includes('tailwind-merge') ||
              id.includes('class-variance-authority')) {
            return 'utils-vendor'
          }
        },
      },
    },
  },

  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', '@tanstack/react-query'],
  },
})
