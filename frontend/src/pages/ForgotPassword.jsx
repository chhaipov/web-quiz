import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { passwordApi } from '../api';
import { useToast } from '../context/ToastContext';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const toast = useToast();
  const [step, setStep] = useState(1);
  const [username, setUsername] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [debugOtp, setDebugOtp] = useState(null);

  const handleRequestOtp = (e) => {
    e.preventDefault();
    if (!username.trim()) return;
    setLoading(true);
    setError('');
    passwordApi
      .forgotPassword(username.trim())
      .then((data) => {
        setStep(2);
        if (data.debug_otp) setDebugOtp(data.debug_otp);
        toast.success('OTP sent (check debug info)');
      })
      .catch((e) => setError(e.response?.data?.detail || 'Request failed'))
      .finally(() => setLoading(false));
  };

  const handleVerifyOtp = (e) => {
    e.preventDefault();
    if (!code.trim() || !newPassword) return;
    setLoading(true);
    setError('');
    passwordApi
      .verifyOtp(username.trim(), code.trim(), newPassword)
      .then(() => {
        toast.success('Password reset successfully! Please log in.');
        navigate('/login');
      })
      .catch((e) => setError(e.response?.data?.detail || 'Invalid OTP'))
      .finally(() => setLoading(false));
  };

  return (
    <div className="page login-page">
      <div className="auth-card">
        <h1>Forgot Password</h1>
        <p className="subtitle">
          {step === 1 ? 'Enter your username to receive a reset code' : 'Enter the OTP and your new password'}
        </p>

        {error && <div className="alert alert-error">{error}</div>}

        {step === 1 ? (
          <form className="auth-form" onSubmit={handleRequestOtp}>
            <label htmlFor="fp-username">Username</label>
            <input
              id="fp-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={loading}
              autoComplete="username"
            />
            <button type="submit" className="btn btn-primary btn-block" disabled={loading || !username.trim()}>
              {loading ? 'Sending…' : 'Send Reset Code'}
            </button>
          </form>
        ) : (
          <>
            {debugOtp && (
              <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
                Debug: Your OTP is <strong>{debugOtp}</strong>
              </div>
            )}
            <form className="auth-form" onSubmit={handleVerifyOtp}>
              <label htmlFor="fp-code">4-Digit OTP Code</label>
              <input
                id="fp-code"
                type="text"
                maxLength={4}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 4))}
                required
                disabled={loading}
                placeholder="0000"
                autoComplete="one-time-code"
              />
              <label htmlFor="fp-newpass">New Password</label>
              <input
                id="fp-newpass"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                disabled={loading}
                minLength={6}
                autoComplete="new-password"
              />
              <button type="submit" className="btn btn-primary btn-block" disabled={loading || code.length < 4 || !newPassword}>
                {loading ? 'Verifying…' : 'Reset Password'}
              </button>
            </form>
            <p className="auth-footer">
              <button type="button" className="btn-link" onClick={() => { setStep(1); setError(''); setDebugOtp(null); }}>
                Back to username
              </button>
            </p>
          </>
        )}

        <p className="auth-footer">
          Remember your password? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}
