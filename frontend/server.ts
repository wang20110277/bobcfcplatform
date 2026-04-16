import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import { fileURLToPath } from 'url';
import { request as httpRequest } from 'node:http';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { v4 as uuidv4 } from 'uuid';
import dotenv from 'dotenv';
import { Message, Agent, User, Artifact, Conversation } from './src/types';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');
const BACKEND_API = process.env.BACKEND_API || 'http://localhost:8000';

// In-memory "database" for demo mode (used when backend is not OIDC mode)
const users = [
  { id: '1', username: 'admin', role: 'SUPER_ADMIN', email: 'admin@example.com', allowedAgentIds: ['a1', 'a2', 'a3', 'a4'] },
  { id: '2', username: 'user', role: 'SUPER_ADMIN', email: 'wang20110277@gmail.com', allowedAgentIds: ['a1', 'a2', 'a3', 'a4'] },
  { id: '3', username: 'regular_user', role: 'REGULAR_USER', email: 'regular@example.com', allowedAgentIds: ['a1'] }
];

const skills = [
  { id: 's1', name: 'Text Summary', description: 'Summarize long texts into concise points.', type: 'TEXT_SUMMARY', status: 'ACTIVE' },
  { id: 's2', name: 'PPT Generator', description: 'Create presentation outlines and slides.', type: 'PPT_GENERATION', status: 'ACTIVE' },
  { id: 's3', name: 'Audio Generator', description: 'Convert text to speech or generate audio scripts.', type: 'AUDIO_GENERATION', status: 'ACTIVE' },
  { id: 's4', name: 'Skill Creator', description: 'Design and prototype new AI skills for the repository.', type: 'SKILL_CREATION', status: 'ACTIVE' }
];

const agents = [
  { id: 'a1', name: 'PPT Assistant', description: 'Expert in creating professional presentations.', status: 'ACTIVE', skillIds: ['s1', 's2'], recommendedModel: 'gemini-2.0-flash' },
  { id: 'a2', name: 'Content Creator', description: 'Helps with writing and summarizing content.', status: 'ACTIVE', skillIds: ['s1'], recommendedModel: 'gemini-1.5-flash' },
  { id: 'a3', name: 'Audio Producer', description: 'Specialized in audio scripts and production.', status: 'ACTIVE', skillIds: ['s3'], recommendedModel: 'gemini-1.5-pro' },
  { id: 'a4', name: 'SkillCreator', description: 'Specialized agent for building and refining new AI capabilities.', status: 'ACTIVE', skillIds: ['s4'], recommendedModel: 'gemini-2.0-flash' }
];

const conversations: Conversation[] = [];
const artifacts: Artifact[] = [];
let currentUser: User | null = null;

/**
 * Manually proxy a request to the backend.
 * Preserves path, forwards Set-Cookie and Location headers correctly.
 */
function proxyToBackend(req: express.Request, res: express.Response) {
  const proxyUrl = new URL(req.originalUrl, BACKEND_API);

  const headers: Record<string, string> = {};
  for (const [key, value] of Object.entries(req.headers)) {
    if (!['host', 'content-length'].includes(key.toLowerCase()) && value !== undefined) {
      headers[key] = Array.isArray(value) ? value.join(', ') : String(value);
    }
  }
  headers['host'] = new URL(BACKEND_API).host;

  let bodyData = '';
  if (req.body && Object.keys(req.body).length > 0) {
    bodyData = JSON.stringify(req.body);
    headers['Content-Type'] = 'application/json';
    headers['Content-Length'] = Buffer.byteLength(bodyData).toString();
  }

  console.log(`[Proxy] ${req.method} ${req.originalUrl} → ${proxyUrl.href}`);

  const proxyReq = httpRequest(proxyUrl, {
    method: req.method,
    headers,
  }, (proxyRes) => {
    res.statusCode = proxyRes.statusCode || 500;
    res.statusMessage = proxyRes.statusMessage || '';

    // Extract and rewrite Set-Cookie headers so browser accepts them on localhost:3000
    const rawCookies = proxyRes.headers['set-cookie'];
    if (rawCookies) {
      const rewrittenCookies = (Array.isArray(rawCookies) ? rawCookies : [rawCookies]).map(c => {
        return c.replace(/Domain=[^;]+/gi, '').replace(/; Secure/gi, '');
      });
      console.log(`[Proxy] Set-Cookie: ${JSON.stringify(rewrittenCookies)}`);
      // Set each cookie as a separate header
      for (const cookie of rewrittenCookies) {
        res.appendHeader('Set-Cookie', cookie);
      }
    }

    // Forward all other headers (exclude set-cookie and transfer-encoding)
    for (const [key, value] of Object.entries(proxyRes.headers)) {
      const k = key.toLowerCase();
      if (k !== 'set-cookie' && k !== 'transfer-encoding' && value !== undefined) {
        res.setHeader(key, value);
      }
    }

    if (proxyRes.headers['location']) {
      console.log(`[Proxy] Redirect → ${proxyRes.headers['location']}`);
    }

    // Pipe body only (headers already set above)
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on('error', (err: Error) => {
    console.error(`[Proxy Error] ${err.message}`);
    res.status(502).json({ error: 'Backend unavailable' });
  });

  if (bodyData) {
    proxyReq.write(bodyData);
  }
  proxyReq.end();
}

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Proxy all /api/* requests to FastAPI backend
  app.all('/api*', (req: express.Request, res: express.Response) => {
    proxyToBackend(req, res);
  });

  // Demo fallback routes (used when backend is down)
  app.get('/api/auth/me', (req, res) => {
    res.json(currentUser);
  });

  app.post('/api/auth/login', (req, res) => {
    currentUser = users[1] as User;
    res.json({ status: 'ok' });
  });

  app.post('/api/auth/logout', (req, res) => {
    currentUser = null;
    res.json({ status: 'ok' });
  });

  app.get('/api/agents', (req, res) => {
    let filteredAgents = agents;
    if (currentUser?.role !== 'SUPER_ADMIN') {
      filteredAgents = agents.filter(a =>
        a.status === 'ACTIVE' &&
        currentUser?.allowedAgentIds?.includes(a.id)
      );
    } else {
      if (req.query.sidebar === 'true') {
        filteredAgents = agents.filter(a => a.status === 'ACTIVE');
      }
    }
    res.json(filteredAgents);
  });

  app.put('/api/agents/:id', (req, res) => {
    const { skillIds, name, description, status, recommendedModel } = req.body;
    const index = agents.findIndex(a => a.id === req.params.id);
    if (index !== -1) {
      agents[index] = { ...agents[index], ...req.body };
      res.json(agents[index]);
    } else {
      res.status(404).json({ error: 'Agent not found' });
    }
  });

  app.get('/api/skills', (req, res) => {
    res.json(skills);
  });

  app.get('/api/conversations', (req, res) => {
    res.json(conversations);
  });

  app.get('/api/conversations/:id', (req, res) => {
    const conv = conversations.find(c => c.id === req.params.id);
    if (conv) res.json(conv);
    else res.status(404).json({ error: 'Conversation not found' });
  });

  app.post('/api/conversations', (req, res) => {
    const { agentId, title, modelId } = req.body;
    const agent = agents.find(a => a.id === agentId);
    const newConv: Conversation = {
      id: uuidv4(),
      userId: '2',
      agentId,
      messages: [],
      title: title || 'New Conversation',
      modelId: modelId || agent?.recommendedModel || 'gemini-2.0-flash'
    };
    conversations.unshift(newConv);
    res.json(newConv);
  });

  app.patch('/api/conversations/:id', (req, res) => {
    const { modelId } = req.body;
    const conv = conversations.find(c => c.id === req.params.id);
    if (conv) {
      if (modelId) conv.modelId = modelId;
      res.json(conv);
    } else {
      res.status(404).json({ error: 'Conversation not found' });
    }
  });

  app.post('/api/chat', async (req, res) => {
    const { message, conversationId } = req.body;
    const conv = conversations.find(c => c.id === conversationId);
    if (!conv) return res.status(404).json({ error: 'Conversation not found' });

    const agent = agents.find(a => a.id === conv.agentId);
    const currentModelId = conv.modelId || 'gemini-2.0-flash';
    const currentModel = genAI.getGenerativeModel({ model: currentModelId });

    try {
      const chat = currentModel.startChat({
        history: conv.messages.map((h: any) => ({
          role: h.role === 'user' ? 'user' : 'model',
          parts: [{ text: h.content }],
        })),
      });

      const prompt = agent
        ? `You are ${agent.name}: ${agent.description}. Use your skills: ${agent.skillIds.join(', ')}. ${message}`
        : message;

      const userMsg: Message = { role: 'user', content: message, timestamp: new Date().toISOString() };
      conv.messages.push(userMsg);

      const result = await chat.sendMessage(prompt);
      const response = await result.response;
      const text = response.text();

      const assistantMsg: Message = { role: 'assistant', content: text, timestamp: new Date().toISOString() };
      conv.messages.push(assistantMsg);

      if (conv.messages.length === 2) {
        conv.title = message.substring(0, 30) + (message.length > 30 ? '...' : '');
      }

      res.json({ content: text, conversation: conv });
    } catch (error) {
      console.error('Chat error:', error);
      res.status(500).json({ error: 'Failed to generate response' });
    }
  });

  app.post('/api/artifacts/generate', (req, res) => {
    const { type, sessionId, name } = req.body;
    const artifact: Artifact = {
      id: uuidv4(),
      sessionId,
      name: name || `Generated ${type}`,
      type,
      status: 'COMPLETED',
      createdAt: new Date().toISOString(),
      storagePath: `/mock-storage/${type}-${Date.now()}.file`
    };
    artifacts.push(artifact);
    res.json(artifact);
  });

  app.get('/api/artifacts', (req, res) => {
    res.json(artifacts);
  });

  app.get('/api/users', (req, res) => {
    if (currentUser?.role !== 'SUPER_ADMIN') return res.status(403).json({ error: 'Forbidden' });
    res.json(users);
  });

  app.put('/api/users/:id', (req, res) => {
    if (currentUser?.role !== 'SUPER_ADMIN') return res.status(403).json({ error: 'Forbidden' });
    const index = users.findIndex(u => u.id === req.params.id);
    if (index !== -1) {
      users[index] = { ...users[index], ...req.body };
      res.json(users[index]);
    } else {
      res.status(404).json({ error: 'User not found' });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
