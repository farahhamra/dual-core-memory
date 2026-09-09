import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const CONFIG = {
  // Ollama configuration
  ollama: {
    baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
    model: process.env.OLLAMA_EMBED_MODEL || 'nomic-embed-text',
    dimension: 768,
  },

  // LanceDB storage
  db: {
    storagePath: path.resolve(__dirname, '..', 'data'),
    tables: {
      default: 'default_memory',
      project: 'project_memory',
    },
  },

  // Search defaults
  search: {
    defaultLimit: 5,
    minScore: 0.2, // cosine similarity threshold
  },
};

export const TABLE_NAMES = {
  DEFAULT: CONFIG.db.tables.default,
  PROJECT: CONFIG.db.tables.project,
};

export default CONFIG;
