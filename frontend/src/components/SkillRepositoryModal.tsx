import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Zap, Search, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Skill, Agent } from '../types';
import { cn } from '../lib/utils';
import { API_BASE } from '../lib/api';

interface SkillRepositoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  agent: Agent;
  onAddSkill: (skillId: string) => void;
}

export function SkillRepositoryModal({ isOpen, onClose, agent, onAddSkill }: SkillRepositoryModalProps) {
  const { t } = useTranslation();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetch(`${API_BASE}/api/skills`, { credentials: 'include' })
        .then(res => res.json())
        .then(setSkills);
    }
  }, [isOpen]);

  const filteredSkills = skills.filter(s => 
    s.name.toLowerCase().includes(search.toLowerCase()) || 
    s.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
          />
          
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]"
          >
            <div className="p-6 border-b border-border flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-primary">{t('skill_repository')}</h2>
                <p className="text-sm text-text-muted mt-1">{t('select_skill_to_add')}</p>
              </div>
              <button 
                onClick={onClose}
                className="p-2 hover:bg-slate-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-text-muted" />
              </button>
            </div>

            <div className="p-4 bg-slate-50 border-b border-border">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search skills..."
                  className="w-full bg-white border border-border rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
              {filteredSkills.map(skill => {
                const isAdded = agent.skillIds.includes(skill.id);
                return (
                  <div 
                    key={skill.id}
                    className={cn(
                      "p-4 rounded-xl border transition-all flex flex-col justify-between group",
                      isAdded 
                        ? "bg-blue-50/50 border-accent/30" 
                        : "bg-white border-border hover:border-accent hover:shadow-md"
                    )}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="p-2 bg-sidebar rounded-lg">
                          <Zap className={cn("w-4 h-4", isAdded ? "text-accent" : "text-text-muted")} />
                        </div>
                        {isAdded && (
                          <span className="flex items-center gap-1 text-[10px] font-bold text-accent uppercase tracking-wider">
                            <Check className="w-3 h-3" />
                            {t('already_added')}
                          </span>
                        )}
                      </div>
                      <h3 className="font-bold text-primary text-sm mb-1">{skill.name}</h3>
                      <p className="text-xs text-text-muted line-clamp-2 mb-4">{skill.description}</p>
                    </div>
                    
                    {!isAdded && (
                      <button
                        onClick={() => onAddSkill(skill.id)}
                        className="w-full py-2 bg-accent text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition-colors"
                      >
                        {t('add_to_agent')}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
