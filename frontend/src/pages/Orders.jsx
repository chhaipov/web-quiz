import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ordersApi } from '../api';
import { useToast } from '../context/ToastContext';
import ProtectedRoute from '../components/ProtectedRoute';
import EmptyState from '../components/EmptyState';
import LoadingSpinner from '../components/LoadingSpinner';

const STATUS_LABELS = {
  pending: 'Pending',
  processing: 'Processing',
  shipped: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
};

function OrdersContent() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exportName, setExportName] = useState('');
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState(null);
  const toast = useToast();

  useEffect(() => {
    ordersApi
      .list()
      .then(setOrders)
      .catch(() => setError('Failed to load orders'))
      .finally(() => setLoading(false));
  }, []);

  const handleExport = (e) => {
    e.preventDefault();
    if (!exportName.trim()) return;
    setExporting(true);
    setExportResult(null);
    ordersApi
      .exportOrders(exportName.trim())
      .then((data) => {
        setExportResult(data);
        toast.success('Export complete');
      })
      .catch((e) => {
        const msg = e.response?.data?.error || 'Export failed';
        setExportResult({ error: msg });
        toast.error(msg);
      })
      .finally(() => setExporting(false));
  };

  if (loading) {
    return (
      <div className="page centered">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Order History</h1>
      <p className="subtitle">View and track your purchases</p>

      <div className="card export-section">
        <h2>Export Orders</h2>
        <form className="export-form" onSubmit={handleExport}>
          <div className="form-group">
            <label htmlFor="export-name">Export filename</label>
            <input
              id="export-name"
              type="text"
              placeholder="my-orders"
              value={exportName}
              onChange={(e) => setExportName(e.target.value)}
              disabled={exporting}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={exporting || !exportName.trim()}>
            {exporting ? 'Exporting…' : 'Export'}
          </button>
        </form>
        {exportResult && (
          <div className={`alert ${exportResult.error ? 'alert-error' : 'alert-success'}`} style={{ marginTop: '0.75rem' }}>
            {exportResult.error || `Exported to: ${exportResult.file}`}
          </div>
        )}
      </div>

      {orders.length === 0 ? (
        <EmptyState
          title="No orders yet"
          description="When you place an order, it will appear here."
          actionLabel="Browse items"
        />
      ) : (
        <div className="orders-list">
          {orders.map((o) => (
            <Link key={o.id} to={`/orders/${o.id}`} className="order-card order-card-link">
              <div className="order-header">
                <strong>Order #{o.id}</strong>
                <time dateTime={o.created_at}>{new Date(o.created_at).toLocaleString()}</time>
                <span className={`order-status status-${o.status}`}>{STATUS_LABELS[o.status] || o.status}</span>
              </div>
              <ul className="order-items">
                {(o.order_items || []).slice(0, 3).map((oi) => (
                  <li key={oi.id}>
                    {oi.quantity}x {oi.item?.name}
                    <span> — ${oi.price_snapshot}</span>
                  </li>
                ))}
                {(o.order_items || []).length > 3 && (
                  <li className="text-muted">+{o.order_items.length - 3} more items</li>
                )}
              </ul>
              <p className="order-total">Total: ${o.total}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Orders() {
  return (
    <ProtectedRoute>
      <OrdersContent />
    </ProtectedRoute>
  );
}
