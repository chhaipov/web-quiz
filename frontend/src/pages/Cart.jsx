import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { cartApi, ordersApi, walletApi } from '../api';
import { useToast } from '../context/ToastContext';
import ProtectedRoute from '../components/ProtectedRoute';
import EmptyState from '../components/EmptyState';
import LoadingSpinner from '../components/LoadingSpinner';

function CartContent() {
  const navigate = useNavigate();
  const [cart, setCart] = useState(null);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [updatingId, setUpdatingId] = useState(null);
  const toast = useToast();

  useEffect(() => {
    Promise.all([
      cartApi.get().then(setCart).catch(() => setCart({ cart_items: [], total: 0 })),
      walletApi.get().then((r) => setBalance(parseFloat(r.balance))).catch(() => setBalance(0)),
    ]).finally(() => setLoading(false));
  }, []);

  const refreshCart = () => cartApi.get().then(setCart).catch(() => setCart({ cart_items: [], total: 0 }));
  const refreshBalance = () => walletApi.get().then((r) => setBalance(parseFloat(r.balance))).catch(() => setBalance(0));

  const updateQty = (id, quantity) => {
    setUpdatingId(id);
    if (quantity <= 0) {
      cartApi.remove(id).then(refreshCart).catch(() => toast.error('Failed to update cart')).finally(() => setUpdatingId(null));
    } else {
      cartApi.update(id, quantity).then(refreshCart).catch(() => toast.error('Failed to update quantity')).finally(() => setUpdatingId(null));
    }
  };

  const checkout = () => {
    setChecking(true);
    ordersApi
      .create()
      .then(() => {
        refreshBalance();
        toast.success('Order placed successfully!');
        navigate('/orders');
      })
      .catch((e) => {
        const msg = e.response?.data?.error || 'Checkout failed';
        toast.error(msg);
        if (msg === 'Insufficient balance') refreshBalance();
      })
      .finally(() => setChecking(false));
  };

  if (loading) {
    return (
      <div className="page centered">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const items = cart?.cart_items || [];
  const total = parseFloat(cart?.total ?? 0);
  const hasInsufficientBalance = balance !== null && total > 0 && balance < total;

  if (items.length === 0) {
    return (
      <div className="page">
        <h1>Your Cart</h1>
        <EmptyState
          title="Your cart is empty"
          description="Add items from the store to get started."
          actionLabel="Browse items"
        />
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Your Cart</h1>
      <p className="subtitle">{items.length} item{items.length !== 1 ? 's' : ''} in your cart</p>

      <div className="cart-wrapper">
        <table className="cart-table">
          <thead>
            <tr>
              <th scope="col">Item</th>
              <th scope="col">Price</th>
              <th scope="col">Qty</th>
              <th scope="col">Subtotal</th>
              <th scope="col"></th>
            </tr>
          </thead>
          <tbody>
            {items.map((ci) => (
                <tr key={ci.id}>
                  <td data-label="Item">
                    <Link to={`/item/${ci.item?.id}`} className="cart-item-name">
                      {ci.item?.name}
                    </Link>
                  </td>
                  <td data-label="Price">${ci.item?.usd_price}</td>
                  <td data-label="Qty">
                    <input
                    type="number"
                    min="1"
                    max="99"
                    value={ci.quantity}
                    onChange={(e) => updateQty(ci.id, Number(e.target.value))}
                    disabled={updatingId === ci.id}
                    aria-label={`Quantity for ${ci.item?.name}`}
                  />
                </td>
                <td data-label="Subtotal" className="gold">${ci.subtotal}</td>
                <td data-label="">
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => updateQty(ci.id, 0)}
                    disabled={updatingId === ci.id}
                    aria-label={`Remove ${ci.item?.name}`}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="cart-summary">
          <p className="cart-balance">Balance: ${balance != null ? balance.toFixed(2) : '0.00'}</p>
          <p className="total">Total: ${total.toFixed(2)}</p>
          {hasInsufficientBalance && (
            <p className="insufficient-balance" role="alert">
              Insufficient balance. Add funds in <Link to="/wallet">Wallet</Link>.
            </p>
          )}
          <button
            className="btn btn-primary btn-lg"
            onClick={checkout}
            disabled={checking || hasInsufficientBalance}
          >
            {checking ? 'Processing…' : 'Checkout'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Cart() {
  return (
    <ProtectedRoute>
      <CartContent />
    </ProtectedRoute>
  );
}
