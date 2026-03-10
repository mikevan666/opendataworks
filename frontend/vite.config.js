import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    css: true
  },
  server: {
    port: 3000,
    proxy: {
      '/api/v1/dataagent': {
        target: 'http://localhost:8900',
        changeOrigin: true
      },
      '/api/v1/nl2sql': {
        target: 'http://localhost:8900',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})
