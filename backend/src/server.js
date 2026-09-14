import { pool, migrate } from './db.js';
import { createApp } from './app.js';
import { createChangeFeed } from './events.js';
await migrate();
const events = createChangeFeed(pool);
await events.start();
const server = createApp(pool, events).listen(process.env.PORT || 3000, '0.0.0.0', () => console.log('API de estoque disponível na porta 3000'));
for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, () => {
  events.close();
  server.close(async () => { await pool.end(); process.exit(0); });
});
