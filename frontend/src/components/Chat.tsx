import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import { Send, Bot, User as UserIcon, Loader2, FileText, Presentation, Music, Cpu, Zap, Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Message, Agent, User, Artifact, Skill } from '../types';
import { cn } from '../lib/utils';
import { API_BASE } from '../lib/api';
import { SkillRepositoryModal } from './SkillRepositoryModal';

interface ChatProps {
  user: User;
}

export function Chat({ user }: ChatProps) {
  const { conversationId } = useParams();
  const { t } = useTranslation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [currentModelId, setCurrentModelId] = useState('gemini-2.0-flash');
  const [availableSkills, setAvailableSkills] = useState<Skill[]>([]);
  const [isSkillModalOpen, setIsSkillModalOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const models = [
    { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', desc: 'Fast & Balanced' },
    { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', desc: 'Optimized for speed' },
    { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', desc: 'Complex reasoning' },
  ];

  useEffect(() => {
    if (conversationId) {
      fetch(`${API_BASE}/api/conversations/${conversationId}`, { credentials: 'include' })
        .then(res => res.json())
        .then(conv => {
          setMessages(conv.messages || []);
          setCurrentModelId(conv.modelId || 'gemini-2.0-flash');
          if (conv.agentId) {
            fetch(`${API_BASE}/api/agents`, { credentials: 'include' })
              .then(res => res.json())
              .then(agents => {
                const found = agents.find((a: Agent) => a.id === conv.agentId);
                setAgent(found || null);
                if (found) {
                  fetchSkills(found.skillIds);
                }
              });
          } else {
            setAgent(null);
            setAvailableSkills([]);
          }
        });
    } else {
      setMessages([]);
      setAgent(null);
      setAvailableSkills([]);
    }
    fetchArtifacts();
  }, [conversationId]);

  const fetchSkills = (skillIds: string[]) => {
    fetch(`${API_BASE}/api/skills`, { credentials: 'include' })
      .then(res => res.json())
      .then(allSkills => {
        const filtered = allSkills.filter((s: Skill) => skillIds.includes(s.id));
        setAvailableSkills(filtered);
      });
  };

  const addSkillFromRepo = async (skillId: string) => {
    if (!agent) return;
    const newSkillIds = [...agent.skillIds, skillId];
    const res = await fetch(`${API_BASE}/api/agents/${agent.id}`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skillIds: newSkillIds })
    });
    const updatedAgent = await res.json();
    setAgent(updatedAgent);
    fetchSkills(newSkillIds);
  };

  const updateModel = async (modelId: string) => {
    if (!conversationId) return;
    setCurrentModelId(modelId);
    await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ modelId })
    });
  };

  const fetchArtifacts = () => {
    fetch(`${API_BASE}/api/artifacts`, { credentials: 'include' })
      .then(res => res.json())
      .then(setArtifacts);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          conversationId
        })
      });

      const data = await response.json();
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.content,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateArtifact = async (type: string) => {
    try {
      await fetch(`${API_BASE}/api/artifacts/generate`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, sessionId: 'current', name: `Artifact from ${agent?.name || 'Chat'}` })
      });
      fetchArtifacts();
    } catch (error) {
      console.error('Artifact error:', error);
    }
  };

  return (
    <div className="flex h-full bg-white">
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-border flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-text-muted">{t('current_agent')}:</span>
              <span className="bg-[#DBEAFE] text-[#1E40AF] px-3 py-1 rounded-full text-xs font-semibold">
                {agent?.name || t('general_assistant')}
              </span>
            </div>
            <div className="h-4 w-px bg-border mx-2" />
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-text-muted" />
              <select
                value={currentModelId}
                onChange={(e) => updateModel(e.target.value)}
                className="text-xs font-semibold bg-transparent border-none focus:ring-0 text-text-main cursor-pointer"
              >
                {models.map(m => (
                  <option key={m.id} value={m.id}>
                    {m.name} {agent?.recommendedModel === m.id ? `(${t('recommended')})` : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button className="px-4 py-2 border border-border rounded-md bg-white text-xs font-semibold hover:bg-slate-50 transition-colors">
            {t('share_session')}
          </button>
        </header>

        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-8 space-y-4"
        >
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50">
              <Bot className="w-12 h-12 text-slate-300" />
              <p className="text-slate-500 max-w-xs text-sm">
                {t('start_conversation', { name: agent?.name || t('general_assistant') })}
              </p>
            </div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "max-w-[80%] p-3 px-4 rounded-xl text-sm leading-relaxed",
                  msg.role === 'user'
                    ? "bg-accent text-white ml-auto"
                    : "bg-artifact-bg text-text-main mr-auto"
                )}
              >
                {msg.content}
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
            <div className="bg-artifact-bg text-text-main mr-auto max-w-[80%] p-3 px-4 rounded-xl text-sm animate-pulse">
              Thinking...
            </div>
          )}
        </div>

        <div className="p-5 border-t border-border flex flex-col gap-3">
          <div className="flex items-center justify-between mb-1">
            <div className="flex gap-2 overflow-x-auto scrollbar-hide flex-1">
              {availableSkills.map(skill => (
                <button
                  key={skill.id}
                  onClick={() => generateArtifact(skill.type)}
                  className="flex items-center gap-2 px-3 py-1.5 bg-sidebar border border-border rounded-full text-[11px] font-bold text-text-muted hover:border-accent hover:text-accent transition-all whitespace-nowrap"
                >
                  <Zap className="w-3 h-3" />
                  {skill.name}
                </button>
              ))}
            </div>
            {user.role === 'SUPER_ADMIN' && (
              <button
                onClick={() => setIsSkillModalOpen(true)}
                className="ml-2 p-1.5 text-text-muted hover:text-accent hover:bg-slate-100 rounded-full transition-all shrink-0"
                title="Add Skill from Repository"
              >
                <Plus className="w-4 h-4" />
              </button>
            )}
          </div>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={t('type_command')}
                className="w-full bg-sidebar border border-border rounded-lg px-4 py-2.5 pr-12 focus:outline-none focus:ring-1 focus:ring-accent transition-all resize-none text-sm"
                rows={1}
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="w-11 h-11 bg-accent text-white rounded-lg flex items-center justify-center hover:bg-blue-700 disabled:opacity-50 transition-colors shrink-0"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <aside className="w-[280px] border-l border-border bg-artifact-bg p-5 flex flex-col overflow-hidden">
        <h3 className="text-[12px] font-bold text-text-muted uppercase tracking-wider mb-4">{t('active_artifacts')}</h3>
        <div className="flex-1 overflow-y-auto space-y-3">
          {artifacts.map((artifact) => (
            <div key={artifact.id} className="bg-white border border-border rounded-lg p-3 flex items-center gap-3 shadow-sm">
              <div className={cn(
                "w-8 h-8 rounded-md flex items-center justify-center text-[10px] font-extrabold shrink-0",
                artifact.type === 'PPT' ? "bg-blue-50 text-accent" : "bg-slate-100 text-text-muted"
              )}>
                {artifact.type}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[13px] font-semibold text-text-main truncate">{artifact.name}</div>
                <div className="text-[11px] text-text-muted truncate">
                  {artifact.status === 'COMPLETED' ? t('ready_to_download') : t('generating')}
                </div>
              </div>
            </div>
          ))}
          {artifacts.length === 0 && (
            <p className="text-xs text-text-muted text-center py-4 italic">{t('no_artifacts')}</p>
          )}
        </div>

        <div className="mt-8">
          <h3 className="text-[12px] font-bold text-text-muted uppercase tracking-wider mb-4">{t('session_context')}</h3>
          <div className="bg-white p-3 rounded-lg border border-border text-[12px] text-text-muted leading-relaxed">
            {t('memory_usage', { percent: 14, total: '2k' })}<br/>
            {t('knowledge_base', { version: 'Enterprise v2' })}
          </div>
        </div>
      </aside>

      {agent && (
        <SkillRepositoryModal
          isOpen={isSkillModalOpen}
          onClose={() => setIsSkillModalOpen(false)}
          agent={agent}
          onAddSkill={(skillId) => {
            addSkillFromRepo(skillId);
            setIsSkillModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
