import test from 'node:test';
import assert from 'node:assert/strict';
import {suggestProducts} from '../src/productSearch.js';
const products = ['Papel toalha','Papel A4','Papel','Papel carbono','Papel vegetal','Caixa de papel','Álcool gel','Arroz'].map((name,index) => ({id:index+1,name}));
test('prioriza nome exato e limita a quatro sugestões sem alterar o catálogo', () => {
  const original = structuredClone(products);
  assert.deepEqual(suggestProducts(products,'papel').map(p=>p.name), ['Papel','Papel A4','Papel carbono','Papel toalha']);
  assert.deepEqual(products, original);
});
test('ignora acentos, caixa e espaços e tolera pequenos erros de digitação', () => {
  assert.equal(suggestProducts(products,' ALCOOL ')[0].name,'Álcool gel');
  assert.equal(suggestProducts(products,'aroz')[0].name,'Arroz');
});
test('não sugere nomes sem correspondência e usa apenas o estoque fornecido', () => {
  assert.deepEqual(suggestProducts(products,'parafuso'),[]);
  assert.deepEqual(suggestProducts([], 'papel'),[]);
  assert.equal(suggestProducts(products,'').length,4);
});
