// API base URL for fetch calls.
// In dev, this goes directly to the FastAPI backend so cookies work natively.
export const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
