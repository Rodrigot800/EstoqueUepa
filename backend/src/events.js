// A dedicated LISTEN connection shares committed changes across API instances and browsers.
export function createChangeFeed(db, { retryMs = 2000, heartbeatMs = 20000 } = {}) {
  const subscribers = new Set();
  let client, retry, stopped = false, connecting = false, online = false, schema;
  function send(res, event, data) {
    if (res.destroyed || res.writableEnded) { subscribers.delete(res); return; }
    // A slow client reconnects and fetches a fresh snapshot instead of buffering indefinitely.
    if (!res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)) res.end();
  }
  function broadcast(event, data) { for (const res of subscribers) send(res, event, data); }
  function disconnect(current) {
    if (client !== current) return;
                   client = undefined; online = false;
    current.release(true);
    broadcast('status', { online: false });
    if (!stopped) { clearTimeout(retry); retry = setTimeout(start, retryMs); retry.unref(); }
  }
  async function start() {
    if (stopped || connecting || client) return;
    connecting = true;
    let current;
    try {
      current = await db.connect();
      if (stopped) { current.release(true); return; }
      client = current;
      current.on('error', () => disconnect(current));
      current.on('end', () => disconnect(current));
      current.on('notification', message => {
        if (message.channel !== 'estoque_changes') return;
        try {
          const payload = JSON.parse(message.payload);
          if (payload.schema === schema) broadcast('change', { table: payload.table });
        } catch { /* Ignore malformed notifications from external publishers. */ }
      });
      schema = (await current.query('SELECT current_schema() AS name')).rows[0].name;
      await current.query('LISTEN estoque_changes');
      if (client !== current || stopped) return;
      online = true;
      // Also resynchronize after a database reconnection; notifications are not a durable log.
      broadcast('ready', { online: true });
    } catch (error) {
      if (current && client === current) disconnect(current);
      else if (!stopped) { clearTimeout(retry); retry = setTimeout(start, retryMs); retry.unref(); }
      console.error('Atualização em tempo real indisponível; reconectando.', error.code || 'connection');
    } finally { connecting = false; }
  }
  const heartbeat = setInterval(() => broadcast('status', { online }), heartbeatMs);
  heartbeat.unref();
  return {
    start,
    subscribe(req, res) {
      res.status(200).set({ 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no', Connection: 'keep-alive' });
      res.setTimeout(0); res.flushHeaders();
      res.write('retry: 2000\n\n');
      subscribers.add(res);
      res.on('close', () => subscribers.delete(res));
      send(res, 'ready', { online });
    },
    close() {
      stopped = true; clearTimeout(retry); clearInterval(heartbeat);
      for (const res of subscribers) res.end();
      subscribers.clear();
      if (client) { const current = client; client = undefined; current.release(true); }
    },
  };
}
