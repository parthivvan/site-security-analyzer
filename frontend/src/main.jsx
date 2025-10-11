import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './SiteSecurityAnalyzer.css'
import App from './SiteSecurityAnalyzer.jsx'
import Landing from './Landing.jsx'
import Login from './Login.jsx'
import History from './History.jsx'
import Layout from './Layout.jsx'
import ProtectedRoute from './ProtectedRoute.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout/>}>
          <Route path="/" element={<Landing/>} />
          <Route path="/login" element={<Login/>} />
          <Route element={<ProtectedRoute/>}>
            <Route path="/analyze" element={<App/>} />
            <Route path="/history" element={<History/>} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
