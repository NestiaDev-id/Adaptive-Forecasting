import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'sonner'
import { ThemeProvider } from '@/lib/theme'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <App />
      <Toaster
        position="bottom-right"
        toastOptions={{
          className: "!bg-card !text-foreground !border-border",
        }}
        richColors
        closeButton
      />
    </ThemeProvider>
  </StrictMode>,
)
