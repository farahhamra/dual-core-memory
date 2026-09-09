import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { getTable, resolveTableName } from './db.js';
import { TABLE_NAMES } from './config.js';

/**
 * Delete memory records by ID or filter.
 * @param {Object} options
 * @param {string} [options.table] - 'project_memory', 'default_memory', or 'all'
 * @param {string} [options.id] - Specific ID to delete
 * @param {string} [options.category] - Delete all records in a category
 * @returns {Promise<Object>}
 */
export async function deleteMemory(options = {}) {
  const {
    table: rawTable = TABLE_NAMES.DEFAULT,
    id,
    category,
  } = options;

  if (!id && !category) {
    throw new Error('Either "id" or "category" must be specified to delete records.');
  }

  const isAll = rawTable === 'all' || rawTable === 'both';
  const targetTables = isAll
    ? [TABLE_NAMES.PROJECT, TABLE_NAMES.DEFAULT]
    : [resolveTableName(rawTable)];

  const results = [];

  for (const tableName of targetTables) {
    const tbl = await getTable(tableName);
    const countBefore = await tbl.countRows();

    if (id) {
      const escapedId = id.trim().replace(/'/g, "''");
      await tbl.delete(`id = '${escapedId}'`);
    } else if (category) {
      const escapedCat = category.trim().replace(/'/g, "''");
      await tbl.delete(`category = '${escapedCat}'`);
    }

    const countAfter = await tbl.countRows();
    const deletedCount = countBefore - countAfter;

    results.push({
      table: tableName,
      deletedCount,
      remainingCount: countAfter,
    });
  }

  return {
    success: true,
    deletedId: id || null,
    deletedCategory: category || null,
    details: results,
  };
}

// CLI Execution Support
const isDirectExecution = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];

if (isDirectExecution) {
  try {
    const { values, positionals } = parseArgs({
      options: {
        table: { type: 'string', short: 't', default: TABLE_NAMES.DEFAULT },
        id: { type: 'string', short: 'i' },
        category: { type: 'string', short: 'c' },
        all: { type: 'boolean', short: 'a', default: false },
        json: { type: 'boolean', default: false },
        help: { type: 'boolean', short: 'h', default: false },
      },
      allowPositionals: true,
    });

    if (values.help) {
      console.log(`
Usage:
  node delete.js [options] [id]

Options:
  -i, --id <id>            Record ID to delete (or provide as positional argument)
  -t, --table <name>       Target table: 'default_memory' (default), 'project_memory', or 'all'
  -c, --category <cat>     Delete all records matching this category
  -a, --all                Apply across both memory tables
  --json                   Output JSON only
  -h, --help               Show help

Examples:
  node delete.js "550e8400-e29b-41d4-a716-446655440000"
  node delete.js --id "schema-users" --table project_memory
  node delete.js --category "temp" --table project_memory
      `);
      process.exit(0);
    }

    let id = values.id;
    if (!id && positionals.length > 0) {
      id = positionals[0];
    }

    if (!id && !values.category) {
      console.error('Error: Provide an ID or --category to delete. Run with --help for details.');
      process.exit(1);
    }

    const targetTable = values.all ? 'all' : values.table;
    const result = await deleteMemory({
      table: targetTable,
      id,
      category: values.category,
    });

    if (values.json) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      console.log(`\n Memory Deletion Result:`);
      if (id) console.log(`  Target ID:       ${id}`);
      if (values.category) console.log(`  Target Category: ${values.category}`);
      result.details.forEach((d) => {
        console.log(`  Table [${d.table}]: Deleted ${d.deletedCount} row(s) | Remaining: ${d.remainingCount}`);
      });
      console.log('');
    }
  } catch (err) {
    console.error(`\n Delete Error: ${err.message}\n`);
    process.exit(1);
  }
}

export default deleteMemory;
