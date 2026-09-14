import { z } from 'zod';
export const integer = z.number().int().min(0).max(2147483647);
export const warehouse = z.object({ name: z.string().trim().min(1).max(100) });
export const warehouseQuery = z.object({ warehouseId: z.string().regex(/^[1-9]\d*$/).transform(Number).pipe(integer.positive()) });
export const product = z.object({ name: z.string().trim().min(1).max(180), unit: z.string().trim().min(1).max(30), minimum: integer });
export const productBatch = z.object({ products: z.array(product).min(1).max(100) });
export const productUpdate = product;
export const movementBatch = z.object({ movements: z.array(z.object({ productId: integer.positive(), type: z.enum(['ENTRADA', 'SAIDA']), quantity: integer.positive() })).min(1).max(100) });
export const movementUpdate = z.object({ type: z.enum(['ENTRADA', 'SAIDA']), quantity: integer.positive() });
const date = z.string().regex(/^\d{4}-\d{2}-\d{2}$/).refine(v => !Number.isNaN(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v);
export const filters = z.object({ from: date.optional(), to: date.optional(), type: z.enum(['ENTRADA', 'SAIDA']).optional(), productId: z.coerce.number().int().positive().optional() }).refine(v => !v.from || !v.to || v.from <= v.to, { message: 'A data inicial deve ser anterior à final.' });
export class HttpError extends Error { constructor(status, message) { super(message); this.status = status; } }
