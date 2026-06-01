import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="page not-found-page">
      <div className="not-found-content">
        <span className="not-found-code">404</span>
        <h1>Page Not Found</h1>
        <p className="subtitle">The battle has moved. This page does not exist.</p>
        <Link to="/" className="btn btn-primary">
          Return to Store
        </Link>
      </div>
    </div>
  );
}
