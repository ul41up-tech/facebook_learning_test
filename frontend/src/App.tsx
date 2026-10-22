import { useEffect } from 'react'
import type { ReactNode } from 'react'
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { TopBar } from './components/TopBar'
import { SidebarLeft } from './components/SidebarLeft'
import { SidebarRight } from './components/SidebarRight'
import { FeedPage } from './pages/FeedPage'
import { LoginPage } from './pages/LoginPage'
import { VerifyPage } from './pages/VerifyPage'
import { NotFoundPage } from './pages/NotFoundPage'

function FullPageSpinner() {
  return (
    <div className="page-loading">
      <span className="spinner spinner-lg" aria-hidden="true" />
      <p className="auth-text">載入中…</p>
    </div>
  )
}

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageSpinner />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <>{children}</>
}

function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <FullPageSpinner />
  if (user) return <Navigate to="/" replace />
  return <>{children}</>
}

function AppLayout() {
  return (
    <div className="app-shell">
      <TopBar />
      <div className="layout">
        <SidebarLeft />
        <main className="layout-center">
          <FeedPage />
        </main>
        <SidebarRight />
      </div>
    </div>
  )
}

function LoginRoute() {
  return (
    <RedirectIfAuthed>
      <LoginPage />
    </RedirectIfAuthed>
  )
}

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ScrollToTop />
        <Routes>
          <Route
            path="/"
            element={
              <Protected>
                <AppLayout />
              </Protected>
            }
          />
          <Route path="/login" element={<LoginRoute />} />
          <Route path="/verify" element={<VerifyPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
