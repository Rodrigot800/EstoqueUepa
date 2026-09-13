import ExcelJS from 'exceljs';
import { product, integer } from './validation.js';
export async function readLegacy(path) {
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.readFile(path);
  const ps = workbook.getWorksheet('produtos'), ms = workbook.getWorksheet('movimentos');
  if (!ps || !ms) throw new Error('A planilha precisa das abas produtos e movimentos.');
  const products = [], movements = [], warnings = [];
  const ids = new Set(), names = new Set(), movementIds = new Set();
  ps.eachRow((row, index) => {
    if (index === 1) return;
    let [, id, name, unit, minimum, savedStock] = row.values;
    // The Python registration dialog wrote (name, minimum, unit) in the opposite order.
    if (/^\d+$/.test(String(unit)) && minimum != null && !/^\d+$/.test(String(minimum))) {
      [unit, minimum] = [minimum, unit];
      warnings.push(`Produto ${id}: colunas Unidade/Qtd_Mínima corrigidas na importação.`);
    }
    id = integer.positive().parse(Number(id));
    const p = product.parse({ name: String(name ?? ''), unit: String(unit ?? ''), minimum: minimum == null || minimum === '' ? NaN : Number(minimum) });
    if (ids.has(id) || names.has(p.name.toLowerCase())) throw new Error(`Produto duplicado na linha ${index}.`);
    ids.add(id); names.add(p.name.toLowerCase());
    products.push({ id, ...p, savedStock });
  });
  ms.eachRow((row, index) => {
    if (index === 1) return;
    const [, rawId, rawProductId, , type, rawQuantity, rawDate] = row.values;
    const id = integer.positive().parse(Number(rawId));
    const productId = integer.positive().parse(Number(rawProductId));
    const quantity = integer.parse(Number(rawQuantity));
    if (!ids.has(productId) || movementIds.has(id) || !['ENTRADA','SAIDA'].includes(type)) throw new Error(`Movimentação inválida na linha ${index}.`);
    movementIds.add(id);
    if (quantity === 0) { warnings.push(`Movimento ${id} com quantidade zero ignorado (não altera saldo).`); return; }
    // Legacy dates are wall-clock times in Belém, even if Excel represents them as Date objects.
    const wall = rawDate instanceof Date ? rawDate.toISOString().slice(0,19) : String(rawDate).replace(' ', 'T');
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(wall)) throw new Error(`Data inválida na linha ${index}.`);
    const date = new Date(`${wall}-03:00`);
    if (Number.isNaN(date.valueOf()) || new Date(date.valueOf()-10800000).toISOString().slice(0,19) !== wall) throw new Error(`Data inválida na linha ${index}.`);
    movements.push({ id, productId, type, quantity, date });
  });
  for (const p of products) {
    const balance = movements.filter(m => m.productId === p.id).reduce((s,m) => s + (m.type === 'ENTRADA' ? m.quantity : -m.quantity), 0);
    if (balance !== Number(p.savedStock)) warnings.push(`Produto ${p.id}: saldo da planilha ${p.savedStock}; saldo pelo histórico ${balance}. Será usado o histórico, como no Python.`);
    if (balance < 0) warnings.push(`Produto ${p.id}: saldo legado negativo (${balance}) preservado.`);
  }
  return { products, movements, warnings };
}
