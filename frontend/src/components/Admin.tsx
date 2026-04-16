import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Plus, Edit2, Trash2, Shield, Zap, Users, ToggleLeft, ToggleRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Agent, Skill, User } from '../types';
import { cn } from '../lib/utils';
import { API_BASE } from '../lib/api';

export function Admin() {
  const [activeTab, setActiveTab] = useState<'USERS' | 'AGENTS' | 'SKILLS'>('USERS');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const { t } = useTranslation();

  const fetchData = () => {
    fetch(`${API_BASE}/api/agents`, { credentials: 'include' }).then(res => res.json()).then(setAgents);
    fetch(`${API_BASE}/api/skills`, { credentials: 'include' }).then(res => res.json()).then(setSkills);
    fetch(`${API_BASE}/api/users`, { credentials: 'include' }).then(res => res.json()).then(setUsers);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const toggleAgentStatus = async (agent: Agent) => {
    const newStatus = agent.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    await fetch(`${API_BASE}/api/agents/${agent.id}`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    fetchData();
  };

  const toggleSkill = async (agent: Agent, skillId: string) => {
    const newSkillIds = agent.skillIds.includes(skillId)
      ? agent.skillIds.filter(id => id !== skillId)
      : [...agent.skillIds, skillId];
    
    await fetch(`${API_BASE}/api/agents/${agent.id}`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skillIds: newSkillIds })
    });
    fetchData();
  };

  const toggleUserRole = async (user: User) => {
    const newRole = user.role === 'SUPER_ADMIN' ? 'REGULAR_USER' : 'SUPER_ADMIN';
    await fetch(`${API_BASE}/api/users/${user.id}`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: newRole })
    });
    fetchData();
  };

  const toggleAllowedAgent = async (user: User, agentId: string) => {
    const currentAllowed = user.allowedAgentIds || [];
    const newAllowed = currentAllowed.includes(agentId)
      ? currentAllowed.filter(id => id !== agentId)
      : [...currentAllowed, agentId];
    
    await fetch(`${API_BASE}/api/users/${user.id}`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ allowedAgentIds: newAllowed })
    });
    fetchData();
  };

  return (
    <div className="p-8 max-w-6xl mx-auto h-full overflow-y-auto bg-white">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-primary">{t('admin_dashboard')}</h2>
          <p className="text-text-muted mt-1 text-sm">{t('manage_platform')}</p>
        </div>
        <button className="flex items-center gap-2 px-5 py-2.5 bg-accent text-white rounded-lg font-bold hover:bg-blue-700 transition-colors shadow-sm">
          <Plus className="w-4 h-4" />
          {t('create_new')} {activeTab === 'AGENTS' ? t('agent') : activeTab === 'SKILLS' ? t('skill') : t('user')}
        </button>
      </div>

      <div className="flex gap-8 mb-8 border-b border-border">
        <button
          onClick={() => setActiveTab('USERS')}
          className={cn(
            "pb-4 px-2 text-sm font-bold transition-all relative",
            activeTab === 'USERS' ? "text-primary" : "text-text-muted hover:text-primary"
          )}
        >
          <div className="flex items-center gap-2" >
            <Shield className="w-4 h-4" />
            {t('users_management')}
          </div>
          {activeTab === 'USERS' && (
            <motion.div layoutId="tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('AGENTS')}
          className={cn(
            "pb-4 px-2 text-sm font-bold transition-all relative",
            activeTab === 'AGENTS' ? "text-primary" : "text-text-muted hover:text-primary"
          )}
        >
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            {t('agents_management')}
          </div>
          {activeTab === 'AGENTS' && (
            <motion.div layoutId="tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('SKILLS')}
          className={cn(
            "pb-4 px-2 text-sm font-bold transition-all relative",
            activeTab === 'SKILLS' ? "text-primary" : "text-text-muted hover:text-primary"
          )}
        >
          <div className="flex items-center gap-2" >
            <Zap className="w-4 h-4" />
            {t('skills_catalog')}
          </div>
          {activeTab === 'SKILLS' && (
            <motion.div layoutId="tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
          )}
        </button>
      </div>

      {activeTab === 'AGENTS' && (
        <div className="grid grid-cols-1 gap-3">
          {agents.map((agent) => (
            <div key={agent.id} className="relative bg-white p-5 rounded-xl border border-border flex flex-col gap-4 group hover:border-accent transition-colors shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-sidebar rounded-lg flex items-center justify-center">
                    <Users className="w-5 h-5 text-text-muted" />
                  </div>
                  <div>
                    <h3 className="font-bold text-primary text-sm">{agent.name}</h3>
                    <p className="text-xs text-text-muted">{agent.description}</p>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {agent.skillIds.map(sid => {
                        const skill = skills.find(s => s.id === sid);
                        return (
                          <span key={sid} className="text-[9px] font-bold px-2 py-0.5 bg-blue-50 text-accent rounded uppercase border border-blue-100">
                            {skill?.name || sid}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button 
                    onClick={() => toggleAgentStatus(agent)}
                    className={cn(
                      "p-2 rounded-md transition-colors",
                      agent.status === 'ACTIVE' ? "text-accent hover:bg-blue-50" : "text-slate-300 hover:bg-slate-50"
                    )}
                  >
                    {agent.status === 'ACTIVE' ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                  </button>
                  <button 
                    onClick={() => setEditingAgent(editingAgent?.id === agent.id ? null : agent)}
                    className={cn(
                      "p-2 rounded-md transition-all",
                      editingAgent?.id === agent.id ? "bg-accent text-white" : "text-text-muted hover:text-primary hover:bg-slate-50"
                    )}
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button className="p-2 text-text-muted hover:text-red-600 hover:bg-red-50 rounded-md transition-all">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              {editingAgent?.id === agent.id && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="border-t border-border pt-4 mt-2"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-[10px] font-bold text-primary uppercase tracking-wider">Manage Agent Skills</h4>
                    <span className="text-[10px] text-text-muted">{agent.skillIds.length} skills active</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {skills.map(skill => {
                      const isActive = agent.skillIds.includes(skill.id);
                      return (
                        <button
                          key={skill.id}
                          onClick={() => toggleSkill(agent, skill.id)}
                          className={cn(
                            "px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all border flex items-center gap-2",
                            isActive
                              ? "bg-accent text-white border-accent shadow-sm"
                              : "bg-white text-text-muted border-border hover:border-accent hover:text-accent"
                          )}
                        >
                          <Zap className={cn("w-3 h-3", isActive ? "text-white" : "text-text-muted")} />
                          {skill.name}
                        </button>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'SKILLS' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {skills.map((skill) => (
            <div key={skill.id} className="bg-white p-5 rounded-xl border border-border hover:border-accent transition-colors shadow-sm">
              <div className="flex items-start justify-between mb-3">
                <div className="p-2.5 bg-sidebar rounded-lg">
                  <Zap className="w-5 h-5 text-text-muted" />
                </div>
                <div className="flex gap-1">
                  <button className="p-2 text-text-muted hover:text-primary hover:bg-slate-50 rounded-md transition-all">
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button className="p-2 text-text-muted hover:text-red-600 hover:bg-red-50 rounded-md transition-all">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <h3 className="font-bold text-primary text-sm mb-1">{skill.name}</h3>
              <p className="text-xs text-text-muted mb-4 line-clamp-2">{skill.description}</p>
              <div className="flex items-center justify-between pt-3 border-t border-border/50">
                <span className="text-[10px] font-bold px-2 py-0.5 bg-slate-100 text-text-muted rounded uppercase tracking-wider">
                  {skill.type}
                </span>
                <span className={cn(
                  "text-[10px] font-bold uppercase tracking-widest",
                  skill.status === 'ACTIVE' ? "text-accent" : "text-slate-300"
                )}>
                  {skill.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'USERS' && (
        <div className="grid grid-cols-1 gap-3">
          {users.map((u) => (
            <div key={u.id} className="bg-white p-5 rounded-xl border border-border flex flex-col gap-4 group hover:border-accent transition-colors shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-sidebar rounded-lg flex items-center justify-center text-primary font-bold">
                    {u.username[0].toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-bold text-primary text-sm">{u.username}</h3>
                    <p className="text-xs text-text-muted">{u.email}</p>
                    <div className="flex gap-2 mt-2">
                      <span className={cn(
                        "text-[9px] font-bold px-2 py-0.5 rounded uppercase border",
                        u.role === 'SUPER_ADMIN' ? "bg-purple-50 text-purple-600 border-purple-100" : "bg-slate-50 text-slate-500 border-slate-100"
                      )}>
                        {u.role === 'SUPER_ADMIN' ? t('super_admin') : t('regular_user')}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button 
                    onClick={() => toggleUserRole(u)}
                    className="p-2 text-text-muted hover:text-primary hover:bg-slate-50 rounded-md transition-all"
                    title="Toggle Role"
                  >
                    <Shield className={cn("w-4 h-4", u.role === 'SUPER_ADMIN' ? "text-purple-600" : "text-slate-300")} />
                  </button>
                  <button 
                    onClick={() => setEditingUser(editingUser?.id === u.id ? null : u)}
                    className={cn(
                      "p-2 rounded-md transition-all",
                      editingUser?.id === u.id ? "bg-accent text-white" : "text-text-muted hover:text-primary hover:bg-slate-50"
                    )}
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {editingUser?.id === u.id && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="border-t border-border pt-4 mt-2"
                >
                  <h4 className="text-[10px] font-bold text-primary mb-3 uppercase tracking-wider">{t('allowed_agents')}</h4>
                  <div className="flex flex-wrap gap-2">
                    {agents.map(agent => {
                      const isAllowed = u.allowedAgentIds?.includes(agent.id);
                      return (
                        <button
                          key={agent.id}
                          onClick={() => toggleAllowedAgent(u, agent.id)}
                          className={cn(
                            "px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all border flex items-center gap-2",
                            isAllowed
                              ? "bg-accent text-white border-accent shadow-sm"
                              : "bg-white text-text-muted border-border hover:border-accent hover:text-accent"
                          )}
                        >
                          <Users className={cn("w-3 h-3", isAllowed ? "text-white" : "text-text-muted")} />
                          {agent.name}
                        </button>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
