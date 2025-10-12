import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './SiteSecurityAnalyzer.css'
import App from './SiteSecurityAnalyzer.jsx'
import Landing from './Landing.jsx'
import Login from './Login.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing/>} />
        <Route path="/login" element={<Login/>} />
        <Route path="/analyze" element={<App/>} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
