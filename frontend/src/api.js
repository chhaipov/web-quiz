/**
 * API client for Dota 2 Item Shop
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh');
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/token/refresh/`, { refresh });
          localStorage.setItem('access', data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem('access');
          localStorage.removeItem('refresh');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(err);
  }
);

export const authApi = {
  login: (username, password) =>
    api.post('/auth/token/', { username, password }).then((r) => r.data),
  refresh: (refresh) =>
    api.post('/auth/token/refresh/', { refresh }).then((r) => r.data),
  register: (email = '') =>
    api.post('/auth/register/', { email }).then((r) => r.data),
  profile: () => api.get('/auth/profile/').then((r) => r.data),
  updateProfile: (data) => api.patch('/auth/profile/', data).then((r) => r.data),
  changePassword: (old_password, new_password) =>
    api.post('/auth/change-password/', { old_password, new_password }).then((r) => r.data),
};

export const itemsApi = {
  list: (params) => api.get('/items/', { params }).then((r) => r.data),
  get: (id) => api.get(`/items/${id}/`).then((r) => r.data),
  reviews: (id) => api.get(`/items/${id}/reviews/`).then((r) => r.data),
  addReview: (id, text, rating) =>
    api.post(`/items/${id}/reviews/`, { text, rating }).then((r) => r.data),
};

export const walletApi = {
  get: () => api.get('/wallet/').then((r) => r.data),
  deposit: (amount) => api.post('/wallet/deposit/', { amount }).then((r) => r.data),
  transfer: (recipient, amount) => api.post('/wallet/transfer/', { recipient, amount }).then((r) => r.data),
  transactions: () => api.get('/wallet/transactions/').then((r) => r.data),
};

export const voucherApi = {
  claim: (code) => api.post('/vouchers/claim/', { code }).then((r) => r.data),
};

export const inventoryApi = {
  list: () => api.get('/inventory/').then((r) => r.data),
  send: (inventoryId, recipient, quantity) =>
    api.post('/inventory/send/', { inventory_id: inventoryId, recipient, quantity }).then((r) => r.data),
  trade: (myInventoryId, myQuantity, theirUsername, theirInventoryId, theirQuantity) =>
    api.post('/inventory/trade/', {
      my_inventory_id: myInventoryId,
      my_quantity: myQuantity,
      their_username: theirUsername,
      their_inventory_id: theirInventoryId,
      their_quantity: theirQuantity,
    }).then((r) => r.data),
  userInventory: (username) => api.get(`/inventory/user/${username}/`).then((r) => r.data),
};

export const cartApi = {
  get: () => api.get('/cart/').then((r) => r.data),
  add: (itemId, quantity = 1) =>
    api.post('/cart/add/', { item_id: itemId, quantity }).then((r) => r.data),
  update: (cartItemId, quantity) =>
    api.patch(`/cart/${cartItemId}/`, { quantity }).then((r) => r.data),
  remove: (cartItemId) => api.delete(`/cart/${cartItemId}/`),
};

export const ordersApi = {
  list: () => api.get('/orders/').then((r) => r.data),
  get: (id) => api.get(`/orders/${id}/`).then((r) => r.data),
  create: () => api.post('/orders/').then((r) => r.data),
  exportOrders: (filename) => api.post('/orders/export/', { filename }).then((r) => r.data),
};

export const toolsApi = {
  previewTemplate: (template) => api.post('/preview/', { template }).then((r) => r.data),
  validateImage: (url) => api.post('/items/validate-image/', { url }).then((r) => r.data),
  downloadFile: (path) => `${API_BASE}/files/download/?path=${encodeURIComponent(path)}`,
};

export const gameApi = {
  submitScore: (spells) => api.post('/game/submit/', { spells }).then((r) => r.data),
};

export const passwordApi = {
  checkUsername: (username) => api.post('/auth/check-username/', { username }).then((r) => r.data),
  forgotPassword: (username) => api.post('/auth/forgot-password/', { username }).then((r) => r.data),
  verifyOtp: (username, code, new_password) =>
    api.post('/auth/verify-otp/', { username, code, new_password }).then((r) => r.data),
};

export default api;
