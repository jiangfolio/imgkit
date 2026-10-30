import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import { resolve } from 'node:path'

const rootDir = import.meta.dirname

// 构建产物直接输出到 FastAPI 静态目录，单进程即可托管
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8787',
    },
  },
  build: {
    outDir: resolve(rootDir, '../app/static'),
    emptyOutDir: true,
  },
})
