import pg from 'pg';
import { readFile } from 'node:fs/promises';
export const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL, options: '-c timezone=America/Belem' });
export async function migrate(db = pool) {
  await db.query(await readFile(new URL('./schema.sql', import.meta.url), 'utf8'));
}
export async function transaction(db, fn) {
  const client = await db.connect();
  try {
    await client.query('BEGIN');
    const result = await fn(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally { client.release(); }
}
