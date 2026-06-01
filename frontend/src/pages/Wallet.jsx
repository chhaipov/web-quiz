import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { walletApi } from '../api';
import { useToast } from '../context/ToastContext';
import ProtectedRoute from '../components/ProtectedRoute';
import LoadingSpinner from '../components/LoadingSpinner';

const TXN_LABELS = {
  deposit: 'Deposit',
  purchase: 'Purchase',
  transfer_out: 'Sent',
  transfer_in: 'Received',
  voucher: 'Voucher',
};

const POSITIVE_TYPES = ['deposit', 'transfer_in', 'voucher'];

function WalletContent() {
  const [balance, setBalance] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [transferRecipient, setTransferRecipient] = useState('');
  const [transferAmount, setTransferAmount] = useState('');
  const [transferring, setTransferring] = useState(false);
  const toast = useToast();

  const refreshData = () =>
    Promise.all([
      walletApi.get().then((r) => setBalance(r.balance)),
      walletApi.transactions().then(setTransactions).catch(() => setTransactions([])),
    ])
      .catch(() => setBalance('0.00'))
      .finally(() => setLoading(false));

  useEffect(() => { refreshData(); }, []);

  const handleTransfer = (e) => {
    e.preventDefault();
    const val = parseFloat(transferAmount);
    if (!transferRecipient.trim()) { toast.error('Enter a recipient username'); return; }
    if (isNaN(val) || val <= 0) { toast.error('Enter a valid positive amount'); return; }
    setTransferring(true);
    walletApi.transfer(transferRecipient.trim(), val)
      .then((r) => {
        setBalance(r.balance);
        setTransferRecipient('');
        setTransferAmount('');
        toast.success(r.message);
        walletApi.transactions().then(setTransactions).catch(() => {});
      })
      .catch((e) => toast.error(e.response?.data?.error || 'Transfer failed'))
      .finally(() => setTransferring(false));
  };

  const stats = {
    totalIn: transactions.filter((t) => POSITIVE_TYPES.includes(t.type)).reduce((s, t) => s + parseFloat(t.amount), 0),
    totalOut: transactions.filter((t) => !POSITIVE_TYPES.includes(t.type)).reduce((s, t) => s + parseFloat(t.amount), 0),
    count: transactions.length,
  };

  if (loading) {
    return <div className="page centered"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="page wallet-page">
      {/* Hero balance section */}
      <div className="wallet-hero">
        <div className="wallet-hero-content">
          <span className="wallet-hero-label">Available Balance</span>
          <h1 className="wallet-hero-amount">${balance ?? '0.00'}</h1>
          <div className="wallet-hero-stats">
            <div className="wallet-stat">
              <span className="wallet-stat-icon wallet-stat-in">&#9650;</span>
              <div>
                <span className="wallet-stat-value text-success">${stats.totalIn.toFixed(2)}</span>
                <span className="wallet-stat-label">Total In</span>
              </div>
            </div>
            <div className="wallet-stat">
              <span className="wallet-stat-icon wallet-stat-out">&#9660;</span>
              <div>
                <span className="wallet-stat-value text-danger">${stats.totalOut.toFixed(2)}</span>
                <span className="wallet-stat-label">Total Out</span>
              </div>
            </div>
            <div className="wallet-stat">
              <span className="wallet-stat-icon wallet-stat-txn">&#9670;</span>
              <div>
                <span className="wallet-stat-value">{stats.count}</span>
                <span className="wallet-stat-label">Transactions</span>
              </div>
            </div>
          </div>
        </div>
        <div className="wallet-hero-actions">
          <Link to="/vouchers" className="btn btn-primary btn-sm">Redeem Voucher</Link>
        </div>
      </div>

      {/* Transfer card */}
      <div className="wallet-actions-card">
        <div className="wallet-tabs">
          <button className="wallet-tab wallet-tab-active">Transfer Funds</button>
        </div>
        <form onSubmit={handleTransfer} className="wallet-action-form">
          <p className="wallet-action-desc">Send funds to another user instantly.</p>
          <div className="form-group">
            <label htmlFor="recipient">Recipient</label>
            <input
              id="recipient"
              type="text"
              placeholder="Enter username"
              value={transferRecipient}
              onChange={(e) => setTransferRecipient(e.target.value)}
              disabled={transferring}
            />
          </div>
          <div className="wallet-amount-input">
            <span className="wallet-currency">$</span>
            <input
              type="number"
              min="0.01"
              step="0.01"
              placeholder="0.00"
              value={transferAmount}
              onChange={(e) => setTransferAmount(e.target.value)}
              disabled={transferring}
            />
          </div>
          <button type="submit" className="btn btn-primary btn-block" disabled={transferring}>
            {transferring ? 'Transferring...' : 'Send Transfer'}
          </button>
        </form>
      </div>

      {/* Transaction history */}
      <div className="wallet-history-card">
        <h2 className="card-title">Transaction History</h2>
        {transactions.length === 0 ? (
          <div className="wallet-empty-txn">
            <p className="text-muted">No transactions yet. <Link to="/vouchers">Redeem a voucher</Link> to add funds.</p>
          </div>
        ) : (
          <div className="wallet-txn-list">
            {transactions.map((t) => {
              const isPositive = POSITIVE_TYPES.includes(t.type);
              return (
                <div key={t.id} className="wallet-txn-row">
                  <div className={`wallet-txn-icon ${isPositive ? 'wallet-txn-icon-in' : 'wallet-txn-icon-out'}`}>
                    {isPositive ? '+' : '-'}
                  </div>
                  <div className="wallet-txn-info">
                    <span className="wallet-txn-label">{TXN_LABELS[t.type] || t.type}</span>
                    <span className="wallet-txn-ref">{t.reference || 'No reference'}</span>
                  </div>
                  <div className="wallet-txn-right">
                    <span className={`wallet-txn-amount ${isPositive ? 'text-success' : 'text-danger'}`}>
                      {isPositive ? '+' : '-'}${t.amount}
                    </span>
                    <time className="wallet-txn-date" dateTime={t.created_at}>
                      {new Date(t.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </time>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Wallet() {
  return (
    <ProtectedRoute>
      <WalletContent />
    </ProtectedRoute>
  );
}
