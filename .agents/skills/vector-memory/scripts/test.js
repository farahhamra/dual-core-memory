import { save, search, deleteMemory, getTableStats, initializeTables, TABLE_NAMES } from '../src/index.js';

async function runTests() {
  console.log('====================================================');
  console.log(' Starting Antigravity Vector Memory Subsystem Tests');
  console.log('====================================================\n');

  // 1. Initialize Tables
  console.log('[Step 1] Initializing LanceDB tables...');
  await initializeTables();
  let stats = await getTableStats();
  console.log('Tables initialized:', stats.map((s) => `${s.name} (${s.count} rows)`).join(', '));

  // 2. Save test entries to project_memory
  console.log('\n[Step 2] Saving test records to project_memory...');
  const projEntry1 = await save({
    table: TABLE_NAMES.PROJECT,
    id: 'test-db-structure-001',
    title: 'PostgreSQL Chart of Accounts Prisma Schema',
    content: `
Model Account has hierarchical self-relation:
parentId referencing Account.id.
Types: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE.
Balance calculation requires recursive CTE queries.
    `.trim(),
    category: 'db-schema',
    metadata: { module: 'accounting', database: 'postgresql', orm: 'prisma' },
  });
  console.log(` Saved: [${projEntry1.id}] "${projEntry1.title}"`);

  const projEntry2 = await save({
    table: TABLE_NAMES.PROJECT,
    id: 'test-feature-tree-002',
    title: 'Electro ERP Feature Tree: Sales and Inventory',
    content: `
Sales Module Tree:
  -> Quotations
  -> Sales Orders
  -> Invoices
Inventory Module Tree:
  -> Warehouses
  -> Stock Transfers
  -> Inventory Adjustments
    `.trim(),
    category: 'feature-tree',
    metadata: { module: 'sales-inventory', hierarchy: 'tree' },
  });
  console.log(` Saved: [${projEntry2.id}] "${projEntry2.title}"`);

  // 3. Save test entry to default_memory
  console.log('\n[Step 3] Saving test record to default_memory...');
  const defEntry = await save({
    table: TABLE_NAMES.DEFAULT,
    id: 'test-agent-pattern-001',
    title: 'Standard Pattern: Zod Validation in NestJS/Fastify Endpoints',
    content: `
When implementing API endpoints:
1. Always define request DTO schema with Zod.
2. Use custom ZodValidationPipe.
3. Return RFC 7807 compliant error format with field-level details.
    `.trim(),
    category: 'best-practice',
    metadata: { framework: 'general-api', standard: 'RFC-7807' },
  });
  console.log(` Saved: [${defEntry.id}] "${defEntry.title}"`);

  // 4. Verify table row counts
  stats = await getTableStats();
  console.log('\nUpdated Stats:', stats.map((s) => `${s.name}: ${s.count} rows`).join(' | '));

  // 5. Test semantic vector search on project_memory
  console.log('\n[Step 4] Searching project_memory for: "how is chart of accounts structured?"');
  const coaResults = await search({
    table: TABLE_NAMES.PROJECT,
    query: 'how is chart of accounts structured?',
    limit: 2,
  });

  console.log(`Found ${coaResults.length} results:`);
  coaResults.forEach((r, idx) => {
    console.log(`  ${idx + 1}. [Score: ${r.score}] ${r.title} (Category: ${r.category})`);
  });

  if (coaResults.length === 0 || coaResults[0].id !== 'test-db-structure-001') {
    throw new Error('Test failed: Expected test-db-structure-001 as top result for COA query.');
  }

  // 6. Test semantic search on default_memory
  console.log('\n[Step 5] Searching default_memory for: "validating input request data with Zod"');
  const zodResults = await search({
    table: TABLE_NAMES.DEFAULT,
    query: 'validating input request data with Zod',
    limit: 1,
  });

  console.log(`Found ${zodResults.length} results:`);
  zodResults.forEach((r, idx) => {
    console.log(`  ${idx + 1}. [Score: ${r.score}] ${r.title}`);
  });

  if (zodResults.length === 0 || zodResults[0].id !== 'test-agent-pattern-001') {
    throw new Error('Test failed: Expected test-agent-pattern-001 as top result for Zod query.');
  }

  // 7. Test category filtered search
  console.log('\n[Step 6] Testing category filter (category = "feature-tree")...');
  const catResults = await search({
    table: TABLE_NAMES.PROJECT,
    query: 'inventory warehouses and quotations',
    category: 'feature-tree',
    limit: 2,
  });

  console.log(`Found ${catResults.length} filtered results:`);
  catResults.forEach((r, idx) => {
    console.log(`  ${idx + 1}. [Score: ${r.score}] ${r.title} (Category: ${r.category})`);
  });

  if (catResults.length === 0 || catResults[0].category !== 'feature-tree') {
    throw new Error('Test failed: Category filter did not properly restrict results.');
  }

  // 8. Test cross-table search ('all')
  console.log('\n[Step 7] Testing cross-table search across all tables...');
  const allResults = await search({
    table: 'all',
    query: 'database schema structure',
    limit: 3,
  });
  console.log(`Cross-table found ${allResults.length} results.`);

  // 9. Cleanup: Delete test records
  console.log('\n[Step 8] Cleaning up test records...');
  await deleteMemory({ table: TABLE_NAMES.PROJECT, id: 'test-db-structure-001' });
  await deleteMemory({ table: TABLE_NAMES.PROJECT, id: 'test-feature-tree-002' });
  await deleteMemory({ table: TABLE_NAMES.DEFAULT, id: 'test-agent-pattern-001' });

  const finalStats = await getTableStats();
  console.log('Final row counts:', finalStats.map((s) => `${s.name}: ${s.count}`).join(', '));

  console.log('\n====================================================');
  console.log(' ALL TESTS PASSED SUCCESSFULLY! ');
  console.log('====================================================\n');
}

runTests().catch((err) => {
  console.error('\nTest Execution Failed:', err);
  process.exit(1);
});
