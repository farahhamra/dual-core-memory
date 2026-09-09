import fs from 'node:fs';
import path from 'node:path';
import { CONFIG, TABLE_NAMES } from './config.js';
import { save } from './save.js';
import { resolveTableName } from './db.js';

/**
 * Path to the provisional candidates staging file in data/.
 */
function getCandidatesFilePath() {
  return path.join(CONFIG.db.storagePath, 'provisional-candidates.json');
}

/**
 * Load all candidates from disk.
 * @returns {Array<Object>}
 */
export function loadCandidates() {
  const filePath = getCandidatesFilePath();
  if (!fs.existsSync(filePath)) {
    return [];
  }
  try {
    const raw = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    console.warn(`[Warning] Failed reading provisional candidates: ${err.message}`);
    return [];
  }
}

/**
 * Save candidates to disk.
 * @param {Array<Object>} candidates
 */
export function saveCandidates(candidates) {
  const filePath = getCandidatesFilePath();
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(filePath, JSON.stringify(candidates, null, 2), 'utf8');
}

/**
 * Generate a deterministic or slug-based candidate ID.
 */
function generateCandidateId(title = '') {
  const slug = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
    .slice(0, 40);
  return `cand-${slug || Date.now()}`;
}

/**
 * Record a technical/episodic candidate solution through the Provisional Gate.
 * - 1st sighting: Staged as "unconfirmed" (reinforcement = 1). NOT written to LanceDB.
 * - 2nd sighting: Automatically promoted to LanceDB as "confirmed" episodic memory!
 * @param {Object} options
 * @param {string} options.title - Short description of the error/solution
 * @param {string} options.content - The fix/workaround steps
 * @param {string} [options.category='episodic'] - Sub-category
 * @param {string} [options.domain='error-handling'] - Domain tag
 * @param {string} [options.table] - Target LanceDB table once promoted (default: project_memory)
 * @param {Object} [options.metadata] - Extra context
 * @returns {Promise<Object>} Outcome details
 */
export async function recordCandidate(options = {}) {
  const {
    title,
    content,
    category = 'episodic',
    domain = 'error-handling',
    table = TABLE_NAMES.PROJECT,
    metadata = {},
  } = options;

  if (!title || !content) {
    throw new Error('Candidate requires both "title" and "content".');
  }

  const candidates = loadCandidates();
  const targetId = options.id || generateCandidateId(title);

  // Check if candidate already exists
  const existingIdx = candidates.findIndex(
    (c) => c.id === targetId || c.title.toLowerCase() === title.toLowerCase()
  );

  const now = new Date().toISOString();

  if (existingIdx === -1) {
    // 1st sighting: Stage as unconfirmed
    const newCandidate = {
      id: targetId,
      title,
      content,
      category,
      domain,
      targetTable: resolveTableName(table),
      reinforcementCount: 1,
      trustState: 'unconfirmed',
      firstObservedAt: now,
      lastObservedAt: now,
      metadata,
    };
    candidates.push(newCandidate);
    saveCandidates(candidates);

    return {
      status: 'staged_unconfirmed',
      candidate: newCandidate,
      message: `[Trust Gate] 1st sighting: Staged "${title}" as UNCONFIRMED. Held at gate (not written to LanceDB).`,
    };
  }

  // 2nd sighting (or more): Reinforce and auto-promote!
  const candidate = candidates[existingIdx];
  candidate.reinforcementCount += 1;
  candidate.lastObservedAt = now;
  candidate.content = content; // Update with latest resolution details

  const qualifiesForPromotion = candidate.reinforcementCount >= 2;

  if (qualifiesForPromotion && candidate.trustState !== 'confirmed') {
    candidate.trustState = 'confirmed';
    candidate.promotedAt = now;

    // Write to LanceDB through the Gate!
    const targetTable = candidate.targetTable || TABLE_NAMES.PROJECT;
    await save({
      table: targetTable,
      id: candidate.id,
      title: candidate.title,
      content: candidate.content,
      category: 'episodic',
      metadata: {
        memory_type: 'episodic',
        trust_state: 'confirmed',
        reinforcement_count: candidate.reinforcementCount,
        first_observed_at: candidate.firstObservedAt,
        promoted_at: now,
        domain: candidate.domain,
        source: 'provisional-gate',
        ...candidate.metadata,
      },
    });

    saveCandidates(candidates);

    return {
      status: 'promoted_confirmed',
      candidate,
      message: `[Trust Gate: PROMOTED] 2nd sighting reinforced! Promoted "${title}" to LanceDB (${targetTable}) as fully confirmed episodic memory.`,
    };
  }

  saveCandidates(candidates);
  return {
    status: 'reinforced',
    candidate,
    message: `[Trust Gate] Reinforced "${title}" (count: ${candidate.reinforcementCount}).`,
  };
}

/**
 * Manually confirm and promote a staged candidate immediately.
 * @param {string} id
 * @param {Object} [options]
 * @returns {Promise<Object>}
 */
export async function confirmCandidate(id, options = {}) {
  const candidates = loadCandidates();
  const candidate = candidates.find((c) => c.id === id);

  if (!candidate) {
    throw new Error(`Candidate with ID "${id}" not found in provisional staging.`);
  }

  const now = new Date().toISOString();
  candidate.trustState = 'confirmed';
  candidate.reinforcementCount = Math.max(2, candidate.reinforcementCount + 1);
  candidate.promotedAt = now;
  candidate.manualConfirmation = true;

  const targetTable = options.table ? resolveTableName(options.table) : candidate.targetTable || TABLE_NAMES.PROJECT;

  await save({
    table: targetTable,
    id: candidate.id,
    title: candidate.title,
    content: candidate.content,
    category: 'episodic',
    metadata: {
      memory_type: 'episodic',
      trust_state: 'confirmed',
      reinforcement_count: candidate.reinforcementCount,
      promoted_at: now,
      source: 'manual-confirmation',
      ...candidate.metadata,
    },
  });

  saveCandidates(candidates);

  return {
    status: 'manually_confirmed',
    candidate,
    message: `[Trust Gate: CONFIRMED] Manually approved "${candidate.title}". Promoted into LanceDB (${targetTable}).`,
  };
}
