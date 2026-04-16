import { useState, useEffect } from 'react';
import { NavLink, useNavigate, useParams } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Box, Settings, Bot, ChevronRight, LogOut, Languages, Palette, Plus, History } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Agent, User, Conversation } from '../types';
import { cn } from '../lib/utils';
import { API_BASE } from '../lib/api';

interface SidebarProps {
  user: User;
  onLogout: () => void;
}

export function Sidebar({ user, onLogout }: SidebarProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const { t, i18n } = useTranslation();
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'aegis');
  const navigate = useNavigate();
  const { conversationId } = useParams();

  useEffect(() => {
    fetch(`${API_BASE}/api/agents?sidebar=true`, { credentials: 'include' })
      .then(res => res.json())
      .then(setAgents);

    fetchConversations();
  }, []);

  const fetchConversations = () => {
    fetch(`${API_BASE}/api/conversations`, { credentials: 'include' })
      .then(res => res.json())
      .then(setConversations);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const createNewChat = async (agentId?: string) => {
    const res = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agentId })
    });
    const newConv = await res.json();
    setConversations(prev => [newConv, ...prev]);
    navigate(`/chat/${newConv.id}`);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const navItems = [
    { icon: MessageSquare, label: t('chat_console'), path: '/' },
    { icon: Box, label: t('artifact_repo'), path: '/artifacts' },
    ...(user.role === 'SUPER_ADMIN' ? [{ icon: Settings, label: t('admin_panel'), path: '/admin' }] : []),
  ];

  const toggleLanguage = () => {
    const nextLng = i18n.language === 'zh' ? 'en' : 'zh';
    i18n.changeLanguage(nextLng);
  };

  const toggleTheme = () => {
    setTheme(prev => prev === 'aegis' ? 'nexus' : 'aegis');
  };

  return (
    <aside className="w-[240px] bg-sidebar border-r border-border flex flex-col shrink-0">
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="p-6 font-bold text-primary text-lg border-b border-border flex items-center gap-2">
          <Bot className="w-6 h-6 text-accent" />
          {theme === 'aegis' ? t('aegis_ai') : t('nexus_ai')}
        </div>

        <nav className="p-3 space-y-1 overflow-y-auto">
          <button
            onClick={() => createNewChat()}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm bg-accent text-white font-bold hover:bg-blue-700 transition-all mb-4"
          >
            <Plus className="w-4 h-4" />
            {t('new_chat')}
          </button>

          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-all",
                isActive 
                  ? "bg-slate-200 text-primary font-semibold" 
                  : "text-text-muted hover:bg-slate-100 hover:text-primary"
              )}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          ))}

          <div className="mt-6 mb-2 px-3 text-[11px] font-bold text-text-muted uppercase tracking-wider flex items-center justify-between">
            <span>{t('history')}</span>
            <History className="w-3 h-3" />
          </div>
          <div className="space-y-1 max-h-[200px] overflow-y-auto">
            {conversations.map((conv) => (
              <NavLink
                key={conv.id}
                to={`/chat/${conv.id}`}
                className={({ isActive }) => cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-all group",
                  isActive 
                    ? "bg-slate-200 text-primary font-semibold" 
                    : "text-text-muted hover:bg-slate-100 hover:text-primary"
                )}
              >
                <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{conv.title}</span>
              </NavLink>
            ))}
          </div>

          <div className="mt-6 mb-2 px-3 text-[11px] font-bold text-text-muted uppercase tracking-wider">
            {t('my_agents')}
          </div>
          {agents.map((agent) => (
            <button
              key={agent.id}
              onClick={() => createNewChat(agent.id)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-md text-sm text-text-muted hover:bg-slate-100 hover:text-primary transition-all group"
            >
              <div className="flex items-center gap-3 truncate">
                <div className={cn(
                  "w-1.5 h-1.5 rounded-full shrink-0",
                  agent.status === 'ACTIVE' ? "bg-accent" : "bg-slate-300"
                )} />
                <span className="truncate">{agent.name}</span>
              </div>
              <Plus className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
          ))}
        </nav>
      </div>

      <div className="p-3 border-t border-border space-y-1">
        <button 
          onClick={toggleLanguage}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium text-text-muted hover:bg-slate-100 hover:text-primary transition-all"
        >
          <Languages className="w-4 h-4" />
          {t('language')}: {i18n.language === 'zh' ? '中文' : 'English'}
        </button>
        <button 
          onClick={toggleTheme}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium text-text-muted hover:bg-slate-100 hover:text-primary transition-all"
        >
          <Palette className="w-4 h-4" />
          {t('subject')}: {theme === 'aegis' ? 'Aegis' : 'Nexus'}
        </button>
      </div>

      <div className="p-4 border-t border-border flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-slate-300 border-2 border-white shrink-0 flex items-center justify-center text-xs font-bold text-slate-600">
          {user.username[0].toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[13px] font-bold text-primary truncate leading-tight">{user.username}</p>
          <p className="text-[11px] text-text-muted truncate">{t('verified_via')}</p>
        </div>
        <button 
          onClick={onLogout}
          className="p-1.5 hover:bg-slate-200 rounded-md transition-colors text-text-muted"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
