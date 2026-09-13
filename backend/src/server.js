import { pool, migrate } from './db.js';
import { createApp } from './app.js';
await migrate();
const server = createApp(pool).listen(process.env.PORT || 3000, '0.0.0.0', () => console.log('API de estoque disponível na porta 3000'));
for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, () => server.close(async () => { await pool.end(); process.exit(0); }));
