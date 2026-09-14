import { test } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { createApp } from '../src/app.js';
import { migrate } from '../src/db.js';
import { productBatch, movementBatch, filters } from '../src/validation.js';

test('valida nomes, unidades, inteiros positivos e períodos reais', () => {
  assert.throws(() => productBatch.parse({products:[{name:' ',unit:'UN',minimum:0}]}));
  for (const quantity of [0,-1,1.5,'2',2147483648]) assert.throws(() => movementBatch.parse({movements:[{productId:1,type:'ENTRADA',quantity}]}));
  assert.throws(() => filters.parse({from:'2026-02-30'}));
  assert.throws(() => filters.parse({from:'2026-03-02',to:'2026-03-01'}));
});

test('fluxo de estoque com PostgreSQL real', { skip: !(process.env.DATABASE_URL || process.env.PGHOST) }, async t => {
  const schema = `test_${Date.now()}`;
  const admin = new pg.Pool({connectionString:process.env.DATABASE_URL});
  await admin.query(`CREATE SCHEMA ${schema}`);
  const db = new pg.Pool({connectionString:process.env.DATABASE_URL,options:`-c search_path=${schema} -c timezone=America/Belem`});
  let server;
  try {
    await migrate(db);
    server = createApp(db).listen(0, '127.0.0.1');
    await new Promise(resolve => server.once('listening',resolve));
    const base = `http://127.0.0.1:${server.address().port}/api/`;
    async function request(route,body,warehouseId=1) { if (route.startsWith('products') || route.startsWith('movements')) { if(body) body={warehouseId,...body}; else route += (route.includes('?') ? '&' : '?') + `warehouseId=${warehouseId}`; } const r = await fetch(base+route,body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {}); return {status:r.status,data:await r.json()}; }
    let id;
    await t.test('cadastro, saldo inicial e rejeição de duplicatas sem salvar lote parcial', async () => {
      const created = await request('products',{products:[{name:'Papel A4',unit:'RESMA',minimum:5}]});
      assert.equal(created.status,201); id=created.data[0].id;
      assert.equal((await request('products')).data[0].stock,0);
      assert.equal((await request('products',{products:[{name:'Caneta',unit:'UN',minimum:0},{name:' papel a4 ',unit:'UN',minimum:0}]})).status,409);
      assert.equal((await request('products')).data.length,1);
    });
    const move = (type,quantity,productId=id) => ({productId,type,quantity});
    await t.test('lote com entrada e saída e rollback por saldo insuficiente', async () => {
      assert.equal((await request('movements',{movements:[move('ENTRADA',10),move('SAIDA',3)]})).status,201);
      assert.equal((await request('products')).data[0].stock,7);
      assert.equal((await request('movements',{movements:[move('ENTRADA',1),move('SAIDA',20)]})).status,409);
      assert.equal((await request('products')).data[0].stock,7);
      assert.equal((await request('movements')).data.length,2);
      assert.equal((await request('movements',{movements:[move('ENTRADA',1,999999)]})).status,404);
    });
    await t.test('saídas concorrentes não consomem o mesmo saldo', async () => {
      const results = await Promise.all([request('movements',{movements:[move('SAIDA',5)]}),request('movements',{movements:[move('SAIDA',5)]})]);
      assert.deepEqual(results.map(r=>r.status).sort(),[201,409]);
      assert.equal((await request('products')).data[0].stock,2);
    });
    await t.test('estoques isolam catálogo, histórico, saldos e nomes duplicados', async () => {
      assert.equal((await request('warehouses',{name:'  '})).status,400);
      const adm = await request('warehouses',{name:'ADM'});
      const ioom = await request('warehouses',{name:'IOOM'});
      assert.equal(adm.status,201); assert.equal(ioom.status,201);
      assert.equal((await request('warehouses',{name:' adm '})).status,409);
      assert.equal((await request('warehouses')).data.length,3);
      const payload = {products:[{name:'Papel A4',unit:'RESMA',minimum:1}]};
      const a = await request('products',payload,adm.data.id);
      const b = await request('products',payload,ioom.data.id);
      assert.equal(a.status,201); assert.equal(b.status,201);
      assert.equal((await request('products',payload,adm.data.id)).status,409);
      assert.equal((await request('movements',{movements:[move('ENTRADA',8,a.data[0].id)]},adm.data.id)).status,201);
      // Even a forged product ID from a different warehouse is rejected atomically.
      assert.equal((await request('movements',{movements:[move('ENTRADA',1,a.data[0].id),move('ENTRADA',10,b.data[0].id)]},adm.data.id)).status,404);
      assert.equal((await request('products',undefined,adm.data.id)).data[0].stock,8);
      assert.equal((await request('products',undefined,ioom.data.id)).data[0].stock,0);
      assert.equal((await request('products')).data[0].stock,2);
      assert.equal((await request('movements',undefined,adm.data.id)).data.length,1);
      assert.equal((await request('movements',undefined,ioom.data.id)).data.length,0);
      assert.equal((await request(`movements?productId=${b.data[0].id}`,undefined,adm.data.id)).data.length,0);
      assert.equal((await request('products',payload,999999)).status,404);
      assert.equal((await fetch(base+'products')).status,400);
      assert.equal((await request('products',undefined,'abc')).status,400);
      // Startup is repeatable after duplicate product names exist in different warehouses.
      await migrate(db);
      assert.equal((await request('products',undefined,adm.data.id)).data[0].stock,8);
      const next = await request('warehouses',{name:'Laboratório'});
      assert.ok(next.data.id > ioom.data.id);
    });
    await t.test('filtros incluem o dia final inteiro no horário de Belém', async () => {
      await db.query("INSERT INTO movements(product_id,type,quantity,occurred_at) VALUES ($1,'ENTRADA',1,'2026-02-27T02:59:59Z'),($1,'ENTRADA',1,'2026-02-27T03:00:00Z')",[id]);
      const r = await request('movements?from=2026-02-26&to=2026-02-26&type=ENTRADA');
      assert.equal(r.status,200); assert.equal(r.data.length,1);
      assert.equal((await request('movements?from=2026-02-30')).status,400);
    });
  } finally {
    if(server) await new Promise(resolve => server.close(resolve));
    await db.end(); await admin.query(`DROP SCHEMA ${schema} CASCADE`); await admin.end();
  }
});
