import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const config = JSON.parse(readFileSync(resolve(__dirname, '../config.json'), 'utf-8'))

export default defineConfig({
  plugins: [vue()],
  server: {
    host: config.frontend.host,
    port: config.frontend.port,
    proxy: {
      '/api': {
        target: `http://localhost:${config.frontend.proxyPort}`,
        changeOrigin: true
      }
    }
  }
})
