import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    // 本地运行
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      // 交通分析API转发到Django
      '/api/traffic_analysis': {
        target: 'http://10.61.169.63:9000',
        changeOrigin: true,
        secure: false
      },
      // 其他API转发到Flask
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
