import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { getTable, resolveTableName } from './db.js';
import { getEmbedding } from './embedder.js';
import { TABLE_NAMES } from './config.js';

/**
 * Update an existing memory record in the specified table.
 * @param {Object} options
 * @param {string} [options.table] - 'default_memory' or 'project_memory' (defaults to 'project_memory')
 * @param {string} options.id - The unique ID of the record to update (required).
 * @param {string} [options.title] - Updated title (optional).
 * @param {string} [options.content] - Updated content (optional).
 * @param {string} [options.category] - Updated category (optional).
 * @param {Object|string} [options.metadata] - Updated metadata (optional).
 * @returns {Promise<Object>}
 */
export async function updateMemory(options = {}) {
  const {
    table: rawTable = TABLE_NAMES.DEFAULT,
    id,
    title,
    content,
    category,
    metadata,
  } = options;

  if (!id || typeof id !== 'string' || id.trim().length === 0) {
    throw new Error('A valid "id" is required to update a memory record.');
  }

  const tableName = resolveTableName(rawTable);
  const tbl = await getTable(tableName);

  const cleanId = id.trim();
  const escapedId = cleanId.replace(/'/g, "''");

  // Query existing record
  const existingRows = await tbl.query().where(`id = '${escapedId}'`).limit(1).toArray();
  if (existingRows.length === 0) {
    throw new Error(`Record with id "${cleanId}" not found in table "${tableName}".`);
  }

  const existing = existingRows[0];

  const newTitle = (title !== undefined && title !== null && String(title).trim().length > 0)
    ? String(title).trim()
    : existing.title;

  const newContent = (content !== undefined && content !== null && String(content).trim().length > 0)
    ? String(content).trim()
    : existing.content;

  const newCategory = (category !== undefined && category !== null && String(category).trim().length > 0)
    ? String(category).trim()
    : existing.category;

  // Handle metadata merge
  let existingMeta = {};
  if (existing.metadata) {
    try {
      existingMeta = typeof existing.metadata === 'string' ? JSON.parse(existing.metadata) : existing.metadata;
    } catch {
      existingMeta = {};
    }
  }

  let finalMeta = { ...existingMeta };
  if (metadata !== undefined && metadata !== null) {
    if (typeof metadata === 'string') {
      try {
        const parsed = JSON.parse(metadata);
        finalMeta = { ...finalMeta, ...parsed };
      } catch {
        finalMeta = { ...finalMeta, raw: metadata };
      }
    } else if (typeof metadata === 'object') {
      finalMeta = { ...finalMeta, ...metadata };
    }
  }

  const metaStr = JSON.stringify(finalMeta);

  // Re-generate vector embedding if title or content was modified
  let vector = existing.vector;
  if (newTitle !== existing.title || newContent !== existing.content || !vector) {
    const textToEmbed = `${newTitle}\n\n${newContent}`;
    vector = await getEmbedding(textToEmbed);
  }

  const now = new Date().toISOString();

  // Delete existing record
  await tbl.delete(`id = '${escapedId}'`);

  // Insert updated record
  const updatedRecord = {
    id: cleanId,
    vector,
    title: newTitle,
    content: newContent,
    category: newCategory,
    metadata: metaStr,
    createdAt: existing.createdAt || now,
    updatedAt: now,
  };

  await tbl.add([updatedRecord]);

  return {
    success: true,
    id: cleanId,
    table: tableName,
    title: updatedRecord.title,
    category: updatedRecord.category,
    metadata: finalMeta,
    updatedAt: now,
  };
}

export const update = updateMemory;

// CLI Execution Support
const isDirectExecution = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];

if (isDirectExecution) {
  try {
    const { values, positionals } = parseArgs({
      options: {
        table: { type: 'string', short: 't', default: TABLE_NAMES.DEFAULT },
        title: { type: 'string' },
        content: { type: 'string', short: 'c' },
        category: { type: 'string' },
        meta: { type: 'string', short: 'm' },
        json: { type: 'boolean', default: false },
        help: { type: 'boolean', short: 'h', default: false },
      },
      allowPositionals: true,
    });

    if (values.help || positionals.length === 0) {
      console.log(`
Usage:
  node update.js <id> [options]
  node update.js <id> [title] [content] [options]

Options:
  -t, --table <name>       Target table: 'default_memory' (default) or 'project_memory'
  --title <title>          Updated memory title/summary
  -c, --content <content>  Updated memory text or documentation
  --category <cat>         Updated category
  -m, --meta <json>        JSON string of metadata updates to merge
  --json                   Output JSON only
  -h, --help               Show help

Examples:
  node update.js "db-table-purchase_orders" --content "New purchase orders DDL with currency_id" --table project_memory
  node update.js "rule-auth" --title "Updated Auth Policy"
      `);
      process.exit(0);
    }

    const id = positionals[0];
    let title = values.title;
    let content = values.content;

    if (!title && positionals.length > 1) {
      title = positionals[1];
    }
    if (!content && positionals.length > 2) {
      content = positionals.slice(2).join(' ');
    }

    let parsedMeta = null;
    if (values.meta) {
      try {
        parsedMeta = JSON.parse(values.meta);
      } catch (e) {
        parsedMeta = { raw: values.meta };
      }
    }

    const result = await updateMemory({
      table: values.table,
      id,
      title,
      content,
      category: values.category,
      metadata: parsedMeta,
    });

    if (values.json) {
      console.log(JSON.stringify(result));
    } else {
      console.log(`\n Memory Updated Successfully!`);
      console.log(`  Table:    ${result.table}`);
      console.log(`  ID:       ${result.id}`);
      console.log(`  Title:    ${result.title}`);
      console.log(`  Category: ${result.category}`);
      console.log(`  Updated:  ${result.updatedAt}\n`);
    }
  } catch (err) {
    console.error(`\n Update Error: ${err.message}\n`);
    process.exit(1);
  }
}

export default updateMemory;
