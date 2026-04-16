/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Chat } from './components/Chat';
import { Sidebar } from './components/Sidebar';
import { Artifacts } from './components/Artifacts';
import { Admin } from './components/Admin';
import { Login } from './components/Login';
import { User } from './types';

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    // Call through Express proxy (same origin) so cookies are consistent
    fetch('/api/auth/me', { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (cancelled) return;
        if (data && data.id) {
          setUser(data);
        }
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        // Backend unreachable - show login page instead of crashing
        setLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  const handleLogin = useCallback(() => {
    // Go through Express proxy at same origin to keep cookies consistent
    window.location.href = '/api/auth/login';
  }, []);

  const handleLogout = async () => {
    try {
      const res = await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
      const data = await res.json();
      setUser(null);
      if (data.logoutUrl) {
        window.location.href = data.logoutUrl;
      } else {
        // Show login page after logout
        setLoading(false);
      }
    } catch (error) {
      console.error('Logout failed:', error);
      setUser(null);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Router>
      <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
        <Sidebar user={user} onLogout={handleLogout} />
        <main className="flex-1 relative overflow-hidden">
          <Routes>
            <Route path="/" element={<Chat user={user} />} />
            <Route path="/chat/:conversationId" element={<Chat user={user} />} />
            <Route path="/artifacts" element={<Artifacts />} />
            <Route
              path="/admin"
              element={user.role === 'SUPER_ADMIN' ? <Admin /> : <Navigate to="/" />}
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
