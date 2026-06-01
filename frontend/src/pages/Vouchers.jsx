import { useState } from 'react';
import { voucherApi } from '../api';
import { useToast } from '../context/ToastContext';
import ProtectedRoute from '../components/ProtectedRoute';

function VouchersContent() {
  const [code, setCode] = useState('');
  const [claiming, setClaiming] = useState(false);
  const [result, setResult] = useState(null);
  const toast = useToast();

  const handleClaim = (e) => {
    e.preventDefault();
    if (!code.trim()) { toast.error('Enter a voucher code'); return; }
    setClaiming(true);
    setResult(null);
    voucherApi.claim(code.trim())
      .then((r) => {
        setResult(r);
        toast.success(r.message);
        setCode('');
      })
      .catch((e) => {
        const msg = e.response?.data?.error || 'Claim failed';
        toast.error(msg);
        setResult({ error: msg });
      })
      .finally(() => setClaiming(false));
  };

  return (
    <div className="page">
      <header className="page-header">
        <h1>Vouchers</h1>
        <p className="subtitle">Redeem voucher codes for wallet credits or free items.</p>
      </header>

      <div className="card">
        <h2 className="card-title">Redeem a Code</h2>
        <form onSubmit={handleClaim} className="voucher-claim-form">
          <div className="form-group">
            <label htmlFor="voucher-code">Voucher Code</label>
            <input
              id="voucher-code"
              type="text"
              placeholder="Enter your voucher code"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              disabled={claiming}
              autoComplete="off"
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={claiming}>
            {claiming ? 'Claiming...' : 'Claim Voucher'}
          </button>
        </form>
        {result && !result.error && (
          <div className="voucher-result">
            <p className="text-success"><strong>{result.message}</strong></p>
            {result.type === 'wallet' && <p>New balance: <span className="gold">${result.balance}</span></p>}
            {result.type === 'item' && <p>Check your <a href="/inventory">Inventory</a> for the item.</p>}
          </div>
        )}
        {result?.error && (
          <div className="voucher-result voucher-result-error">
            <p className="text-danger">{result.error}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Vouchers() {
  return (
    <ProtectedRoute>
      <VouchersContent />
    </ProtectedRoute>
  );
}
