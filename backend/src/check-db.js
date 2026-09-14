import { pool } from './db.js';
try {
  const { rows } = await pool.query('SELECT current_database() AS database, current_user AS username');
  console.log(`Conexão autenticada: banco ${rows[0].database}, usuário ${rows[0].username}.`);
} catch (error) {
  console.error(`Falha na conexão (${error.code || 'desconhecido'}). Confira host, porta e senha configurados.`);
  process.exitCode = 1;
} finally { await pool.end(); }
