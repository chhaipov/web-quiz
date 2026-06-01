import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';

import Store from './pages/Store';
import ItemDetail from './pages/ItemDetail';
import Cart from './pages/Cart';
import Wallet from './pages/Wallet';
import Orders from './pages/Orders';
import OrderDetail from './pages/OrderDetail';
import Inventory from './pages/Inventory';
import Vouchers from './pages/Vouchers';
import Profile from './pages/Profile';
import Tools from './pages/Tools';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import InvokerGame from './pages/InvokerGame';
import NotFound from './pages/NotFound';
import './App.css';

function Nav() {
  const { isAuthenticated, user, logout } = useAuth();
  return (
    <header className="nav" role="banner">
      <div className="nav-inner">
        <Link to="/" className="nav-logo">
          Dota 2 Shop
        </Link>
        <nav className="nav-links" aria-label="Main navigation">
          <Link to="/">Store</Link>
          {isAuthenticated ? (
            <>
              <Link to="/cart">Cart</Link>
              <Link to="/wallet">Wallet</Link>
              <Link to="/inventory">Inventory</Link>
              <Link to="/vouchers">Vouchers</Link>
              <Link to="/orders">Orders</Link>
              <Link to="/tools">Tools</Link>
              <Link to="/invoker">Invoker</Link>
              <Link to="/profile" className="nav-user" aria-label={`Logged in as ${user?.username}`}>
                {user?.username}
              </Link>
              <button
                type="button"
                className="btn-link"
                onClick={logout}
                aria-label="Log out"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Log in</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="footer" role="contentinfo">
      <div className="footer-inner">
        <p>Dota 2 Item Shop</p>
        <p className="footer-muted">&copy; Dota 2 Item Shop</p>
      </div>
    </footer>
  );
}

function Layout({ children }) {
  const location = useLocation();
  const isAuthPage = ['/login', '/register', '/forgot-password'].includes(location.pathname);
  return (
    <div className="app-layout">
      <Nav />
      <main className={isAuthPage ? 'main main-center' : 'main'} role="main">
        {children}
      </main>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Store />} />
              <Route path="/item/:id" element={<ItemDetail />} />
              <Route path="/cart" element={<Cart />} />
              <Route path="/wallet" element={<Wallet />} />
              <Route path="/orders" element={<Orders />} />
              <Route path="/orders/:id" element={<OrderDetail />} />
              <Route path="/inventory" element={<Inventory />} />
              <Route path="/vouchers" element={<Vouchers />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/tools" element={<Tools />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/invoker" element={<InvokerGame />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
