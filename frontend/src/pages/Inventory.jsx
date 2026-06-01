import { useState, useEffect } from 'react';
import { inventoryApi } from '../api';
import { useToast } from '../context/ToastContext';
import ProtectedRoute from '../components/ProtectedRoute';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import RarityBadge from '../components/RarityBadge';

function SendModal({ entry, onClose, onSent }) {
  const [recipient, setRecipient] = useState('');
  const [qty, setQty] = useState(1);
  const [sending, setSending] = useState(false);
  const toast = useToast();

  const handleSend = (e) => {
    e.preventDefault();
    if (!recipient.trim()) { toast.error('Enter a recipient username'); return; }
    if (qty < 1 || qty > entry.quantity) { toast.error('Invalid quantity'); return; }
    setSending(true);
    inventoryApi.send(entry.id, recipient.trim(), qty)
      .then((r) => { toast.success(r.message); onSent(); })
      .catch((e) => toast.error(e.response?.data?.error || 'Send failed'))
      .finally(() => setSending(false));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2 className="card-title">Send Item</h2>
        <p>Sending: <strong>{entry.name}</strong> (you have {entry.quantity})</p>
        <form onSubmit={handleSend} className="profile-form">
          <div className="form-group">
            <label htmlFor="send-recipient">Recipient Username</label>
            <input id="send-recipient" value={recipient} onChange={(e) => setRecipient(e.target.value)} placeholder="e.g. john_doe" disabled={sending} />
          </div>
          <div className="form-group">
            <label htmlFor="send-qty">Quantity</label>
            <input id="send-qty" type="number" min="1" max={entry.quantity} value={qty} onChange={(e) => setQty(Number(e.target.value))} disabled={sending} />
          </div>
          <div className="modal-actions">
            <button type="submit" className="btn btn-primary" disabled={sending}>{sending ? 'Sending...' : 'Send'}</button>
            <button type="button" className="btn" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function TradeModal({ myInventory, onClose, onTraded }) {
  const [myItemId, setMyItemId] = useState('');
  const [myQty, setMyQty] = useState(1);
  const [theirUsername, setTheirUsername] = useState('');
  const [theirInventory, setTheirInventory] = useState(null);
  const [theirItemId, setTheirItemId] = useState('');
  const [theirQty, setTheirQty] = useState(1);
  const [loading, setLoading] = useState(false);
  const [trading, setTrading] = useState(false);
  const toast = useToast();

  const lookupUser = () => {
    if (!theirUsername.trim()) return;
    setLoading(true);
    inventoryApi.userInventory(theirUsername.trim())
      .then((data) => {
        setTheirInventory(data.inventory);
        if (data.inventory.length > 0) setTheirItemId(String(data.inventory[0].id));
      })
      .catch(() => { toast.error('User not found'); setTheirInventory(null); })
      .finally(() => setLoading(false));
  };

  const handleTrade = (e) => {
    e.preventDefault();
    if (!myItemId || !theirItemId) { toast.error('Select items for both sides'); return; }
    setTrading(true);
    inventoryApi.trade(Number(myItemId), myQty, theirUsername.trim(), Number(theirItemId), theirQty)
      .then((r) => { toast.success(r.message); onTraded(); })
      .catch((e) => toast.error(e.response?.data?.error || 'Trade failed'))
      .finally(() => setTrading(false));
  };

  const selectedMy = myInventory.find((e) => String(e.id) === myItemId);
  const selectedTheir = theirInventory?.find((e) => String(e.id) === theirItemId);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-wide" onClick={(e) => e.stopPropagation()}>
        <h2 className="card-title">Trade Items</h2>
        <form onSubmit={handleTrade}>
          <div className="trade-columns">
            <div className="trade-side">
              <h3>Your Items</h3>
              <div className="form-group">
                <label htmlFor="my-item">Select Item</label>
                <select id="my-item" value={myItemId} onChange={(e) => { setMyItemId(e.target.value); setMyQty(1); }}>
                  <option value="">-- Select --</option>
                  {myInventory.map((e) => (
                    <option key={e.id} value={e.id}>{e.name} (x{e.quantity})</option>
                  ))}
                </select>
              </div>
              {selectedMy && (
                <div className="form-group">
                  <label htmlFor="my-qty">Quantity (max {selectedMy.quantity})</label>
                  <input id="my-qty" type="number" min="1" max={selectedMy.quantity} value={myQty} onChange={(e) => setMyQty(Number(e.target.value))} />
                </div>
              )}
            </div>

            <div className="trade-divider">
              <span className="trade-arrow">&#8596;</span>
            </div>

            <div className="trade-side">
              <h3>Their Items</h3>
              <div className="form-group">
                <label htmlFor="their-user">Username</label>
                <div className="input-with-btn">
                  <input id="their-user" value={theirUsername} onChange={(e) => setTheirUsername(e.target.value)} placeholder="Username" />
                  <button type="button" className="btn btn-sm" onClick={lookupUser} disabled={loading}>{loading ? '...' : 'Lookup'}</button>
                </div>
              </div>
              {theirInventory !== null && (
                theirInventory.length === 0 ? (
                  <p className="text-muted">This user has no items.</p>
                ) : (
                  <>
                    <div className="form-group">
                      <label htmlFor="their-item">Select Item</label>
                      <select id="their-item" value={theirItemId} onChange={(e) => { setTheirItemId(e.target.value); setTheirQty(1); }}>
                        {theirInventory.map((e) => (
                          <option key={e.id} value={e.id}>{e.name} (x{e.quantity})</option>
                        ))}
                      </select>
                    </div>
                    {selectedTheir && (
                      <div className="form-group">
                        <label htmlFor="their-qty">Quantity (max {selectedTheir.quantity})</label>
                        <input id="their-qty" type="number" min="1" max={selectedTheir.quantity} value={theirQty} onChange={(e) => setTheirQty(Number(e.target.value))} />
                      </div>
                    )}
                  </>
                )
              )}
            </div>
          </div>
          <div className="modal-actions" style={{ marginTop: '1rem' }}>
            <button type="submit" className="btn btn-primary" disabled={trading || !myItemId || !theirItemId}>{trading ? 'Trading...' : 'Execute Trade'}</button>
            <button type="button" className="btn" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function InventoryContent() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [sendEntry, setSendEntry] = useState(null);
  const [showTrade, setShowTrade] = useState(false);
  const toast = useToast();

  const fetchInventory = () => {
    setLoading(true);
    inventoryApi.list()
      .then(setItems)
      .catch(() => { toast.error('Failed to load inventory'); setItems([]); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchInventory(); }, []);

  const filtered = filter ? items.filter((i) => i.category === filter) : items;

  const categories = [...new Set(items.map((i) => i.category))];

  if (loading) return <div className="page centered"><LoadingSpinner size="lg" /></div>;

  return (
    <div className="page">
      <header className="page-header">
        <h1>Your Inventory</h1>
        <p className="subtitle">{items.length} unique item{items.length !== 1 ? 's' : ''} &middot; {items.reduce((s, i) => s + i.quantity, 0)} total</p>
      </header>

      <div className="inventory-toolbar">
        <div className="filters">
          <select value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter by category">
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c === 'hero_skin' ? 'Hero Skins' : c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
        </div>
        <button className="btn btn-primary" onClick={() => setShowTrade(true)}>Trade Items</button>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title="Inventory Empty"
          description={filter ? 'No items in this category.' : 'Purchase items from the store to fill your inventory.'}
          actionLabel="Visit Store"
          actionHref="/"
        />
      ) : (
        <div className="item-grid">
          {filtered.map((entry) => (
            <article key={entry.id} className="item-card inventory-card">
              {entry.image_src && (
                <img src={entry.image_src} alt="" className="item-img" loading="lazy" onError={(e) => (e.target.style.display = 'none')} />
              )}
              <div className="item-card-body">
                <RarityBadge rarity={entry.rarity} />
                <h2 className="item-title">{entry.name}</h2>
                <span className="inventory-qty">x{entry.quantity}</span>
                <span className="inventory-category">{entry.category === 'hero_skin' ? 'Hero Skin' : entry.category}</span>
              </div>
              <div className="card-actions">
                <button className="btn btn-sm" onClick={() => setSendEntry(entry)}>Send</button>
              </div>
            </article>
          ))}
        </div>
      )}

      {sendEntry && (
        <SendModal entry={sendEntry} onClose={() => setSendEntry(null)} onSent={() => { setSendEntry(null); fetchInventory(); }} />
      )}
      {showTrade && (
        <TradeModal myInventory={items} onClose={() => setShowTrade(false)} onTraded={() => { setShowTrade(false); fetchInventory(); }} />
      )}
    </div>
  );
}

export default function Inventory() {
  return (
    <ProtectedRoute>
      <InventoryContent />
    </ProtectedRoute>
  );
}
