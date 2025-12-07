import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './', // Important for Electron to load assets
  server: {
    port: 11242,
    strictPort: true, // 如果端口被占用则报错，不自动切换
  },
})
