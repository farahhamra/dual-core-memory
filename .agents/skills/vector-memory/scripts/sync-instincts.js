#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { save, getTable, resolveTableName, TABLE_NAMES } from '../src/index.js';

const __filename = fileURLToPath(import.meta.url);

/**
 * Resolve the root data directory for continuous-learning-v2 (ecc-homunculus).
 */
export function resolveHomunculusDir(overrideDir = null) {
  if (overrideDir && fs.existsSync(overrideDir)) {
    return overrideDir;
  }
  if (process.env.CLV2_HOMUNCULUS_DIR && fs.existsSync(process.env.CLV2_HOMUNCULUS_DIR)) {
    return process.env.CLV2_HOMUNCULUS_DIR;
  }
  if (process.env.XDG_DATA_HOME) {
    const p = path.join(process.env.XDG_DATA_HOME, 'ecc-homunculus');
    if (fs.existsSync(p)) return p;
  }
  const home = process.env.USERPROFILE || process.env.HOME || '';
  return path.join(home, '.local', 'share', 'ecc-homunculus');
}

/**
 * Parse an instinct YAML file with markdown body without external dependencies.
 * @param {string} rawContent
 * @returns {Object|null}
 */
export function parseInstinctFile(rawContent) {
  if (!rawContent.startsWith('---')) return null;

  const parts = rawContent.split(/^---$/m);
  if (parts.length < 3) return null;

  const frontmatterStr = parts[1];
  const bodyStr = parts.slice(2).join('---').trim();

  const metadata = {};
  for (const line of frontmatterStr.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const colonIdx = trimmed.indexOf(':');
    if (colonIdx === -1) continue;

    const key = trimmed.slice(0, colonIdx).trim();
    let val = trimmed.slice(colonIdx + 1).trim();

    // Strip surrounding quotes
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }

    if (key === 'confidence') {
      metadata[key] = parseFloat(val);
    } else {
      metadata[key] = val;
    }
  }

  // Extract title from body (# Title)
  let title = metadata.id || 'Untitled Instinct';
  const titleMatch = bodyStr.match(/^#\s+(.+)$/m);
  if (titleMatch) {
    title = titleMatch[1].trim();
  }

  // Extract action section (## Action)
  let action = '';
  const actionMatch = bodyStr.match(/##\s+Action\s*\n([\s\S]*?)(?=\n##|$)/i);
  if (actionMatch) {
    action = actionMatch[1].trim();
  }

  // Extract evidence section (## Evidence)
  let evidence = '';
  const evidenceMatch = bodyStr.match(/##\s+Evidence\s*\n([\s\S]*?)(?=\n##|$)/i);
  if (evidenceMatch) {
    evidence = evidenceMatch[1].trim();
  }

  const content = [
    `Trigger: ${metadata.trigger || 'General'}`,
    action ? `Action:\n${action}` : '',
    evidence ? `Evidence:\n${evidence}` : '',
  ]
    .filter(Boolean)
    .join('\n\n');

  return {
    id: metadata.id || `instinct-${Date.now()}`,
    title,
    content,
    confidence: typeof metadata.confidence === 'number' ? metadata.confidence : 0.5,
    domain: metadata.domain || 'workflow',
    trigger: metadata.trigger || '',
    scope: metadata.scope || 'project',
    projectId: metadata.project_id || null,
    projectName: metadata.project_name || null,
    rawBody: bodyStr,
  };
}

/**
 * Scan directory recursively for .yaml instinct files.
 * @param {string} dir
 * @returns {Array<string>}
 */
function findInstinctFiles(dir) {
  const results = [];
  if (!fs.existsSync(dir)) return results;

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findInstinctFiles(fullPath));
    } else if (entry.isFile() && (entry.name.endsWith('.yaml') || entry.name.endsWith('.yml'))) {
      results.push(fullPath);
    }
  }
  return results;
}

/**
 * Sync instincts through the Approach 2 Promotion / Trust Gate into LanceDB.
 * @param {Object} options
 * @param {number} [options.minConfidence=0.7] - Confidence threshold for promotion
 * @param {boolean} [options.dryRun=false] - Preview without saving to LanceDB
 * @param {string} [options.table] - Target table override
 * @param {string} [options.homunculusDir] - Custom homunculus directory
 * @returns {Promise<Object>} Summary statistics
 */
export async function syncInstincts(options = {}) {
  const {
    minConfidence = 0.7,
    dryRun = false,
    table: tableOverride = null,
    homunculusDir: customDir = null,
  } = options;

  const baseDir = resolveHomunculusDir(customDir);
  console.log(`\n=== Approach 2 Promotion & Trust Gate (sync-instincts) ===`);
  console.log(`Homunculus Source: ${baseDir}`);
  console.log(`Promotion Threshold: confidence >= ${minConfidence}`);
  console.log(`Dry Run Mode:        ${dryRun ? 'YES (No writes)' : 'NO (Writing to LanceDB)'}\n`);

  if (!fs.existsSync(baseDir)) {
    console.log(`Source directory not found (${baseDir}). No instincts to sync yet.`);
    return { scanned: 0, promoted: 0, skipped: 0, sourceDir: baseDir };
  }

  // Scan both global instincts and project-scoped instincts
  const instinctFiles = findInstinctFiles(baseDir);
  console.log(`Found ${instinctFiles.length} instinct file(s) across repositories.\n`);

  let scanned = 0;
  let promoted = 0;
  let skipped = 0;

  for (const filePath of instinctFiles) {
    scanned++;
    const rawContent = fs.readFileSync(filePath, 'utf8');
    const instinct = parseInstinctFile(rawContent);

    if (!instinct) {
      console.log(`[SKIP] Could not parse: ${path.basename(filePath)}`);
      skipped++;
      continue;
    }

    const passesGate = instinct.confidence >= minConfidence;
    const targetTable = tableOverride
      ? resolveTableName(tableOverride)
      : instinct.scope === 'global'
      ? TABLE_NAMES.DEFAULT
      : TABLE_NAMES.PROJECT;

    if (!passesGate) {
      console.log(
        `[GATE: REJECTED] "${instinct.title}" (${instinct.id}) - Confidence ${instinct.confidence} < ${minConfidence}`
      );
      skipped++;
      continue;
    }

    console.log(
      `[GATE: PROMOTED] "${instinct.title}" (${instinct.id})` +
        `\n  Confidence: ${instinct.confidence} >= ${minConfidence} | Scope: ${instinct.scope} | Table: ${targetTable}`
    );

    if (!dryRun) {
      const recordId = `instinct-${instinct.id}`;
      await save({
        table: targetTable,
        id: recordId,
        title: instinct.title,
        content: instinct.content,
        category: 'procedural', // 3-Category Taxonomy: Procedural
        metadata: {
          memory_type: 'procedural',
          trust_state: 'confirmed',
          source: 'continuous-learning-v2',
          instinct_id: instinct.id,
          confidence: instinct.confidence,
          domain: instinct.domain,
          trigger: instinct.trigger,
          scope: instinct.scope,
          project_id: instinct.projectId,
          promoted_at: new Date().toISOString(),
        },
      });
      console.log(`  -> Successfully indexed into ${targetTable} [ID: ${recordId}]`);
    }

    promoted++;
  }

  console.log('\n---------------------------------------------------------');
  console.log(`Sync Complete: ${scanned} scanned, ${promoted} promoted, ${skipped} held at gate.`);
  console.log('---------------------------------------------------------\n');

  return { scanned, promoted, skipped, sourceDir: baseDir };
}

// CLI Execution Handler
if (process.argv[1] === __filename) {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run') || args.includes('-n');

  const confIdx = args.findIndex((a) => a === '--min-confidence' || a === '-c');
  const minConfidence = confIdx !== -1 ? parseFloat(args[confIdx + 1]) : 0.7;

  const tblIdx = args.findIndex((a) => a === '--table' || a === '-t');
  const table = tblIdx !== -1 ? args[tblIdx + 1] : null;

  const dirIdx = args.findIndex((a) => a === '--dir' || a === '-d');
  const homunculusDir = dirIdx !== -1 ? args[dirIdx + 1] : null;

  syncInstincts({ minConfidence, dryRun, table, homunculusDir }).catch((err) => {
    console.error(`\nSync Failed: ${err.message}\n`, err);
    process.exit(1);
  });
}

export default syncInstincts;
