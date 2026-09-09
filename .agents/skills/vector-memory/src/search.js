import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { getTable, resolveTableName, getDatabase } from './db.js';
import { getEmbedding } from './embedder.js';
import { CONFIG, TABLE_NAMES } from './config.js';

/**
 * Map raw category and metadata to 3-category taxonomy: procedural, declarative, episodic.
 * @param {string} rawCategory
 * @param {Object} metadata
 * @returns {'procedural'|'declarative'|'episodic'}
 */
export function resolveTaxonomyCategory(rawCategory = '', metadata = {}) {
  if (metadata.memory_type) {
    const mt = String(metadata.memory_type).toLowerCase();
    if (mt === 'procedural' || mt === 'declarative' || mt === 'episodic') return mt;
  }

  const cat = String(rawCategory).toLowerCase();
  if (
    cat === 'procedural' ||
    cat === 'learned-instinct' ||
    cat === 'best-practice' ||
    cat === 'pattern' ||
    cat === 'agent-tip'
  ) {
    return 'procedural';
  }
  if (
    cat === 'episodic' ||
    cat === 'error-handling' ||
    cat === 'bug-fix' ||
    cat === 'workaround' ||
    cat === 'troubleshooting'
  ) {
    return 'episodic';
  }
  // Default to declarative for architecture, schemas, domain rules, conventions
  return 'declarative';
}

/**
 * Compute trust score based on taxonomy and metadata:
 * - Procedural: CLv2 confidence (0.7 to 0.95)
 * - Declarative: 1.0 (verified durable invariant)
 * - Episodic: 0.5 if unconfirmed (1st sight candidate), 1.0 if confirmed
 * @param {string} categoryType
 * @param {Object} metadata
 * @returns {number}
 */
export function computeTrustScore(categoryType, metadata = {}) {
  if (categoryType === 'procedural') {
    const conf = typeof metadata.confidence === 'number' ? metadata.confidence : 0.85;
    return Number(Math.min(1.0, Math.max(0.1, conf)).toFixed(4));
  }
  if (categoryType === 'episodic') {
    return metadata.trust_state === 'unconfirmed' ? 0.5 : 1.0;
  }
  return 1.0;
}

/**
 * Compute category-specific freshness weight:
 * - Declarative: flat ~1.0 (schemas don't rot merely from time passing)
 * - Procedural: flat ~1.0 (decay handled natively by CLv2 confidence lifecycle)
 * - Episodic: steep exponential temporal decay with 30-day half-life
 * @param {string} categoryType
 * @param {string} dateStr
 * @param {number} [halfLifeDays=30]
 * @returns {number}
 */
export function computeFreshnessWeight(categoryType, dateStr, halfLifeDays = 30) {
  if (categoryType === 'declarative' || categoryType === 'procedural') {
    return 1.0;
  }

  if (!dateStr) return 1.0;
  const recordDate = new Date(dateStr).getTime();
  if (isNaN(recordDate)) return 1.0;

  const now = Date.now();
  const deltaDays = Math.max(0, (now - recordDate) / (1000 * 60 * 60 * 24));
  const lambda = Math.LN2 / halfLifeDays; // ~0.0231
  const freshness = Math.exp(-lambda * deltaDays);

  return Number(Math.max(0.1, Math.min(1.0, freshness)).toFixed(4));
}

/**
 * Execute vector similarity search on a memory table with trust and freshness ranking.
 * @param {Object} options
 * @param {string} [options.table] - 'project_memory', 'default_memory', or 'all'
 * @param {string} options.query - Text to search
 * @param {number} [options.limit=5] - Number of top results
 * @param {string} [options.category] - Filter by category
 * @param {number} [options.minScore=0.0] - Minimum final rank score threshold
 * @returns {Promise<Array<Object>>}
 */
export async function search(options = {}) {
  const {
    table: rawTable = TABLE_NAMES.DEFAULT,
    query,
    limit = CONFIG.search.defaultLimit,
    category = null,
    minScore = 0.0,
  } = options;

  if (!query || typeof query !== 'string' || query.trim().length === 0) {
    throw new Error('A valid "query" string is required to perform vector search.');
  }

  // Check if searching across all tables
  const isAllTables = rawTable === 'all' || rawTable === 'both';
  const targetTables = isAllTables
    ? [TABLE_NAMES.PROJECT, TABLE_NAMES.DEFAULT]
    : [resolveTableName(rawTable)];

  const queryVector = await getEmbedding(query.trim());
  const allResults = [];

  for (const tableName of targetTables) {
    try {
      const tbl = await getTable(tableName);
      const rowCount = await tbl.countRows();
      if (rowCount === 0) continue;

      let searchBuilder = tbl.vectorSearch(queryVector).distanceType('cosine').limit(limit * 2);

      if (category && typeof category === 'string' && category.trim().length > 0) {
        const escapedCat = category.trim().replace(/'/g, "''");
        searchBuilder = searchBuilder.filter(`category = '${escapedCat}'`);
      }

      const rows = await searchBuilder.toArray();

      for (const row of rows) {
        const distance = row._distance ?? 1;
        // Cosine similarity = 1 - distance (clamped 0 to 1)
        const similarity = Number(Math.max(0, 1 - distance).toFixed(4));

        let parsedMeta = {};
        try {
          parsedMeta = JSON.parse(row.metadata || '{}');
        } catch {
          parsedMeta = { raw: row.metadata };
        }

        const memoryType = resolveTaxonomyCategory(row.category, parsedMeta);
        const trustScore = computeTrustScore(memoryType, parsedMeta);
        const freshnessWeight = computeFreshnessWeight(memoryType, row.updatedAt || row.createdAt);

        // Unified Trust Gate Formula: Rank = Similarity * Trust * Freshness
        const rankScore = Number((similarity * trustScore * freshnessWeight).toFixed(4));

        if (rankScore < minScore) continue;

        allResults.push({
          id: row.id,
          title: row.title,
          content: row.content,
          category: row.category,
          memoryType,
          metadata: parsedMeta,
          similarity,
          trustScore,
          freshnessWeight,
          rankScore,
          score: rankScore, // backward compatibility
          distance: Number(distance.toFixed(4)),
          table: tableName,
          updatedAt: row.updatedAt,
        });
      }
    } catch (err) {
      console.warn(`[Warning] Failed searching table "${tableName}": ${err.message}`);
    }
  }

  // Sort combined results by rankScore descending
  allResults.sort((a, b) => b.rankScore - a.rankScore);

  return allResults.slice(0, limit);
}

// CLI Execution Support
const isDirectExecution = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];

if (isDirectExecution) {
  try {
    const { values, positionals } = parseArgs({
      options: {
        table: { type: 'string', short: 't', default: TABLE_NAMES.DEFAULT },
        query: { type: 'string', short: 'q' },
        limit: { type: 'string', short: 'l', default: String(CONFIG.search.defaultLimit) },
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
  node search.js [options] [query]

Options:
  -q, --query <text>       Search query (or provide as first positional argument)
  -t, --table <name>       Target table: 'default_memory' (default), 'project_memory', or 'all'
  -a, --all                Search across both tables
  -l, --limit <num>        Maximum results to return (default: 5)
  -c, --category <cat>     Filter by category (e.g. 'schema', 'feature-tree', 'best-practice')
  --json                   Output pure JSON for programmatic parsing
  -h, --help               Show help

Examples:
  node search.js "Zod request validation"
  node search.js "chart of accounts schema" --table project_memory
  node search.js "accounting features" --table project_memory --category feature-tree
      `);
      process.exit(0);
    }

    // Positional query support: node search.js "query"
    let query = values.query;
    if (!query && positionals.length > 0) {
      query = positionals.join(' ');
    }

    if (!query) {
      console.error('Error: Please provide a query string. E.g. node search.js "search query"');
      process.exit(1);
    }

    const tableToSearch = values.all ? 'all' : values.table;
    const limit = parseInt(values.limit, 10) || CONFIG.search.defaultLimit;

    const results = await search({
      table: tableToSearch,
      query,
      limit,
      category: values.category,
    });

    if (values.json) {
      console.log(JSON.stringify(results, null, 2));
    } else {
      console.log(`\n Vector Search Results (${results.length} found for: "${query}"):`);
      console.log(`Target: ${tableToSearch}\n` + '='.repeat(60));

      if (results.length === 0) {
        console.log('No relevant memory records found.');
      } else {
        results.forEach((item, index) => {
          console.log(`\n[#${index + 1}] ${item.title}`);
          console.log(`  Table:    ${item.table} | Type: ${item.memoryType} (${item.category})`);
          console.log(
            `  Rank:     ${item.rankScore} (Sim: ${item.similarity} | Trust: ${item.trustScore} | Freshness: ${item.freshnessWeight})`
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
  } catch (err) {
    console.error(`\n Search Error: ${err.message}\n`);
    process.exit(1);
  }
}

export default search;
