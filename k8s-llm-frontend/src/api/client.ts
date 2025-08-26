// src/api/client.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000', // Adjust if your FastAPI backend runs on a different port
  headers: {
    'Content-Type': 'application/json',
  },
});

export default client;
