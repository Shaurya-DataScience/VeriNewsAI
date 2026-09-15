import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: 'frontend',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    minify: 'terser',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'frontend/index.html')
      }
    }
  },
  server: {
    port: 3000,
    open: true
  }
});
