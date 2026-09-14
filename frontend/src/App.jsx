import { useEffect, useMemo, useRef, useState } from 'react';
import ProductAutocomplete from './ProductAutocomplete.jsx';
import { Package, LayoutDashboard, ArrowLeftRight, Plus, Search, RefreshCw, ArrowDownLeft, ArrowUpRight, AlertTriangle, X, Trash2, CheckCircle2, Pencil } from 'lucide-react';
import uepaLogo from '../../assets/UepaEstoqueIcone.png';

const number = n => Number(n).toLocaleString('pt-BR');
const date = d => new Date(d).toLocaleString('pt-BR', { timeZone: 'America/Belem' });
async function api(path, body, method = body ? 'POST' : 'GET') {
  const response = await fetch(`/api/${path}`, method === 'GET' ? { cache: 'no-store' } : { method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(data.error || 'Não foi possível carregar os dados.');
  return data;
}
function Status({ p }) { return <span className={`badge ${p.stock <= 0 ? 'danger' : p.stock < p.minimum ? 'warning' : 'success'}`}>{p.stock <= 0 ? 'Sem estoque' : p.stock < p.minimum ? 'Estoque baixo' : 'Disponível'}</span>; }

export default function App() {
  const [warehouses, setWarehouses] = useState([]);
  const [warehouseId, setWarehouseId] = useState(() => { try { return localStorage.getItem('warehouseId') || ''; } catch { return ''; } });
  const activeWarehouse = warehouses.find(w => String(w.id) === String(warehouseId));
  const [page, setPage] = useState('stock'), [products, setProducts] = useState([]), [movements, setMovements] = useState([]);
  const [search, setSearch] = useState(''), [sort, setSort] = useState('name'), [status, setStatus] = useState('all');
  const [filter, setFilter] = useState({ from: '', to: '', type: '', productId: '' });
  const [modal, setModal] = useState(null), [editing, setEditing] = useState(null), [loading, setLoading] = useState(true), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const generation = useRef(0);
  const selectedRef = useRef(warehouseId), busyRef = useRef(false), pendingRef = useRef(false), refreshRef = useRef(null);
  async function refresh(requestedId = selectedRef.current, {quiet = false} = {}) {
    if (quiet && busyRef.current) { pendingRef.current = true; return; }
    const current = ++generation.current;
    busyRef.current = true;
    if (!quiet) { setLoading(true); setError(''); setProducts([]); setMovements([]); }
    try {
      const list = await api('warehouses');
      if (current !== generation.current) return;
      const selected = list.find(w => String(w.id) === String(requestedId)) || list[0];
      if (!selected) throw new Error('Crie um estoque para começar.');
      if (requestedId && String(selected.id) !== String(requestedId)) setModal(null);
      selectedRef.current = String(selected.id);
      setWarehouses(list); setWarehouseId(String(selected.id));
      try { localStorage.setItem('warehouseId', String(selected.id)); } catch { /* Storage may be unavailable. */ }
      const [p,m] = await Promise.all([api(`products?warehouseId=${selected.id}`), api(`movements?warehouseId=${selected.id}`)]);
      if (current === generation.current) { setProducts(p); setMovements(m); setError(''); }
    } catch (e) { if (current === generation.current) setError(e.message || 'Sem conexão com o servidor.'); }
    finally {
      if (current === generation.current) {
        busyRef.current = false; setLoading(false);
        if (pendingRef.current) { pendingRef.current = false; queueMicrotask(() => refreshRef.current(undefined, {quiet: true})); }
      }
    }
  }
  refreshRef.current = refresh;
  useEffect(() => { refresh(); }, []);
  useEffect(() => {
    let timer;
    const schedule = () => {
      if (timer) return;
      timer = setTimeout(() => { timer = undefined; refreshRef.current(undefined, {quiet: true}); }, 150);
    };
    const source = new EventSource('/api/events');
    source.addEventListener('ready', schedule);
    source.addEventListener('change', schedule);
    // Recover missed events after sleep/network loss; polling also works if SSE is blocked.
    const fallback = setInterval(schedule, 15000);
    const onVisible = () => { if (document.visibilityState === 'visible') schedule(); };
    window.addEventListener('online', schedule);
    window.addEventListener('focus', schedule);
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      source.close(); clearTimeout(timer); clearInterval(fallback);
      window.removeEventListener('online', schedule); window.removeEventListener('focus', schedule);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, []);
  function selectWarehouse(id) {
    selectedRef.current = String(id);
    setWarehouseId(String(id)); setSearch(''); setStatus('all'); setSort('name');
    setFilter({ from: '', to: '', type: '', productId: '' }); setModal(null); setNotice('');
    refresh(String(id));
  }
  useEffect(() => { if (notice) { const t = setTimeout(() => setNotice(''), 6000); return () => clearTimeout(t); } }, [notice]);
  const low = products.filter(p => p.stock < p.minimum || p.stock <= 0).length;
  const filteredProducts = useMemo(() => products.filter(p => p.name.toLocaleLowerCase('pt-BR').includes(search.toLocaleLowerCase('pt-BR')) && (status === 'all' || (status === 'low' ? p.stock < p.minimum || p.stock <= 0 : p.stock > 0 && p.stock >= p.minimum))).sort((a,b) => sort === 'name' ? a.name.localeCompare(b.name, 'pt-BR') : sort === 'id' ? a.id-b.id : b.stock-a.stock), [products,search,sort,status]);
  const badRange = filter.from && filter.to && filter.from > filter.to;
  const filteredMovements = movements.filter(m => {
    const day = new Date(m.occurred_at).toLocaleDateString('en-CA', { timeZone: 'America/Belem' });
    return !badRange && m.product_name.toLowerCase().includes(search.toLowerCase()) && (!filter.from || day >= filter.from) && (!filter.to || day <= filter.to) && (!filter.type || m.type === filter.type) && (!filter.productId || m.product_id === Number(filter.productId));
  });
  const month = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Belem' }).slice(0,7);
  const recent = movements.filter(m => new Date(m.occurred_at).toLocaleDateString('en-CA', { timeZone: 'America/Belem' }).startsWith(month));
  const changePage = p => { setPage(p); setSearch(''); };
  async function remove(kind, record) {
    const isProduct = kind === 'product';
    const message = isProduct ? `Excluir “${record.name}” e todo o seu histórico? Esta ação não pode ser desfeita.` : `Excluir a ${record.type === 'ENTRADA' ? 'entrada' : 'saída'} de ${record.product_name}? Esta ação não pode ser desfeita.`;
    if (!window.confirm(message)) return;
    try {
      await api(`${isProduct ? 'products' : 'movements'}/${record.id}`, {warehouseId: activeWarehouse.id}, 'DELETE');
      setNotice(isProduct ? 'Produto e histórico excluídos com sucesso.' : 'Movimentação excluída com sucesso.');
      await refresh();
    } catch (e) { setError(e.message || 'Não foi possível excluir o registro.'); }
  }
  return <div className="shell">
    <aside className="sidebar"><a className="brand" href="#" onClick={e => { e.preventDefault(); changePage('stock'); }}><img className="brand-logo" src={uepaLogo} alt="Estoque UEPA"/><span>Estoque<span className="brand-sub">UEPA</span></span></a>
      <div className="warehouse-picker"><label htmlFor="warehouse-select">ESTOQUE ATUAL</label><select id="warehouse-select" value={warehouseId} onChange={e => selectWarehouse(e.target.value)} disabled={!warehouses.length}>{!warehouses.length && <option value="">Carregando…</option>}{warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}</select><button className="secondary action-blue" onClick={() => setModal('warehouse')}><Plus size={16}/> Adicionar estoque</button></div><p className="nav-label">GESTÃO DE MATERIAIS</p>
      <nav><button className={page === 'stock' ? 'active' : ''} onClick={() => changePage('stock')}><LayoutDashboard size={19}/> Visão do estoque</button><button className={page === 'history' ? 'active' : ''} onClick={() => changePage('history')}><ArrowLeftRight size={19}/> Movimentações</button></nav>
      <div className="sidebar-bottom"><img className="secondary-logo" src={uepaLogo} alt=""/><div>Universidade do Estado do Pará<small>Controle de almoxarifado</small></div></div>
    </aside>
    <div className="workspace"><header className="topbar"><span className="breadcrumb"><span className="warehouse-name" title={activeWarehouse?.name}>{activeWarehouse?.name || 'Almoxarifado'}</span><span className="slash">/</span> <strong>{page === 'stock' ? 'Visão do estoque' : 'Movimentações'}</strong></span><span className="institution">UEPA <img className="avatar" src={uepaLogo} alt=""/></span></header>
    <main><div className="page-heading page-actions"><button className="primary action-blue" onClick={() => setModal('movement')} disabled={loading || !products.length}><ArrowLeftRight size={17}/> Nova movimentação</button></div>
      {error && <div className="message error" role="alert">{error}<button onClick={() => refresh()}>Tentar novamente</button></div>}
      {notice && <div className="message success-message" role="status"><CheckCircle2 size={18}/>{notice}</div>}
      <div className="stats"><Stat title="Produtos cadastrados" value={products.length} label="Materiais no catálogo" icon={<Package/>}/><Stat title="Precisam de atenção" value={low} label="Estoque baixo ou indisponível" icon={<AlertTriangle/>} warm/><Stat title="Entradas neste mês" value={recent.filter(m => m.type === 'ENTRADA').length} label="Movimentações de recebimento" icon={<ArrowDownLeft/>}/><Stat title="Saídas neste mês" value={recent.filter(m => m.type === 'SAIDA').length} label="Movimentações de retirada" icon={<ArrowUpRight/>}/></div>
      {page === 'stock' && low > 0 && <div className="stock-alert"><AlertTriangle size={19}/><span><strong>{low} {low === 1 ? 'produto precisa' : 'produtos precisam'} de atenção.</strong> Confira os itens que precisam de reposição.</span><button className="action-yellow" onClick={() => setStatus('low')}>Ver produtos <ArrowUpRight size={16}/></button></div>}
      <section className="panel"><div className="panel-title"><div><h2>{page === 'stock' ? 'Seus produtos' : 'Entradas e saídas'}</h2><span>{page === 'stock' ? 'Saldos atualizados a cada movimentação.' : 'Registros exibidos do mais recente para o mais antigo.'}</span></div><div className="actions"><button className="icon-button" title="Atualizar dados" aria-label="Atualizar dados" onClick={() => refresh()} disabled={loading}><RefreshCw size={17} className={loading ? 'spinning' : ''}/></button>{page === 'stock' && <button className="secondary action-green" disabled={loading || !activeWarehouse || !!error} onClick={() => setModal('product')}><Plus size={17}/> Cadastrar produtos</button>}</div></div>
        <div className="filters"><label className="search"><Search size={18}/><input aria-label="Pesquisar produto" placeholder="Pesquisar por nome do produto..." value={search} onChange={e => setSearch(e.target.value)}/></label>
          {page === 'stock' ? <><select aria-label="Situação do estoque" value={status} onChange={e => setStatus(e.target.value)}><option value="all">Todas as situações</option><option value="low">Precisam de atenção</option><option value="available">Disponíveis</option></select><select aria-label="Ordenar produtos" value={sort} onChange={e => setSort(e.target.value)}><option value="name">Nome (A–Z)</option><option value="id">Código do produto</option><option value="stock">Maior saldo</option></select></> : <><label className="date-filter">De<input aria-label="Data inicial" type="date" value={filter.from} onChange={e => setFilter({...filter, from: e.target.value})}/></label><label className="date-filter">Até<input aria-label="Data final" type="date" value={filter.to} onChange={e => setFilter({...filter, to: e.target.value})}/></label><select aria-label="Tipo de movimentação" value={filter.type} onChange={e => setFilter({...filter, type: e.target.value})}><option value="">Todos os tipos</option><option value="ENTRADA">Entrada</option><option value="SAIDA">Saída</option></select></>}
        </div>
        {badRange && page === 'history' && <p className="inline-error" role="alert">A data inicial deve ser anterior à data final.</p>}
        <div className="table-wrap" aria-busy={loading}>{page === 'stock' ? <table><thead><tr><th>CÓDIGO</th><th>PRODUTO</th><th>UNIDADE</th><th className="numeric">ESTOQUE MÍNIMO</th><th className="numeric">SALDO ATUAL</th><th>SITUAÇÃO</th><th className="actions-column">AÇÕES</th></tr></thead><tbody>{filteredProducts.map(p => <tr key={p.id}><td className="muted">#{String(p.id).padStart(3,'0')}</td><td><span className="product-cell"><span className="product-icon"><Package size={18}/></span><strong>{p.name}</strong></span></td><td>{p.unit}</td><td className="numeric muted">{number(p.minimum)}</td><td className="numeric balance">{number(p.stock)}</td><td><Status p={p}/></td><td><span className="row-actions"><button className="icon-button edit-button" title="Editar produto" aria-label={`Editar ${p.name}`} onClick={() => setEditing({kind:'product', record:p})}><Pencil size={16}/></button><button className="icon-button delete-button" title="Excluir produto" aria-label={`Excluir ${p.name}`} onClick={() => remove('product',p)}><Trash2 size={16}/></button></span></td></tr>)}</tbody></table> : <table><thead><tr><th>DATA E HORA</th><th>PRODUTO</th><th>TIPO</th><th className="numeric">QUANTIDADE</th><th>UNIDADE</th><th className="actions-column">AÇÕES</th></tr></thead><tbody>{filteredMovements.map(m => <tr key={m.id}><td className="muted">{date(m.occurred_at)}</td><td><strong>{m.product_name}</strong></td><td><span className={`badge ${m.type === 'ENTRADA' ? 'success' : 'outgoing'}`}>{m.type === 'ENTRADA' ? <ArrowDownLeft size={14}/> : <ArrowUpRight size={14}/>} {m.type === 'ENTRADA' ? 'Entrada' : 'Saída'}</span></td><td className="numeric balance">{number(m.quantity)}</td><td>{m.unit}</td><td><span className="row-actions"><button className="icon-button edit-button" title="Editar movimentação" aria-label={`Editar movimentação de ${m.product_name}`} onClick={() => setEditing({kind:'movement', record:m})}><Pencil size={16}/></button><button className="icon-button delete-button" title="Excluir movimentação" aria-label={`Excluir movimentação de ${m.product_name}`} onClick={() => remove('movement',m)}><Trash2 size={16}/></button></span></td></tr>)}</tbody></table>}
        {!loading && !error && !(page === 'stock' ? filteredProducts : filteredMovements).length && <div className="empty"><Package size={36}/><h3>{search || status !== 'all' || page === 'history' ? 'Nenhum registro encontrado' : 'Seu estoque começa aqui'}</h3><p>{products.length ? 'Cadastre novos itens ou ajuste os filtros para ver outros resultados.' : 'Cadastre seu primeiro produto para começar a registrar entradas e saídas.'}</p>{!products.length && <button className="primary" onClick={() => setModal('product')}><Plus size={16}/> Cadastrar produtos</button>}</div>}
        {loading && <div className="loading" role="status">Carregando estoque…</div>}</div><div className="table-footer">{number((page === 'stock' ? filteredProducts : filteredMovements).length)} registros <span>Horário de Belém (PA)</span></div>
      </section><footer className="page-footer">Estoque UEPA <span>Organização para o dia a dia.</span></footer>
    </main></div>
    {modal === 'warehouse' && <WarehouseModal onClose={() => setModal(null)} onSaved={w => { setWarehouses(list => [...list,w]); selectWarehouse(w.id); setNotice(`Estoque “${w.name}” criado com sucesso.`); }}/ >}
    {modal && modal !== 'warehouse' && activeWarehouse && <BatchModal kind={modal} warehouse={activeWarehouse} products={products} onClose={() => setModal(null)} onSaved={async () => { setModal(null); setNotice('Lista registrada com sucesso.'); await refresh(); }}/ >}
    {editing?.kind === 'product' && <EditProductModal product={editing.record} warehouse={activeWarehouse} onClose={() => setEditing(null)} onSaved={async () => { setEditing(null); setNotice('Produto atualizado com sucesso.'); await refresh(); }}/>} 
    {editing?.kind === 'movement' && <EditMovementModal movement={editing.record} warehouse={activeWarehouse} onClose={() => setEditing(null)} onSaved={async () => { setEditing(null); setNotice('Movimentação atualizada com sucesso.'); await refresh(); }}/>} 
  </div>;
}
function Stat({title,value,label,icon,warm}) { return <article className="stat"><div><span>{title}</span><strong>{number(value)}</strong><small>{label}</small></div><span className={`stat-icon ${warm ? 'warm' : ''}`}>{icon}</span></article>; }

function BatchModal({kind, warehouse, products, onClose, onSaved}) {
  const isProduct = kind === 'product', dialog = useRef(null);
  const [items, setItems] = useState([]), [error, setError] = useState(''), [saving, setSaving] = useState(false);
  const empty = isProduct ? {name:'',unit:'UN',minimum:0} : {productId:'',type:'ENTRADA',quantity:1};
  const [draft, setDraft] = useState(empty);
  const [productQuery, setProductQuery] = useState('');
  useEffect(() => { const d = dialog.current; d.showModal(); return () => d.close(); }, []);
  const field = (key,value) => setDraft({...draft,[key]:value});
  function add(e) {
    e.preventDefault(); setError('');
    if (items.length >= 100) { setError('Adicione até 100 itens por lista.'); return; }
    if (isProduct) {
      const name = draft.name.trim(), unit = draft.unit.trim(), minimum = Number(draft.minimum);
      if (!name || !unit || !Number.isInteger(minimum) || minimum < 0 || minimum > 2147483647) { setError('Preencha nome, unidade e quantidade mínima válida.'); return; }
      if ([...products,...items].some(p => p.name.toLowerCase() === name.toLowerCase())) { setError('Já existe um produto com esse nome.'); return; }
      setItems([...items,{name,unit,minimum}]);
    } else {
      const productId = Number(draft.productId), quantity = Number(draft.quantity);
      if (!products.some(p => p.id === productId) || !Number.isInteger(quantity) || quantity <= 0 || quantity > 2147483647) { setError('Escolha um produto e uma quantidade inteira positiva.'); return; }
      setItems([...items,{productId,type:draft.type,quantity}]);
    }
    setDraft(empty); setProductQuery('');
  }
  async function save() {
    setSaving(true); setError('');
    try { await api(isProduct ? 'products' : 'movements', {warehouseId: warehouse.id, ...(isProduct ? {products:items} : {movements:items})}); await onSaved(); }
    catch (e) { setError(e.message); setSaving(false); }
  }
  return <dialog ref={dialog} onCancel={e => { e.preventDefault(); if (!saving) onClose(); }} aria-labelledby="modal-title"><div className="modal-header"><div><p className="eyebrow">{isProduct ? 'CATÁLOGO DE MATERIAIS' : 'CONTROLE DE SALDO'}</p><h2 id="modal-title">{isProduct ? 'Cadastrar produtos' : 'Nova movimentação'}</h2></div><button className="icon-button" aria-label="Fechar" onClick={onClose} disabled={saving}><X size={22}/></button></div><p className="modal-intro">Estoque: <strong>{warehouse.name}</strong>. Adicione os itens à lista, confira e salve tudo de uma vez.</p>
    <form onSubmit={add}><fieldset disabled={saving}>{isProduct ? <><label>Nome do produto<input autoFocus required maxLength={180} value={draft.name} onChange={e => field('name',e.target.value)} placeholder="Ex.: Papel A4"/></label><div className="form-row"><label>Unidade<input required maxLength={30} value={draft.unit} onChange={e => field('unit',e.target.value)} list="units"/><datalist id="units">{['UN','CX','KG','L','PCT','RESMA'].map(u => <option key={u}>{u}</option>)}</datalist></label><label>Estoque mínimo<input required type="number" min="0" max="2147483647" step="1" value={draft.minimum} onChange={e => field('minimum',e.target.value)}/></label></div></> : <><ProductAutocomplete products={products} query={productQuery} onQuery={value => { setProductQuery(value); field('productId',''); }} onSelect={product => { setProductQuery(product.name); field('productId',product.id); }}/><div className="form-row"><label>Tipo<select value={draft.type} onChange={e => field('type',e.target.value)}><option value="ENTRADA">Entrada</option><option value="SAIDA">Saída</option></select></label><label>Quantidade<input required type="number" min="1" max="2147483647" step="1" value={draft.quantity} onChange={e => field('quantity',e.target.value)}/></label></div></>}<button type="submit" className={`secondary ${isProduct || draft.type === 'ENTRADA' ? 'action-green' : 'action-red'}`}><Plus size={17}/> Adicionar à lista</button></fieldset></form>
    {error && <div className="message error" role="alert">{error}</div>}
    <div className="batch-heading">Itens para registrar <span>{items.length}/100</span></div><div className="batch-items">{!items.length ? <p className="muted">Os itens adicionados aparecerão aqui.</p> : items.map((item,i) => <div className="batch-item" key={i}><div><strong>{isProduct ? item.name : products.find(p => p.id === item.productId)?.name}</strong><small>{isProduct ? `${item.unit} · mínimo ${item.minimum}` : `${item.type === 'ENTRADA' ? 'Entrada' : 'Saída'} · ${item.quantity}`}</small></div><button className="icon-button" aria-label={`Remover item ${i+1}`} disabled={saving} onClick={() => setItems(items.filter((_,j) => j !== i))}><Trash2 size={17}/></button></div>)}</div>
    <div className="modal-footer"><button className="secondary" onClick={onClose} disabled={saving}>Cancelar</button><button className={`primary ${isProduct ? 'action-green' : items.some(item => item.type === 'SAIDA') ? 'action-red' : 'action-green'}`} disabled={!items.length || saving} onClick={save}>{saving ? 'Salvando…' : `Salvar lista (${items.length})`}</button></div>
  </dialog>;
}

function EditProductModal({product, warehouse, onClose, onSaved}) {
  const dialog = useRef(null);
  const [draft, setDraft] = useState({name:product.name, unit:product.unit, minimum:product.minimum}), [saving, setSaving] = useState(false), [error, setError] = useState('');
  useEffect(() => { const d = dialog.current; d.showModal(); return () => d.close(); }, []);
  async function save(e) {
    e.preventDefault();
    const minimum = Number(draft.minimum);
    if (!draft.name.trim() || !draft.unit.trim() || !Number.isInteger(minimum) || minimum < 0) { setError('Preencha nome, unidade e estoque mínimo válido.'); return; }
    setSaving(true); setError('');
    try { await api(`products/${product.id}`, {warehouseId:warehouse.id, name:draft.name.trim(), unit:draft.unit.trim(), minimum}, 'PUT'); await onSaved(); }
    catch (e) { setError(e.message); setSaving(false); }
  }
  return <dialog ref={dialog} aria-labelledby="edit-product-title" onCancel={e => { e.preventDefault(); if (!saving) onClose(); }}><div className="modal-header"><div><p className="eyebrow">CATÁLOGO DE MATERIAIS</p><h2 id="edit-product-title">Editar produto</h2></div><button className="icon-button" aria-label="Fechar" onClick={onClose} disabled={saving}><X size={22}/></button></div><form onSubmit={save}><fieldset disabled={saving}><label>Nome do produto<input autoFocus required maxLength={180} value={draft.name} onChange={e => setDraft({...draft,name:e.target.value})}/></label><div className="form-row"><label>Unidade<input required maxLength={30} value={draft.unit} onChange={e => setDraft({...draft,unit:e.target.value})}/></label><label>Estoque mínimo<input required type="number" min="0" max="2147483647" step="1" value={draft.minimum} onChange={e => setDraft({...draft,minimum:e.target.value})}/></label></div></fieldset>{error && <div className="message error" role="alert">{error}</div>}<div className="modal-footer"><button type="button" className="secondary" onClick={onClose} disabled={saving}>Cancelar</button><button className="primary action-green" type="submit" disabled={saving}>{saving ? 'Salvando…' : 'Salvar alterações'}</button></div></form></dialog>;
}

function EditMovementModal({movement, warehouse, onClose, onSaved}) {
  const dialog = useRef(null);
  const [draft, setDraft] = useState({type:movement.type, quantity:movement.quantity}), [saving, setSaving] = useState(false), [error, setError] = useState('');
  useEffect(() => { const d = dialog.current; d.showModal(); return () => d.close(); }, []);
  async function save(e) {
    e.preventDefault();
    const quantity = Number(draft.quantity);
    if (!Number.isInteger(quantity) || quantity <= 0) { setError('Informe uma quantidade inteira positiva.'); return; }
    setSaving(true); setError('');
    try { await api(`movements/${movement.id}`, {warehouseId:warehouse.id, type:draft.type, quantity}, 'PUT'); await onSaved(); }
    catch (e) { setError(e.message); setSaving(false); }
  }
  return <dialog ref={dialog} aria-labelledby="edit-movement-title" onCancel={e => { e.preventDefault(); if (!saving) onClose(); }}><div className="modal-header"><div><p className="eyebrow">HISTÓRICO DE MOVIMENTAÇÕES</p><h2 id="edit-movement-title">Editar movimentação</h2></div><button className="icon-button" aria-label="Fechar" onClick={onClose} disabled={saving}><X size={22}/></button></div><p className="modal-intro">Produto: <strong>{movement.product_name}</strong>. A data do registro é mantida.</p><form onSubmit={save}><fieldset disabled={saving}><div className="form-row"><label>Tipo<select value={draft.type} onChange={e => setDraft({...draft,type:e.target.value})}><option value="ENTRADA">Entrada</option><option value="SAIDA">Saída</option></select></label><label>Quantidade<input required type="number" min="1" max="2147483647" step="1" value={draft.quantity} onChange={e => setDraft({...draft,quantity:e.target.value})}/></label></div></fieldset>{error && <div className="message error" role="alert">{error}</div>}<div className="modal-footer"><button type="button" className="secondary" onClick={onClose} disabled={saving}>Cancelar</button><button className={`primary ${draft.type === 'ENTRADA' ? 'action-green' : 'action-red'}`} type="submit" disabled={saving}>{saving ? 'Salvando…' : 'Salvar alterações'}</button></div></form></dialog>;
}

function WarehouseModal({onClose, onSaved}) {
  const dialog = useRef(null);
  const [name, setName] = useState(''), [saving, setSaving] = useState(false), [error, setError] = useState('');
  useEffect(() => { const d = dialog.current; d.showModal(); return () => d.close(); }, []);
  async function save(e) {
    e.preventDefault();
    if (!name.trim()) { setError('Informe o nome do estoque.'); return; }
    setSaving(true); setError('');
    try { onSaved(await api('warehouses', {name: name.trim()})); }
    catch (e) { setError(e.message); setSaving(false); }
  }
  return <dialog ref={dialog} aria-labelledby="warehouse-title" onCancel={e => { e.preventDefault(); if (!saving) onClose(); }}><div className="modal-header"><h2 id="warehouse-title">Adicionar estoque</h2><button className="icon-button" onClick={onClose} disabled={saving} aria-label="Fechar"><X size={22}/></button></div><p className="modal-intro">Crie um estoque para cada setor ou local. Os produtos e as movimentações ficarão separados.</p><form onSubmit={save}><label>Nome do estoque<input autoFocus required maxLength={100} value={name} onChange={e => setName(e.target.value)} placeholder="Ex.: ADM ou IOOM" disabled={saving}/></label>{error && <div className="message error" role="alert">{error}</div>}<div className="modal-footer"><button type="button" className="secondary" onClick={onClose} disabled={saving}>Cancelar</button><button className="primary action-blue" type="submit" disabled={saving || !name.trim()}>{saving ? 'Criando…' : 'Criar estoque'}</button></div></form></dialog>;
}
