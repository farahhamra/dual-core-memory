#!/usr/bin/env node

import {
  save,
  search,
  updateMemory,
  deleteMemory,
  getTableStats,
  getTable,
  resolveTableName,
  recordCandidate,
  confirmCandidate,
  loadCandidates,
  CONFIG,
  TABLE_NAMES,
} from '../src/index.js';
import { syncInstincts } from '../scripts/sync-instincts.js';

const [command, ...args] = process.argv.slice(2);

function printHelp() {
  console.log(`
Antigravity Vector Memory CLI
=============================
Powered by Ollama (nomic-embed-text) & LanceDB

Commands:
  search <query> [options]       Semantic search memory records
  save <title> <content> [opts]  Save/upsert a memory record
  update <id> [options]          Update an existing memory record by ID
  delete <id> [options]          Delete a record by ID or category
  stats                          Show row counts and database overview
  dump [options]                 List records from a table
  sync-instincts [options]       Promote qualified CLv2 instincts (conf >= 0.7) to LanceDB
  candidates                     List staged provisional candidates
  record-candidate <title> <sol> Stage an episodic candidate (auto-promotes on 2nd sight)
  confirm-candidate <id>         Manually promote candidate into LanceDB

Flags (Common):
  -t, --table <name>             Target 'default_memory' (default), 'project_memory', or 'all'
  -c, --category <cat>           Category name
  -l, --limit <number>           Result count limit (default: 5)
  --json                         Format output as JSON

Quick Examples:
  node bin/cli.js search "Zod request validation"
  node bin/cli.js search "prisma schema for customers" --table project_memory
  node bin/cli.js save "COA Hierarchy" "Assets -> Current Assets -> Cash" --category "feature-tree" --table project_memory
  node bin/cli.js stats
  node bin/cli.js delete "id-123"
  `);
}

async function handleStats() {
  const stats = await getTableStats();
  console.log('\n Memory Database Overview:');
  console.log(` Storage Path: ${CONFIG.db.storagePath}`);
  console.log(` Model:        ${CONFIG.ollama.model} (${CONFIG.ollama.dimension} dims)`);
  console.log('-'.repeat(50));
  for (const s of stats) {
    console.log(` Table: ${s.name.padEnd(20)} | Rows: ${s.count}`);
  }
  console.log('');
}

async function handleDump() {
  const tableArgIdx = args.findIndex((a) => a === '-t' || a === '--table');
  const tableName = tableArgIdx !== -1 ? args[tableArgIdx + 1] : TABLE_NAMES.DEFAULT;
  const target = resolveTableName(tableName);

  const tbl = await getTable(target);
  const total = await tbl.countRows();
  console.log(`\n Records in table "${target}" (Total: ${total}):\n` + '='.repeat(60));

  if (total === 0) {
    console.log('No records found in this table.\n');
    return;
  }

  // Retrieve all records using empty or scan
  const allRows = await tbl.query().limit(100).toArray();
  allRows.forEach((r, i) => {
    console.log(`[#${i + 1}] ID: ${r.id} | Category: ${r.category}`);
    console.log(`  Title:   ${r.title}`);
    console.log(`  Updated: ${r.updatedAt}`);
    console.log(`  Content: ${r.content.slice(0, 150)}${r.content.length > 150 ? '...' : ''}`);
    console.log('-'.repeat(60));
  });
  console.log('');
}

async function main() {
  if (!command || command === 'help' || command === '--help' || command === '-h') {
    printHelp();
    return;
  }

  switch (command.toLowerCase()) {
    case 'stats':
    case 'list':
    case 'info':
      await handleStats();
      break;

    case 'dump':
      await handleDump();
      break;

    case 'search': {
      // Re-parse args for search
      let table = TABLE_NAMES.DEFAULT;
      let limit = 5;
      let category = null;
      let isJson = false;
      let isAll = false;
      const queryParts = [];

      for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '-t' || arg === '--table') {
          table = args[++i];
        } else if (arg === '-l' || arg === '--limit') {
          limit = parseInt(args[++i], 10);
        } else if (arg === '-c' || arg === '--category') {
          category = args[++i];
        } else if (arg === '-a' || arg === '--all') {
          isAll = true;
        } else if (arg === '--json') {
          isJson = true;
        } else if (!arg.startsWith('-')) {
          queryParts.push(arg);
        }
      }

      const query = queryParts.join(' ');
      if (!query) {
        console.error('Error: Please specify search query.');
        process.exit(1);
      }

      const results = await search({
        table: isAll ? 'all' : table,
        query,
        limit,
        category,
      });

      if (isJson) {
        console.log(JSON.stringify(results, null, 2));
      } else {
        console.log(`\n Vector Search Results (${results.length} found for: "${query}"):`);
        console.log(`Target: ${isAll ? 'all' : table}\n` + '='.repeat(60));
        if (results.length === 0) {
          console.log('No relevant memory records found.');
        } else {
          results.forEach((item, idx) => {
            console.log(`\n[#${idx + 1}] ${item.title}`);
            console.log(`  Table:    ${item.table} | Type: ${item.memoryType || 'declarative'} (${item.category})`);
            console.log(
              `  Rank:     ${item.rankScore ?? item.score} (Sim: ${item.similarity ?? item.score} | Trust: ${item.trustScore ?? 1.0} | Freshness: ${item.freshnessWeight ?? 1.0})`
            );
            console.log(`  ID:       ${item.id} | Updated: ${item.updatedAt}`);
            if (Object.keys(item.metadata).length > 0) {
              console.log(`  Metadata: ${JSON.stringify(item.metadata)}`);
            }
            console.log(`  Content:\n  ${item.content.split('\n').join('\n  ')}`);
            console.log('-'.repeat(60));
          });
        }
        console.log('');
      }
      break;
    }

    case 'save': {
      let table = TABLE_NAMES.DEFAULT;
      let category = 'general';
      let id = null;
      let metaStr = '{}';
      let isJson = false;
      const positional = [];

      for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '-t' || arg === '--table') {
          table = args[++i];
        } else if (arg === '-c' || arg === '--category') {
          category = args[++i];
        } else if (arg === '--id') {
          id = args[++i];
        } else if (arg === '-m' || arg === '--meta') {
          metaStr = args[++i];
        } else if (arg === '--json') {
          isJson = true;
        } else if (!arg.startsWith('-')) {
          positional.push(arg);
        }
      }

      if (positional.length < 2) {
        console.error('Error: "save" requires at least <title> and <content>.');
        console.error('Usage: node cli.js save "Title" "Content" [options]');
        process.exit(1);
      }

      const title = positional[0];
      const content = positional.slice(1).join(' ');

      let parsedMeta = {};
      try {
        parsedMeta = JSON.parse(metaStr);
      } catch {
        parsedMeta = { raw: metaStr };
      }

      const res = await save({
        table,
        id,
        title,
        content,
        category,
        metadata: parsedMeta,
      });

      if (isJson) {
        console.log(JSON.stringify(res));
      } else {
        console.log(`\n Memory Saved Successfully!`);
        console.log(`  Table:    ${res.table}`);
        console.log(`  ID:       ${res.id}`);
        console.log(`  Title:    ${res.title}`);
        console.log(`  Category: ${res.category}`);
        console.log(`  Updated:  ${res.updatedAt}\n`);
      }
      break;
    }

    case 'update': {
      let table = TABLE_NAMES.DEFAULT;
      let category = null;
      let title = null;
      let content = null;
      let metaStr = null;
      let isJson = false;
      const positional = [];

      for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '-t' || arg === '--table') {
          table = args[++i];
        } else if (arg === '-c' || arg === '--category') {
          category = args[++i];
        } else if (arg === '--title') {
          title = args[++i];
        } else if (arg === '--content') {
          content = args[++i];
        } else if (arg === '-m' || arg === '--meta') {
          metaStr = args[++i];
        } else if (arg === '--json') {
          isJson = true;
        } else if (!arg.startsWith('-')) {
          positional.push(arg);
        }
      }

      if (positional.length === 0) {
        console.error('Error: "update" requires at least an <id>.');
        console.error('Usage: node cli.js update <id> [options]');
        process.exit(1);
      }

      const id = positional[0];
      if (!title && positional.length > 1) {
        title = positional[1];
      }
      if (!content && positional.length > 2) {
        content = positional.slice(2).join(' ');
      }

      let parsedMeta = null;
      if (metaStr) {
        try {
          parsedMeta = JSON.parse(metaStr);
        } catch {
          parsedMeta = { raw: metaStr };
        }
      }

      const updateRes = await updateMemory({
        table,
        id,
        title,
        content,
        category,
        metadata: parsedMeta,
      });

      if (isJson) {
        console.log(JSON.stringify(updateRes));
      } else {
        console.log(`\n Memory Updated Successfully!`);
        console.log(`  Table:    ${updateRes.table}`);
        console.log(`  ID:       ${updateRes.id}`);
        console.log(`  Title:    ${updateRes.title}`);
        console.log(`  Category: ${updateRes.category}`);
        console.log(`  Updated:  ${updateRes.updatedAt}\n`);
      }
      break;
    }

    case 'delete': {
      let table = TABLE_NAMES.DEFAULT;
      let category = null;
      let isJson = false;
      let isAll = false;
      let id = null;

      for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '-t' || arg === '--table') {
          table = args[++i];
        } else if (arg === '-c' || arg === '--category') {
          category = args[++i];
        } else if (arg === '-a' || arg === '--all') {
          isAll = true;
        } else if (arg === '--json') {
          isJson = true;
        } else if (!arg.startsWith('-')) {
          id = arg;
        }
      }

      if (!id && !category) {
        console.error('Error: "delete" requires either an <id> or --category.');
        process.exit(1);
      }

      const delRes = await deleteMemory({
        table: isAll ? 'all' : table,
        id,
        category,
      });

      if (isJson) {
        console.log(JSON.stringify(delRes, null, 2));
      } else {
        console.log(`\n Memory Deletion Result:`);
        if (id) console.log(`  Target ID:       ${id}`);
        if (category) console.log(`  Target Category: ${category}`);
        delRes.details.forEach((d) => {
          console.log(`  Table [${d.table}]: Deleted ${d.deletedCount} row(s) | Remaining: ${d.remainingCount}`);
        });
        console.log('');
      }
      break;
    }

    case 'sync':
    case 'sync-instincts': {
      const dryRun = args.includes('--dry-run') || args.includes('-n');
      const confIdx = args.findIndex((a) => a === '--min-confidence' || a === '-c');
      const minConfidence = confIdx !== -1 ? parseFloat(args[confIdx + 1]) : 0.7;
      const tblIdx = args.findIndex((a) => a === '--table' || a === '-t');
      const table = tblIdx !== -1 ? args[tblIdx + 1] : null;
      const dirIdx = args.findIndex((a) => a === '--dir' || a === '-d');
      const homunculusDir = dirIdx !== -1 ? args[dirIdx + 1] : null;

      await syncInstincts({ minConfidence, dryRun, table, homunculusDir });
      break;
    }

    case 'candidates':
    case 'list-candidates': {
      const candidates = loadCandidates();
      console.log(`\n Provisional Candidates Staging (${candidates.length} tracked):\n` + '='.repeat(60));
      if (candidates.length === 0) {
        console.log('No candidates currently staged.\nRun "node bin/cli.js record-candidate <title> <content>" to stage one.\n');
        return;
      }
      candidates.forEach((c, idx) => {
        console.log(`\n[#${idx + 1}] ID: ${c.id}`);
        console.log(`  Title:         ${c.title}`);
        console.log(
          `  Trust State:   ${c.trustState.toUpperCase()} (Seen ${c.reinforcementCount} time${c.reinforcementCount > 1 ? 's' : ''})`
        );
        console.log(`  Domain:        ${c.domain} | Category: ${c.category} | Target: ${c.targetTable}`);
        console.log(`  First Seen:    ${c.firstObservedAt}`);
        console.log(`  Solution:\n  ${c.content.slice(0, 150)}${c.content.length > 150 ? '...' : ''}`);
        console.log('-'.repeat(60));
      });
      console.log('');
      break;
    }

    case 'record-candidate': {
      const positional = args.filter((a) => !a.startsWith('-'));
      const title = positional[0];
      const content = positional.slice(1).join(' ');
      if (!title || !content) {
        console.error('Usage: node bin/cli.js record-candidate "<title>" "<solution_content>"');
        process.exit(1);
      }
      const res = await recordCandidate({ title, content });
      console.log(`\n${res.message}\n`);
      break;
    }

    case 'confirm-candidate':
    case 'promote-candidate': {
      const id = args.find((a) => !a.startsWith('-'));
      if (!id) {
        console.error('Usage: node bin/cli.js confirm-candidate "<candidate_id>"');
        process.exit(1);
      }
      const res = await confirmCandidate(id);
      console.log(`\n${res.message}\n`);
      break;
    }

    default:
      console.error(`Unknown command: "${command}". Run "node cli.js --help" for usage.`);
      process.exit(1);
  }
}

main().catch((err) => {
  console.error(`CLI Error: ${err.message}`);
  process.exit(1);
});
