import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'sonner'
import { ThemeProvider } from '@/lib/theme'
import './index.css'
import App from './App.tsx'
import PublicDashboard from './pages/PublicDashboard.tsx'
import SandboxPage from './pages/SandboxPage.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<App />}>
            <Route index element={<PublicDashboard />} />
            <Route path="sandbox" element={<SandboxPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
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
