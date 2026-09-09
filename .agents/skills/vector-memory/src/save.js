import crypto from 'node:crypto';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { getTable, resolveTableName } from './db.js';
import { getEmbedding } from './embedder.js';
import { TABLE_NAMES } from './config.js';

/**
 * Save or upsert a memory record into the specified table.
 * @param {Object} options
 * @param {string} [options.table] - 'default_memory' or 'project_memory' (defaults to 'project_memory')
 * @param {string} [options.id] - Optional custom ID. If omitted, a UUID is generated.
 * @param {string} options.title - Short summary/title of the memory.
 * @param {string} options.content - The main memory text / schema / markdown content.
 * @param {string} [options.category] - Category (e.g. 'schema', 'feature-tree', 'rule', 'pattern', 'fix').
 * @param {Object|string} [options.metadata] - Extra structured metadata (object or JSON string).
 * @returns {Promise<Object>}
 */
export async function save(options = {}) {
  const {
    table: rawTable = TABLE_NAMES.DEFAULT,
    id: inputId,
    title,
    content,
    category = 'general',
    metadata = {},
  } = options;

  if (!title || typeof title !== 'string' || title.trim().length === 0) {
    throw new Error('A valid "title" is required to save a memory.');
  }

  if (!content || typeof content !== 'string' || content.trim().length === 0) {
    throw new Error('A valid "content" string is required to save a memory.');
  }

  const tableName = resolveTableName(rawTable);
  const tbl = await getTable(tableName);

  const id = inputId && typeof inputId === 'string' && inputId.trim().length > 0
    ? inputId.trim()
    : crypto.randomUUID();

  // Generate vector embedding on title + content for optimal semantic recall
  const textToEmbed = `${title.trim()}\n\n${content.trim()}`;
  const vector = await getEmbedding(textToEmbed);

  // Stringify metadata if passed as object
  const metaStr = typeof metadata === 'string'
    ? metadata
    : JSON.stringify(metadata ?? {});

  const now = new Date().toISOString();

  // Upsert: check if record with same id exists, and delete it first if present
  try {
    const escapedId = id.replace(/'/g, "''");
    await tbl.delete(`id = '${escapedId}'`);
  } catch (err) {
    // If table was just created or record didn't exist, ignore
  }

  const record = {
    id,
    vector,
    title: title.trim(),
    content: content.trim(),
    category: (category || 'general').trim(),
    metadata: metaStr,
    createdAt: now,
    updatedAt: now,
  };

  await tbl.add([record]);

  return {
    success: true,
    id,
    table: tableName,
    title: record.title,
    category: record.category,
    metadata: typeof metadata === 'string' ? JSON.parse(metaStr || '{}') : metadata,
    updatedAt: now,
  };
}

// CLI Execution Support
const isDirectExecution = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];

if (isDirectExecution) {
  try {
    const { values, positionals } = parseArgs({
      options: {
        table: { type: 'string', short: 't', default: TABLE_NAMES.DEFAULT },
        title: { type: 'string' },
        content: { type: 'string', short: 'c' },
        category: { type: 'string', default: 'general' },
        id: { type: 'string' },
        meta: { type: 'string', short: 'm' },
        json: { type: 'boolean', default: false },
        help: { type: 'boolean', short: 'h', default: false },
      },
      allowPositionals: true,
    });

    if (values.help) {
      console.log(`
Usage:
  node save.js [options] [title] [content]

Options:
  -t, --table <name>       Target table: 'default_memory' (default) or 'project_memory'
  --title <title>          Memory title/summary
  -c, --content <content>  Memory text or documentation
  --category <cat>         Category (e.g. 'schema', 'feature-tree', 'rule', 'pattern')
  --id <id>                Specific ID (optional, defaults to UUID)
  -m, --meta <json>        JSON string of metadata
  --json                   Output JSON only
  -h, --help               Show help

Examples:
  node save.js --title "RFC 7807 Error Standard" --content "API error schema guidelines" --category "best-practice"
  node save.js --title "Prisma Schema" --content "User model with relations" --category "schema" --table project_memory
  node save.js "Feature Tree" "Auth -> Login, Register, Session" --table project_memory
      `);
      process.exit(0);
    }

    // Support positional arguments: [title] [content]
    let title = values.title;
    let content = values.content;

    if (!title && positionals.length > 0) {
      title = positionals[0];
    }
    if (!content && positionals.length > 1) {
      content = positionals[1];
    }

    let parsedMeta = {};
    if (values.meta) {
      try {
        parsedMeta = JSON.parse(values.meta);
      } catch (e) {
        parsedMeta = { raw: values.meta };
      }
    }

    const result = await save({
      table: values.table,
      id: values.id,
      title,
      content,
      category: values.category,
      metadata: parsedMeta,
    });

    if (values.json) {
      console.log(JSON.stringify(result));
    } else {
      console.log(`\n Memory Saved Successfully!`);
      console.log(`  Table:    ${result.table}`);
      console.log(`  ID:       ${result.id}`);
      console.log(`  Title:    ${result.title}`);
      console.log(`  Category: ${result.category}`);
      console.log(`  Updated:  ${result.updatedAt}\n`);
    }
  } catch (err) {
    console.error(`\n Save Error: ${err.message}\n`);
    process.exit(1);
  }
}

export default save;
