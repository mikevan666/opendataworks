import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import ElementPlus from 'unplugin-element-plus/vite'

export default defineConfig(() => {
  const isTest = process.env.VITEST === 'true'

  const manualChunks = (id) => {
    if (!id.includes('node_modules')) return
    if (id.includes('element-plus') || id.includes('@element-plus')) return 'element-plus'
    if (id.includes('echarts')) return 'charts'
    if (id.includes('@codemirror') || id.includes('codemirror')) return 'codemirror'
    if (id.includes('marked') || id.includes('markdown-it') || id.includes('highlight.js')) return 'markdown'
    if (id.includes('lucide-vue-next')) return 'icons'
    if (id.includes('vue') || id.includes('vue-router') || id.includes('pinia') || id.includes('@vue')) return 'vue-core'
    return 'vendor'
  }

  return {
    plugins: [
      tailwindcss(),
      vue(),
      Components({
        dirs: [],
        dts: false,
        resolvers: [
          ElementPlusResolver({
            importStyle: isTest ? false : 'css',
            directives: true
          })
        ]
      }),
      !isTest && ElementPlus()
    ].filter(Boolean),
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    server: {
      port: 3010,
      proxy: {
        '/api': {
          target: 'http://localhost:18900',
          changeOrigin: true
        }
      }
    },
    test: {
      environment: 'jsdom',
      globals: true,
      css: true
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks
        }
      }
    }
  }
})
