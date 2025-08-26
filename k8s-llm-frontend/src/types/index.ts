// src/types/index.ts

export type Role = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  timestamp?: string;
}

export interface ApiRequest {
  query: string;
}

export interface ApiResponse {
  response: string;
  action_taken?: string;
}
// src/types/index.ts
// src/types/index.ts
export interface Message {
    role: 'user' | 'assistant';
    content: string;
  }
  