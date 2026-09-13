import { readLegacy } from './legacy.js';
import { pool, migrate, transaction } from './db.js';
const args = process.argv.slice(2), path = args.find(a => !a.startsWith('--'));
try {
  if (!path) throw new Error('Uso: npm run import -w backend -- /caminho/estoque.xlsx [--dry-run]');
  const data = await readLegacy(path);
  console.log(JSON.stringify({ products: data.products.length, movements: data.movements.length, warnings: data.warnings }, null, 2));
  if (!args.includes('--dry-run')) {
    await migrate();
    await transaction(pool, async c => {
      await c.query('LOCK TABLE products, movements IN ACCESS EXCLUSIVE MODE');
      if ((await c.query('SELECT 1 FROM products UNION ALL SELECT 1 FROM movements LIMIT 1')).rowCount) throw new Error('Importação permitida somente em banco vazio para evitar duplicações.');
      for (const p of data.products) await c.query('INSERT INTO products(id,name,unit,minimum) VALUES ($1,$2,$3,$4)', [p.id,p.name,p.unit,p.minimum]);
      for (const m of data.movements) await c.query('INSERT INTO movements(id,product_id,type,quantity,occurred_at) VALUES ($1,$2,$3,$4,$5)', [m.id,m.productId,m.type,m.quantity,m.date]);
      for (const table of ['products','movements']) await c.query(`SELECT setval(pg_get_serial_sequence('${table}','id'), COALESCE(max(id),1), max(id) IS NOT NULL) FROM ${table}`);
    });
    console.log('Importação concluída.');
  }
} catch (error) { console.error(error.message); process.exitCode = 1; }
finally { await pool.end(); }
