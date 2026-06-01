export default function PageSkeleton({ type = 'grid' }) {
  if (type === 'grid') {
    return (
      <div className="page">
        <div className="skeleton skeleton-title" />
        <div className="skeleton skeleton-subtitle" />
        <div className="item-grid">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="item-card skeleton-card">
              <div className="skeleton skeleton-img" />
              <div className="skeleton skeleton-text w-3" />
              <div className="skeleton skeleton-text w-2" />
              <div className="skeleton skeleton-text w-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }
  return (
    <div className="page">
      <div className="skeleton skeleton-title" />
      <div className="skeleton skeleton-block" />
      <div className="skeleton skeleton-block" />
    </div>
  );
}
