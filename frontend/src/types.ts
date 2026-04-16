export interface User {
  id: string;
  username: string;
  role: 'SUPER_ADMIN' | 'REGULAR_USER';
  email: string;
  allowedAgentIds?: string[];
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  type: string;
  status: 'ACTIVE' | 'INACTIVE';
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'ACTIVE' | 'INACTIVE';
  skillIds: string[];
  recommendedModel?: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  userId: string;
  agentId?: string;
  messages: Message[];
  title: string;
  modelId?: string;
}

export interface Artifact {
  id: string;
  sessionId: string;
  name: string;
  type: string;
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  createdAt: string;
  storagePath: string;
}
