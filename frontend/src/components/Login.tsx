import { motion } from 'motion/react';
import { useTranslation } from 'react-i18next';

interface LoginProps {
  onLogin: () => void;
}

export function Login({ onLogin }: LoginProps) {
  const { t } = useTranslation();

  return (
    <div className="relative h-screen w-full bg-white overflow-hidden flex flex-col items-center justify-center font-sans">
      {/* Background Gradient Wave */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
        <div 
          className="w-[120%] h-[400px] opacity-60 blur-[100px] animate-pulse"
          style={{
            background: `
              radial-gradient(ellipse at 20% 50%, #22D3EE 0%, transparent 50%),
              radial-gradient(ellipse at 50% 50%, #8B5CF6 0%, transparent 60%),
              radial-gradient(ellipse at 80% 50%, #EC4899 0%, transparent 50%)
            `,
            transform: 'scaleY(0.5) rotate(-5deg)',
          }}
        />
      </div>

      {/* Content */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative z-10 text-center px-4"
      >
        <h1 className="text-5xl md:text-6xl font-bold text-[#0F172A] mb-2 tracking-tight">
          {t('login_title_1')}
        </h1>
        <h2 className="text-5xl md:text-6xl font-bold text-[#0F172A] mb-6 tracking-tight">
          {t('login_title_2')}
        </h2>
        <h3 className="text-3xl md:text-4xl font-medium text-[#1E293B] mb-12">
          {t('login_subtitle')}
        </h3>

        <button
          onClick={onLogin}
          className="bg-[#0F172A] hover:bg-[#1E293B] text-white px-16 py-4 rounded-md text-lg font-medium transition-all shadow-lg hover:shadow-xl active:scale-95 mb-12"
        >
          {t('experience_now')}
        </button>

        <p className="text-[#64748B] text-lg max-w-2xl mx-auto">
          {t('login_description')}
        </p>
      </motion.div>

      {/* Bottom Left Logo */}
      <div className="absolute bottom-8 left-8 z-20">
        <div className="w-10 h-10 bg-[#1E293B] rounded-full flex items-center justify-center text-white font-bold text-xl">
          N
        </div>
      </div>
    </div>
  );
}
