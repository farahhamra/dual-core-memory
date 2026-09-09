import { save } from './save.js';
import { search } from './search.js';
import { updateMemory } from './update.js';
import { deleteMemory } from './delete.js';
import { getTable, getTableStats, initializeTables, resolveTableName } from './db.js';
import { getEmbedding, getBatchEmbeddings } from './embedder.js';
import { recordCandidate, confirmCandidate, loadCandidates } from './candidate-gate.js';
import { CONFIG, TABLE_NAMES } from './config.js';

export {
  save,
  search,
  updateMemory,
  updateMemory as update,
  deleteMemory,
  recordCandidate,
  confirmCandidate,
  loadCandidates,
  getTable,
  getTableStats,
  initializeTables,
  resolveTableName,
  getEmbedding,
  getBatchEmbeddings,
  CONFIG,
  TABLE_NAMES,
};

export default {
  save,
  search,
  update: updateMemory,
  updateMemory,
  delete: deleteMemory,
  deleteMemory,
  getTable,
  getTableStats,
  initializeTables,
  CONFIG,
  TABLE_NAMES,
};
