import { CONFIG } from './config.js';

/**
 * Generate a 768-dimensional embedding vector for given text using local Ollama nomic-embed-text.
 * @param {string} text
 * @returns {Promise<number[]>}
 */
export async function getEmbedding(text) {
  if (!text || typeof text !== 'string' || text.trim().length === 0) {
    throw new Error('Text to embed must be a non-empty string.');
  }

  const endpoint = `${CONFIG.ollama.baseUrl}/api/embeddings`;
  const payload = {
    model: CONFIG.ollama.model,
    prompt: text.trim(),
  };

  let response;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    throw new Error(
      `Failed to connect to Ollama at ${CONFIG.ollama.baseUrl}. Is Ollama running? (${err.message})`
    );
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Ollama embedding request failed with status ${response.status}: ${errorText}`
    );
  }

  const data = await response.json();
  if (!data.embedding || !Array.isArray(data.embedding)) {
    throw new Error(`Invalid response format from Ollama: ${JSON.stringify(data)}`);
  }

  if (data.embedding.length !== CONFIG.ollama.dimension) {
    console.warn(
      `[Warning] Expected embedding dimension ${CONFIG.ollama.dimension}, received ${data.embedding.length}`
    );
  }

  return data.embedding;
}

/**
 * Generate embeddings for multiple texts sequentially or in parallel batches.
 * @param {string[]} texts
 * @returns {Promise<number[][]>}
 */
export async function getBatchEmbeddings(texts) {
  if (!Array.isArray(texts) || texts.length === 0) {
    return [];
  }

  // Generate embeddings
  const results = [];
  for (const text of texts) {
    const embedding = await getEmbedding(text);
    results.push(embedding);
  }
  return results;
}

export default {
  getEmbedding,
  getBatchEmbeddings,
};
