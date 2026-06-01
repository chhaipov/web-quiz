import { useState, useEffect } from 'react';
import { authApi } from '../api';
import { useToast } from '../context/ToastContext';
import ProtectedRoute from '../components/ProtectedRoute';
import LoadingSpinner from '../components/LoadingSpinner';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function ProfileContent() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [changingPw, setChangingPw] = useState(false);
  const [activeTab, setActiveTab] = useState('info');

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [bio, setBio] = useState('');
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const toast = useToast();

  useEffect(() => {
    authApi
      .profile()
      .then((data) => {
        setProfile(data);
        setUsername(data.username);
        setEmail(data.email || '');
        setBio(data.bio || '');
      })
      .catch(() => toast.error('Failed to load profile'))
      .finally(() => setLoading(false));
  }, []);

  const getAvatarUrl = () => {
    if (profile?.avatar_url) {
      if (profile.avatar_url.startsWith('http')) return profile.avatar_url;
      if (profile.avatar_url.startsWith('/images/')) return profile.avatar_url;
      return `${API_BASE.replace('/api', '')}${profile.avatar_url}`;
    }
    return null;
  };

  const handleSaveProfile = (e) => {
    e.preventDefault();
    setSaving(true);
    authApi
      .updateProfile({ username, email, bio })
      .then((data) => {
        setProfile(data);
        toast.success('Profile updated');
      })
      .catch((e) => toast.error(e.response?.data?.detail || 'Update failed'))
      .finally(() => setSaving(false));
  };

  const handleChangePassword = (e) => {
    e.preventDefault();
    if (!oldPassword || !newPassword) {
      toast.error('Both fields are required');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    setChangingPw(true);
    authApi
      .changePassword(oldPassword, newPassword)
      .then(() => {
        toast.success('Password changed successfully');
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
      })
      .catch((e) => toast.error(e.response?.data?.detail || 'Password change failed'))
      .finally(() => setChangingPw(false));
  };

  if (loading) {
    return (
      <div className="page centered">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const avatarUrl = getAvatarUrl();
  const memberSince = profile?.date_joined
    ? new Date(profile.date_joined).toLocaleDateString(undefined, { year: 'numeric', month: 'long' })
    : null;

  return (
    <div className="page profile-page">
      {/* Hero banner */}
      <div className="profile-hero">
        <div className="profile-hero-bg" />
        <div className="profile-hero-content">
          <div className="profile-hero-avatar">
            {avatarUrl ? (
              <img src={avatarUrl} alt="Avatar" />
            ) : (
              <div className="profile-hero-avatar-placeholder">
                <span>{username?.charAt(0)?.toUpperCase() || '?'}</span>
              </div>
            )}
            <div className="profile-avatar-status" />
          </div>
          <div className="profile-hero-info">
            <h1 className="profile-hero-name">{profile?.username}</h1>
            <p className="profile-hero-email">{profile?.email || 'No email set'}</p>
            {profile?.bio && <p className="profile-hero-bio">{profile.bio}</p>}
          </div>
          <div className="profile-hero-meta">
            <div className="profile-meta-badge">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              {memberSince ? `Member since ${memberSince}` : 'Active member'}
            </div>
            <div className="profile-meta-badge profile-meta-id">
              ID: {profile?.id}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="profile-tabs">
        <button
          className={`profile-tab ${activeTab === 'info' ? 'profile-tab-active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          Account Info
        </button>
        <button
          className={`profile-tab ${activeTab === 'security' ? 'profile-tab-active' : ''}`}
          onClick={() => setActiveTab('security')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
          Security
        </button>
      </div>

      {/* Tab content */}
      <div className="profile-tab-content">
        {activeTab === 'info' && (
          <div className="profile-card">
            <div className="profile-card-header">
              <h2>Edit Profile</h2>
              <p className="text-muted">Update your personal information</p>
            </div>
            <form onSubmit={handleSaveProfile} className="profile-edit-form">
              <div className="profile-form-grid">
                <div className="form-group">
                  <label htmlFor="profile-username">Username</label>
                  <div className="profile-input-wrapper">
                    <svg className="profile-input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    <input
                      id="profile-username"
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      disabled={saving}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label htmlFor="profile-email">Email Address</label>
                  <div className="profile-input-wrapper">
                    <svg className="profile-input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                    <input
                      id="profile-email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={saving}
                      placeholder="you@example.com"
                    />
                  </div>
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="profile-bio">Bio</label>
                <textarea
                  id="profile-bio"
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  disabled={saving}
                  placeholder="Write a short bio about yourself..."
                  rows={3}
                />
                <span className="profile-field-hint">{bio.length}/300 characters</span>
              </div>
              <div className="profile-form-actions">
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        )}

        {activeTab === 'security' && (
          <div className="profile-card">
            <div className="profile-card-header">
              <h2>Change Password</h2>
              <p className="text-muted">Keep your account secure with a strong password</p>
            </div>
            <form onSubmit={handleChangePassword} className="profile-edit-form">
              <div className="form-group">
                <label htmlFor="old-pw">Current Password</label>
                <div className="profile-input-wrapper">
                  <svg className="profile-input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                  <input
                    id="old-pw"
                    type="password"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    disabled={changingPw}
                    placeholder="Enter current password"
                  />
                </div>
              </div>
              <div className="profile-form-grid">
                <div className="form-group">
                  <label htmlFor="new-pw">New Password</label>
                  <div className="profile-input-wrapper">
                    <svg className="profile-input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.78 7.78 5.5 5.5 0 017.78-7.78zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
                    <input
                      id="new-pw"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      disabled={changingPw}
                      minLength={6}
                      placeholder="Enter new password"
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label htmlFor="confirm-pw">Confirm New Password</label>
                  <div className="profile-input-wrapper">
                    <svg className="profile-input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    <input
                      id="confirm-pw"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={changingPw}
                      minLength={6}
                      placeholder="Confirm new password"
                    />
                  </div>
                  {confirmPassword && newPassword !== confirmPassword && (
                    <span className="profile-field-hint text-danger">Passwords do not match</span>
                  )}
                </div>
              </div>
              <div className="profile-form-actions">
                <button type="submit" className="btn btn-primary" disabled={changingPw}>
                  {changingPw ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Profile() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}
