import fs from 'node:fs';
import path from 'node:path';
import * as lancedb from '@lancedb/lancedb';
import * as arrow from 'apache-arrow';
import { CONFIG, TABLE_NAMES } from './config.js';

let dbInstance = null;

/**
 * LanceDB arrow schema for memory records.
 */
export const memorySchema = new arrow.Schema([
  new arrow.Field('id', new arrow.Utf8(), false),
  new arrow.Field(
    'vector',
    new arrow.FixedSizeList(CONFIG.ollama.dimension, new arrow.Field('item', new arrow.Float32())),
    false
  ),
  new arrow.Field('title', new arrow.Utf8(), false),
  new arrow.Field('content', new arrow.Utf8(), false),
  new arrow.Field('category', new arrow.Utf8(), false),
  new arrow.Field('metadata', new arrow.Utf8(), false),
  new arrow.Field('createdAt', new arrow.Utf8(), false),
  new arrow.Field('updatedAt', new arrow.Utf8(), false),
]);

/**
 * Get or establish LanceDB connection.
 * @returns {Promise<lancedb.Connection>}
 */
export async function getDatabase() {
  if (!dbInstance) {
    if (!fs.existsSync(CONFIG.db.storagePath)) {
      fs.mkdirSync(CONFIG.db.storagePath, { recursive: true });
    }
    dbInstance = await lancedb.connect(CONFIG.db.storagePath);
  }
  return dbInstance;
}

/**
 * Normalize and resolve table name.
 * @param {string} name
 * @returns {string}
 */
export function resolveTableName(name) {
  if (!name) return TABLE_NAMES.DEFAULT;
  const normalized = name.toLowerCase().replace(/-/g, '_');
  if (normalized === 'default' || normalized === 'default_memory') {
    return TABLE_NAMES.DEFAULT;
  }
  if (normalized === 'project' || normalized === 'project_memory') {
    return TABLE_NAMES.PROJECT;
  }
  return normalized;
}

/**
 * Get or create table with schema.
 * @param {string} [name]
 * @returns {Promise<lancedb.Table>}
 */
export async function getTable(name) {
  const tableName = resolveTableName(name);
  const db = await getDatabase();
  const existingTables = await db.tableNames();

  if (existingTables.includes(tableName)) {
    return await db.openTable(tableName);
  }

  // Create table with arrow schema
  return await db.createEmptyTable(tableName, memorySchema);
}

/**
 * Initialize all registered tables in LanceDB.
 */
export async function initializeTables() {
  const tables = [TABLE_NAMES.DEFAULT, TABLE_NAMES.PROJECT];
  for (const t of tables) {
    await getTable(t);
  }
}

/**
 * List all memory tables with their record counts.
 */
export async function getTableStats() {
  const db = await getDatabase();
  const existing = await db.tableNames();
  const stats = [];

  for (const name of existing) {
    const tbl = await db.openTable(name);
    const count = await tbl.countRows();
    stats.push({ name, count });
  }

  return stats;
}

export default {
  getDatabase,
  getTable,
  getTableStats,
  initializeTables,
  resolveTableName,
  memorySchema,
};
