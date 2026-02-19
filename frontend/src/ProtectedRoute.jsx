import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import api from './api';

/**
 * Protected Route Component
 * Guards routes that require authentication by checking TokenManager
 * Redirects to login if user is not authenticated
 */
export default function ProtectedRoute() {
  const location = useLocation();
  
  // Use api.isAuthenticated() which checks for valid tokens in TokenManager
  // (ssa_access_token in sessionStorage AND ssa_refresh_token in localStorage)
  if (!api.isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  
  return <Outlet />;
}
