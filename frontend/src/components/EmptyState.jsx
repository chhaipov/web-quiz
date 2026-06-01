import { Link } from 'react-router-dom';

export default function EmptyState({ title, description, actionLabel = 'Browse items', actionHref = '/' }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">🛒</div>
      <h2>{title}</h2>
      <p>{description}</p>
      <Link to={actionHref} className="btn btn-primary">
        {actionLabel}
      </Link>
    </div>
  );
}
