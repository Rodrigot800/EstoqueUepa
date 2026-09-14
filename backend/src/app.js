import express from 'express';
import helmet from 'helmet';
import { ZodError } from 'zod';
import { transaction } from './db.js';
import { productBatch, movementBatch, filters, HttpError, warehouse, warehouseQuery, integer } from './validation.js';

export function createApp(db, events) {
  const app = express();
  app.use(helmet());
  app.use(express.json({ limit: '128kb' }));
  app.use('/api', (_req, res, next) => { res.set('Cache-Control', 'no-store'); next(); });
  app.get('/api/events', (req, res) => {
    if (!events) return res.status(503).json({ error: 'Atualização em tempo real indisponível.' });
    events.subscribe(req, res);
  });
  app.get('/api/health', async (_req, res) => { await db.query('SELECT 1'); res.json({ status: 'ok' }); });
  app.get('/api/warehouses', async (_req, res) => {
    res.json((await db.query('SELECT * FROM warehouses ORDER BY lower(name),id')).rows);
  });
  app.post('/api/warehouses', async (req, res) => {
    const { name } = warehouse.parse(req.body);
    res.status(201).json((await db.query('INSERT INTO warehouses(name) VALUES ($1) RETURNING *', [name])).rows[0]);
  });
  app.use(['/api/products', '/api/movements'], async (req, _res, next) => {
    req.warehouseId = req.method === 'GET' ? warehouseQuery.parse(req.query).warehouseId : integer.positive().parse(req.body?.warehouseId);
    if (!(await db.query('SELECT id FROM warehouses WHERE id=$1', [req.warehouseId])).rowCount) throw new HttpError(404, 'Estoque não encontrado.');
    next();
  });
  app.get('/api/products', async (req, res) => {
    const { rows } = await db.query(`SELECT p.*, COALESCE(sum(CASE WHEN m.type='ENTRADA' THEN m.quantity::bigint ELSE -m.quantity::bigint END),0)::float8 AS stock
      FROM products p LEFT JOIN movements m ON m.product_id=p.id WHERE p.warehouse_id=$1 GROUP BY p.id ORDER BY lower(p.name), p.id`, [req.warehouseId]);
    res.json(rows);
  });
  app.post('/api/products', async (req, res) => {
    const { products } = productBatch.parse(req.body);
    const result = await transaction(db, async c => {
      const rows = [];
      for (const p of products) rows.push((await c.query('INSERT INTO products(name,unit,minimum,warehouse_id) VALUES ($1,$2,$3,$4) RETURNING *', [p.name, p.unit, p.minimum, req.warehouseId])).rows[0]);
      return rows;
    });
    res.status(201).json(result);
  });
  app.post('/api/movements', async (req, res) => {
    const { movements } = movementBatch.parse(req.body);
    const result = await transaction(db, async c => {
      // Lock products in a stable order; concurrent withdrawals cannot consume the same stock.
      const ids = [...new Set(movements.map(m => m.productId))].sort((a,b) => a-b);
      const locked = await c.query('SELECT id,name FROM products WHERE id=ANY($1::int[]) AND warehouse_id=$2 ORDER BY id FOR UPDATE', [ids, req.warehouseId]);
      if (locked.rowCount !== ids.length) throw new HttpError(404, 'Produto não encontrado neste estoque.');
      const balances = await c.query(`SELECT product_id, sum(CASE WHEN type='ENTRADA' THEN quantity::bigint ELSE -quantity::bigint END)::float8 AS stock FROM movements WHERE product_id=ANY($1::int[]) GROUP BY product_id`, [ids]);
      const stock = new Map(balances.rows.map(r => [r.product_id, r.stock]));
      const rows = [];
      for (const m of movements) {
        const balance = (stock.get(m.productId) ?? 0) + (m.type === 'ENTRADA' ? m.quantity : -m.quantity);
        if (balance < 0) throw new HttpError(409, `Saldo insuficiente para ${locked.rows.find(p => p.id === m.productId).name}. Nenhuma movimentação foi registrada.`);
        stock.set(m.productId, balance);
        rows.push((await c.query('INSERT INTO movements(product_id,type,quantity) VALUES ($1,$2,$3) RETURNING *', [m.productId, m.type, m.quantity])).rows[0]);
      }
      return rows;
    });
    res.status(201).json(result);
  });
  app.get('/api/movements', async (req, res) => {
    const f = filters.parse(req.query);
    const { rows } = await db.query(`SELECT m.*, p.name AS product_name, p.unit FROM movements m JOIN products p ON p.id=m.product_id
      WHERE ($1::date IS NULL OR m.occurred_at >= $1::date::timestamp AT TIME ZONE 'America/Belem')
      AND ($2::date IS NULL OR m.occurred_at < ($2::date + 1)::timestamp AT TIME ZONE 'America/Belem')
      AND ($3::text IS NULL OR m.type=$3) AND ($4::int IS NULL OR m.product_id=$4) AND p.warehouse_id=$5
      ORDER BY m.occurred_at DESC,m.id DESC`, [f.from ?? null, f.to ?? null, f.type ?? null, f.productId ?? null, req.warehouseId]);
    res.json(rows);
  });
  app.use((_req, res) => res.status(404).json({ error: 'Rota não encontrada.' }));
  app.use((error, _req, res, _next) => {
    if (error instanceof ZodError) return res.status(400).json({ error: 'Verifique os campos: use nomes e unidades válidos, quantidades inteiras e datas válidas.', details: error.issues });
    if (error.code === '23505') return res.status(409).json({ error: error.constraint === 'warehouses_name_unique' ? 'Já existe um estoque com esse nome.' : 'Já existe um produto com esse nome neste estoque. Nenhum item da lista foi salvo.' });
    if (error.type === 'entity.parse.failed') return res.status(400).json({ error: 'JSON inválido.' });
    if (error.status) return res.status(error.status).json({ error: error.message });
    console.error(error);
    res.status(500).json({ error: 'Não foi possível concluir a operação. Tente novamente.' });
  });
  return app;
}
