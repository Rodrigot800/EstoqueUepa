import { test } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { createApp } from '../src/app.js';
import { createChangeFeed } from '../src/events.js';
import { migrate } from '../src/db.js';

async function stream(url) {
  const controller = new AbortController();
  const response = await fetch(url, { signal: controller.signal });
  assert.equal(response.status, 200);
  assert.match(response.headers.get('content-type'), /text\/event-stream/);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  const queue = [], waiting = [];
  function deliver(item) {
    const index = waiting.findIndex(w => w.type === item.type);
    if (index < 0) queue.push(item);
    else { const [w] = waiting.splice(index, 1); clearTimeout(w.timer); w.resolve(item.data); }
  }
  const reader = response.body.getReader();
  const read = (async () => {
    const decoder = new TextDecoder(); let buffer = '';
    try {
      while (true) {
        const {value,done} = await reader.read(); if(done) break;
        buffer += decoder.decode(value, {stream:true});
        let end;
        while ((end = buffer.indexOf('\n\n')) >= 0) {
          const frame = buffer.slice(0,end); buffer = buffer.slice(end+2);
          const type = frame.split('\n').find(line => line.startsWith('event: '))?.slice(7);
          const payload = frame.split('\n').find(line => line.startsWith('data: '))?.slice(6);
          if(type && payload) deliver({type,data:JSON.parse(payload)});
        }
      }
    } catch (error) { if (!controller.signal.aborted) throw error; }
  })();
  return {
    next(type) {
      const index = queue.findIndex(item => item.type === type);
      if (index >= 0) return Promise.resolve(queue.splice(index,1)[0].data);
      return new Promise((resolve,reject) => {
        const w = {type,resolve};
        w.timer = setTimeout(() => { waiting.splice(waiting.indexOf(w),1); reject(new Error(`Evento ${type} não recebido`)); },5000);
        waiting.push(w);
      });
    },
    async close() { controller.abort(); for(const w of waiting) clearTimeout(w.timer); await read; },
  };
}

test('notificações após commit chegam a clientes de duas APIs e recuperam conexão', {skip: !(process.env.DATABASE_URL || process.env.PGHOST)}, async t => {
  const schema = `events_${Date.now()}`, applicationName = `${schema}_listeners`;
  const admin = new pg.Pool({connectionString:process.env.DATABASE_URL});
  await admin.query(`CREATE SCHEMA ${schema}`);
  const options = {connectionString:process.env.DATABASE_URL,options:`-c search_path=${schema}`,connectionTimeoutMillis:2000};
  const db = new pg.Pool(options), listenerDb = new pg.Pool({...options,application_name:applicationName});
  const feeds = [], servers = [], clients = [];
  try {
    await migrate(db);
    for(let i=0;i<2;i++) {
      const feed = createChangeFeed(listenerDb, {retryMs:100}); feeds.push(feed); await feed.start();
      const server = createApp(db,feed).listen(0,'127.0.0.1'); servers.push(server);
      await new Promise(resolve => server.once('listening',resolve));
      const client = await stream(`http://127.0.0.1:${server.address().port}/api/events`); clients.push(client);
      assert.equal((await client.next('ready')).online,true);
    }
    const both = type => Promise.all(clients.map(c => c.next(type)));
    await t.test('cadastros pela API notificam todos os clientes', async () => {
      const response = await fetch(`http://127.0.0.1:${servers[0].address().port}/api/warehouses`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'ADM'})});
      assert.equal(response.status,201);
      assert.deepEqual(await both('change'),[{table:'warehouses'},{table:'warehouses'}]);
    });
    await t.test('SQL direto também notifica; rollback não publica dados', async () => {
      await db.query("INSERT INTO products(name,unit,minimum) VALUES ('Papel','UN',0)");
      assert.deepEqual(await both('change'),[{table:'products'},{table:'products'}]);
      const c = await db.connect();
      try {
        await c.query('BEGIN');
        await c.query("INSERT INTO movements(product_id,type,quantity) VALUES (1,'ENTRADA',3)");
        // A later committed notification must arrive before any uncommitted movement.
        await db.query('SELECT pg_notify($1,$2)', ['estoque_changes',JSON.stringify({schema,table:'barrier'})]);
        assert.deepEqual(await both('change'),[{table:'barrier'},{table:'barrier'}]);
        await c.query('ROLLBACK');
      } finally { c.release(); }
      await db.query("UPDATE products SET minimum=2 WHERE id=1");
      assert.deepEqual(await both('change'),[{table:'products'},{table:'products'}]);
      assert.equal((await db.query('SELECT count(*)::int AS n FROM movements')).rows[0].n,0);
    });
    await t.test('LISTEN reconecta após perda da conexão e solicita nova leitura', async () => {
      await db.query('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE application_name=$1', [applicationName]);
      assert.deepEqual(await both('status'),[{online:false},{online:false}]);
      assert.deepEqual(await both('ready'),[{online:true},{online:true}]);
      await db.query("INSERT INTO movements(product_id,type,quantity) VALUES (1,'ENTRADA',2)");
      assert.deepEqual(await both('change'),[{table:'movements'},{table:'movements'}]);
    });
  } finally {
    for(const client of clients) await client.close();
    for(const feed of feeds) feed.close();
    for(const server of servers) await new Promise(resolve => server.close(resolve));
    await listenerDb.end(); await db.end();
    await admin.query(`DROP SCHEMA ${schema} CASCADE`); await admin.end();
  }
});
