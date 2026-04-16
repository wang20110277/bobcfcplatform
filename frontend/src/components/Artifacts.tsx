import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { FileText, Presentation, Music, Download, Search, Filter, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Artifact } from '../types';
import { cn } from '../lib/utils';
import { format } from 'date-fns';
import { API_BASE } from '../lib/api';

export function Artifacts() {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [filter, setFilter] = useState('ALL');
  const { t } = useTranslation();

  useEffect(() => {
    fetch(`${API_BASE}/api/artifacts`, { credentials: 'include' })
      .then(res => res.json())
      .then(setArtifacts);
  }, []);

  const filtered = filter === 'ALL' ? artifacts : artifacts.filter(a => a.type === filter);

  const getIcon = (type: string) => {
    switch (type) {
      case 'PPT': return Presentation;
      case 'AUDIO': return Music;
      default: return FileText;
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto h-full overflow-y-auto bg-white">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-primary">{t('artifact_repo')}</h2>
          <p className="text-text-muted mt-1 text-sm">{t('manage_platform')}</p>
        </div>
        <div className="flex gap-2 bg-sidebar p-1 rounded-lg border border-border">
          {['ALL', 'PPT', 'AUDIO', 'SUMMARY'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "px-4 py-1.5 rounded-md text-xs font-bold transition-all",
                filter === f ? "bg-accent text-white shadow-sm" : "text-text-muted hover:bg-slate-200"
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 bg-sidebar rounded-xl border border-border">
          <Box className="w-12 h-12 text-slate-300 mb-4" />
          <p className="text-text-muted text-sm font-medium">{t('no_artifacts')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((artifact, i) => {
            const Icon = getIcon(artifact.type);
            return (
              <motion.div
                key={artifact.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-white rounded-lg p-4 border border-border flex items-center gap-4 group hover:border-accent transition-colors shadow-sm"
              >
                <div className={cn(
                  "w-10 h-10 rounded-md flex items-center justify-center text-[10px] font-extrabold shrink-0",
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
                <button className="p-2 text-text-muted hover:text-accent opacity-0 group-hover:opacity-100 transition-all">
                  <Download className="w-4 h-4" />
                </button>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Box({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    </svg>
  );
}
