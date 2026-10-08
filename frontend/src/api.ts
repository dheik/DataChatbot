import { Platform } from 'react-native';

// No emulador Android, "localhost" é o próprio emulador: o PC fica em 10.0.2.2.
const DEFAULT_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
export const API_URL = process.env.EXPO_PUBLIC_API_URL || DEFAULT_URL;

export type Pokemon = {
  id: number;
  pokedex_number: number;
  name: string;
  species: string;
  form: string | null;
  form_category: 'base' | 'regional' | 'mega' | 'gigantamax' | 'alternate';
  types: string[];
  hp: number; attack: number; defense: number; sp_attack: number; sp_defense: number; speed: number;
  total: number;
  generation: number;
  region: string;
  height_m: number;
  weight_kg: number;
  is_legendary: boolean;
  is_mythical: boolean;
  is_baby: boolean;
  capture_rate: number | null;
  sprite_url: string;
  abilities: { name: string; hidden: boolean }[];
  query_values?: Record<string, unknown>;
};

export type AskResponse = {
  id: string;
  question: string;
  answer: string;
  explanation: string;
  sql: string;
  result_type: 'pokemon' | 'table';
  pokemon: Pokemon[];
  table: { columns: string[]; rows: Record<string, unknown>[] } | null;
  row_count: number;
  truncated: boolean;
  self_corrected: boolean;
  model: string | null;
  cached: boolean;
  elapsed_ms: number;
};

export class ApiError extends Error {
  constructor(message: string, public code: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    });
  } catch {
    throw new ApiError(`Sem conexão com a API em ${API_URL}. Verifique se o backend está rodando.`, 'network');
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(body?.error?.message || `Erro ${res.status} na API.`, body?.error?.code || 'http');
  }
  return body as T;
}

export const api = {
  ask: (question: string, sessionId: string) =>
    request<AskResponse>('/api/ask', { method: 'POST', body: JSON.stringify({ question, session_id: sessionId }) }),
  examples: () => request<string[]>('/api/examples'),
};
