import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ordersApi } from '../api';
import ProtectedRoute from '../components/ProtectedRoute';
import LoadingSpinner from '../components/LoadingSpinner';

const STATUS_LABELS = {
  pending: 'Pending',
  processing: 'Processing',
  shipped: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
};

function OrderDetailContent() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    ordersApi
      .get(id)
      .then(setOrder)
      .catch(() => setError('Order not found'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="page centered">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="page">
        <div className="alert alert-error">{error || 'Order not found'}</div>
        <Link to="/orders" className="btn">Back to Orders</Link>
      </div>
    );
  }

  return (
    <div className="page">
      <Link to="/orders" className="btn btn-sm back-link">Back to Orders</Link>
      <h1>Order #{order.id}</h1>

      <div className="order-detail-meta">
        <span className={`order-status status-${order.status}`}>
          {STATUS_LABELS[order.status] || order.status}
        </span>
        <time dateTime={order.created_at}>
          {new Date(order.created_at).toLocaleString()}
        </time>
      </div>

      <table className="cart-table">
        <thead>
          <tr>
            <th scope="col">Item</th>
            <th scope="col">Unit Price</th>
            <th scope="col">Qty</th>
            <th scope="col">Subtotal</th>
          </tr>
        </thead>
        <tbody>
          {(order.order_items || []).map((oi) => (
            <tr key={oi.id}>
              <td data-label="Item">
                <Link to={`/item/${oi.item?.id}`} className="cart-item-name">
                  {oi.item?.name}
                </Link>
              </td>
              <td data-label="Unit Price">${oi.price_snapshot}</td>
              <td data-label="Qty">{oi.quantity}</td>
              <td data-label="Subtotal" className="gold">
                ${(parseFloat(oi.price_snapshot) * oi.quantity).toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="cart-summary">
        <p className="total">Total: ${order.total}</p>
      </div>
    </div>
  );
}

export default function OrderDetail() {
  return (
    <ProtectedRoute>
      <OrderDetailContent />
    </ProtectedRoute>
  );
}
