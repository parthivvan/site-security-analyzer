import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import App from './SiteSecurityAnalyzer.jsx'
import Login from './Login.jsx'
import Signup from './Signup.jsx'
import ForgotPassword from './ForgotPassword.jsx'
import ResetPassword from './ResetPassword.jsx'
import Landing from './Landing.jsx'
import History from './History.jsx'
import Learn from './Learn.jsx'
import Layout from './Layout.jsx'
import ProtectedRoute from './ProtectedRoute.jsx'
import { DarkModeProvider } from './DarkModeContext.jsx'
import NotFound from './NotFound.jsx'
import LoginDebug from './LoginDebug.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <DarkModeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/learn" element={<Learn />} />
            <Route path="/debug-login" element={<LoginDebug />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/analyze" element={<App />} />
              <Route path="/history" element={<History />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </DarkModeProvider>
  </StrictMode>,
)
