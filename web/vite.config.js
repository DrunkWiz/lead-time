import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// /api goes to scripts/dev_server.py locally; on Vercel it's the Python function.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8787' } },
})
