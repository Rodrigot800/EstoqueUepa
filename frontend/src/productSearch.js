const normalize = value => value.normalize('NFD').replace(/\p{M}/gu, '').toLocaleLowerCase('pt-BR').trim();

function distance(a, b) {
  let row = Array.from({length: b.length + 1}, (_, i) => i);
  for (let i = 0; i < a.length; i++) {
    const next = [i + 1];
    for (let j = 0; j < b.length; j++) next.push(Math.min(next[j] + 1, row[j + 1] + 1, row[j] + (a[i] === b[j] ? 0 : 1)));
    row = next;
  }
  return row[b.length];
}

export function suggestProducts(products, query) {
  const term = normalize(query);
  return products.map(product => {
    const name = normalize(product.name);
    let score = 0;
    if (term && name !== term) {
      if (name.startsWith(term)) score = 1;
      else if (name.split(/\s+/).some(word => word.startsWith(term))) score = 2;
      else if (name.includes(term)) score = 3;
      else {
        const difference = Math.min(...[name, ...name.split(/\s+/)].map(word => distance(term, word)));
        score = difference <= Math.max(1, Math.floor(term.length / 3)) && term.length >= 3 ? 4 + difference : Infinity;
      }
    }
    return {product, score};
  }).filter(item => Number.isFinite(item.score))
    .sort((a, b) => a.score - b.score || a.product.name.localeCompare(b.product.name, 'pt-BR') || a.product.id - b.product.id)
    .slice(0, 4).map(item => item.product);
}
