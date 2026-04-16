import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  en: {
    translation: {
      'app_name': 'AI Agent Platform',
      'chat_console': 'Chat Console',
      'artifact_repo': 'Artifact Repository',
      'admin_panel': 'Admin Panel',
      'my_agents': 'My Agents',
      'current_agent': 'Current Agent',
      'general_assistant': 'General Assistant',
      'share_session': 'Share Session',
      'type_command': 'Type your command or select a skill...',
      'active_artifacts': 'Active Artifacts',
      'session_context': 'Session Context',
      'memory_usage': 'Memory usage: {{percent}}% of {{total}} Tokens.',
      'knowledge_base': 'Knowledge Base: {{version}}',
      'ready_to_download': 'Ready to Download',
      'generating': 'Generating...',
      'no_artifacts': 'No artifacts generated yet.',
      'admin_dashboard': 'Admin Dashboard',
      'manage_platform': 'Manage platform agents, skills, and user permissions.',
      'create_new': 'Create New',
      'agent': 'Agent',
      'skill': 'Skill',
      'agents_management': 'Agents Management',
      'skills_catalog': 'Skills Catalog',
      'verified_via': 'Verified via ADFS',
      'language': 'Language',
      'subject': 'Theme',
      'nexus_ai': 'Nexus AI',
      'aegis_ai': 'Aegis AI',
      'new_chat': 'New Chat',
      'history': 'History',
      'recommended': 'Recommended',
      'start_conversation': 'Start a conversation with {{name}}.',
      'login_title_1': 'Bank of Beijing',
      'login_title_2': 'Consumer Finance Company',
      'login_subtitle': 'Large Model Service Platform',
      'login_description': 'Reshaping work with AI, driving efficiency leaps and innovation breakthroughs',
      'experience_now': 'Experience Now',
      'skill_repository': 'Skill Repository',
      'select_skill_to_add': 'Select a skill from the repository to add to this agent.',
      'add_to_agent': 'Add to Agent',
      'already_added': 'Added',
      'skill_creator_name': 'SkillCreator',
      'skill_creator_desc': 'Specialized agent for building and refining new AI capabilities.',
      'skill_create_skill_name': 'Skill Creator',
      'skill_create_skill_desc': 'Design and prototype new AI skills for the repository.',
      'users_management': 'Users Management',
      'allowed_agents': 'Allowed Agents',
      'role': 'Role',
      'super_admin': 'Super Admin',
      'regular_user': 'Regular User'
    }
  },
  zh: {
    translation: {
      'app_name': 'AI 智能体协作平台',
      'chat_console': '对话控制台',
      'artifact_repo': '制品仓库',
      'admin_panel': '管理后台',
      'my_agents': '我的智能体',
      'current_agent': '当前智能体',
      'general_assistant': '通用助手',
      'share_session': '分享会话',
      'type_command': '输入指令或选择技能...',
      'active_artifacts': '活跃制品',
      'session_context': '会话上下文',
      'memory_usage': '内存占用: {{percent}}% / {{total}} Token',
      'knowledge_base': '知识库: {{version}}',
      'ready_to_download': '可下载',
      'generating': '生成中...',
      'no_artifacts': '暂无生成的制品',
      'admin_dashboard': '管理面板',
      'manage_platform': '管理平台智能体、技能和用户权限。',
      'create_new': '新建',
      'agent': '智能体',
      'skill': '技能',
      'agents_management': '智能体管理',
      'skills_catalog': '技能目录',
      'verified_via': '已通过 ADFS 验证',
      'language': '语言',
      'subject': '主题',
      'nexus_ai': 'Nexus AI (绿色)',
      'aegis_ai': 'Aegis AI (蓝色)',
      'new_chat': '开启新对话',
      'history': '历史记录',
      'recommended': '推荐',
      'start_conversation': '开始与 {{name}} 对话吧。',
      'login_title_1': '北京银行',
      'login_title_2': '消费金融公司',
      'login_subtitle': '大模型服务平台',
      'login_description': '用人工智能重塑工作方式，驱动效率跃升与创新突破',
      'experience_now': '立即体验',
      'skill_repository': '技能仓库',
      'select_skill_to_add': '从仓库中选择一个技能添加到当前智能体。',
      'add_to_agent': '添加到智能体',
      'already_added': '已添加',
      'skill_creator_name': '技能创造者',
      'skill_creator_desc': '专门用于构建和完善新 AI 能力的智能体。',
      'skill_create_skill_name': '技能创造',
      'skill_create_skill_desc': '为仓库设计和原型化新的 AI 技能。',
      'users_management': '用户管理',
      'allowed_agents': '可见智能体',
      'role': '角色',
      'super_admin': '超级管理员',
      'regular_user': '普通用户'
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'zh',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
