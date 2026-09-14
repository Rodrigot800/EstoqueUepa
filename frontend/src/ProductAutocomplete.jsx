import { useId, useState } from 'react';
import { suggestProducts } from './productSearch.js';

export default function ProductAutocomplete({products, query, onQuery, onSelect}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const suggestions = suggestProducts(products, query);
  const selected = active < suggestions.length ? active : -1;
  function choose(product) { onSelect(product); setOpen(false); setActive(-1); }
  function keyDown(event) {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault(); setOpen(true);
      setActive(suggestions.length ? (selected + (event.key === 'ArrowDown' ? 1 : -1) + suggestions.length) % suggestions.length : -1);
    } else if (event.key === 'Enter' && open) {
      event.preventDefault();
      if (suggestions[selected >= 0 ? selected : 0]) choose(suggestions[selected >= 0 ? selected : 0]);
    } else if (event.key === 'Escape' && open) {
      event.preventDefault(); event.stopPropagation(); setOpen(false);
    }
  }
  return <div className="product-autocomplete">
    <label htmlFor={id}>Produto</label>
    <input id={id} autoFocus required maxLength={180} autoComplete="off" placeholder="Digite o nome do produto" value={query}
      role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls={`${id}-list`}
      aria-activedescendant={open && selected >= 0 ? `${id}-option-${selected}` : undefined}
      onChange={event => { onQuery(event.target.value); setOpen(true); setActive(-1); }}
      onFocus={() => setOpen(true)} onBlur={() => { setOpen(false); setActive(-1); }} onKeyDown={keyDown}/>
    {open && <div className="product-suggestions">
      <ul id={`${id}-list`} role="listbox" aria-label="Produtos sugeridos">
        {suggestions.map((product, index) => <li key={product.id} id={`${id}-option-${index}`} role="option" aria-selected={selected === index}
          onMouseDown={event => event.preventDefault()} onClick={() => choose(product)}>
          <strong>{product.name}</strong><small>Saldo: {Number(product.stock).toLocaleString('pt-BR')} {product.unit}</small>
        </li>)}
      </ul>
      {!suggestions.length && <p role="status">Nenhum produto encontrado neste estoque.</p>}
    </div>}
  </div>;
}
