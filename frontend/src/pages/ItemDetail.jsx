import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { itemsApi, cartApi } from '../api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import LoadingSpinner from '../components/LoadingSpinner';
import RarityBadge from '../components/RarityBadge';

export default function ItemDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [error, setError] = useState(null);
  const [qty, setQty] = useState(1);
  const [adding, setAdding] = useState(false);
  const [reviews, setReviews] = useState([]);
  const [reviewText, setReviewText] = useState('');
  const [reviewRating, setReviewRating] = useState(5);
  const [submitting, setSubmitting] = useState(false);
  const { isAuthenticated } = useAuth();
  const toast = useToast();

  useEffect(() => {
    setError(null);
    itemsApi
      .get(id)
      .then((data) => {
        setItem(data);
        setError(null);
      })
      .catch(() => setError('Item not found'));
    itemsApi.reviews(id).then(setReviews).catch(() => setReviews([]));
  }, [id]);

  const handleAdd = () => {
    if (!isAuthenticated) {
      toast.info('Please log in to add items to your cart');
      return;
    }
    setAdding(true);
    cartApi
      .add(item.id, qty)
      .then(() => {
        toast.success(`Added ${item.name} to cart`);
        navigate('/cart');
      })
      .catch((e) => toast.error(e.response?.data?.detail || 'Failed to add to cart'))
      .finally(() => setAdding(false));
  };

  const handleReview = (e) => {
    e.preventDefault();
    if (!reviewText.trim()) {
      toast.error('Please enter a review');
      return;
    }
    setSubmitting(true);
    itemsApi
      .addReview(id, reviewText, reviewRating)
      .then(() => {
        toast.success('Review submitted');
        setReviewText('');
        setReviewRating(5);
        itemsApi.reviews(id).then(setReviews).catch(() => {});
      })
      .catch((e) => toast.error(e.response?.data?.error || 'Failed to submit review'))
      .finally(() => setSubmitting(false));
  };

  if (error) {
    return (
      <div className="page">
        <div className="empty-state">
          <h2>{error}</h2>
          <Link to="/" className="btn btn-primary">
            Return to Store
          </Link>
        </div>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="page centered">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="page item-detail-page">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/">Store</Link>
        <span className="breadcrumb-sep">/</span>
        <span>{item.name}</span>
      </nav>

      <div className="detail-card">
        {item.image_src && (
          <img src={item.image_src} alt="" className="detail-img" />
        )}
        <div className="detail-info">
          <RarityBadge rarity={item.rarity} />
          <h1>{item.name}</h1>
          <div className="detail-meta">
            <span className="gold">{item.gold_cost} gold</span>
            <span className="price">${item.usd_price}</span>
            <span className="category">Category: {item.category}</span>
          </div>
          <p className="desc">{item.description}</p>
          <div className="add-row">
            <label htmlFor="qty-input" className="sr-only">Quantity</label>
            <input
              id="qty-input"
              type="number"
              min="1"
              max="99"
              value={qty}
              onChange={(e) => setQty(Math.max(1, Math.min(99, Number(e.target.value) || 1)))}
            />
            <button
              className="btn btn-primary"
              onClick={handleAdd}
              disabled={!isAuthenticated || adding}
            >
              {adding ? 'Adding…' : isAuthenticated ? 'Add to Cart' : 'Log in to Add'}
            </button>
          </div>
        </div>
      </div>

      <div className="card reviews-section">
        <h2 className="card-title">Reviews</h2>

        {isAuthenticated && (
          <form onSubmit={handleReview} className="review-form">
            <div className="form-group">
              <label htmlFor="review-rating">Rating</label>
              <select
                id="review-rating"
                value={reviewRating}
                onChange={(e) => setReviewRating(Number(e.target.value))}
                disabled={submitting}
              >
                <option value={5}>5 - Excellent</option>
                <option value={4}>4 - Good</option>
                <option value={3}>3 - Average</option>
                <option value={2}>2 - Poor</option>
                <option value={1}>1 - Terrible</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="review-text">Your Review</label>
              <textarea
                id="review-text"
                rows="3"
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                placeholder="Write your review..."
                disabled={submitting}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit Review'}
            </button>
          </form>
        )}

        {reviews.length === 0 ? (
          <p className="text-muted" style={{ marginTop: '1rem' }}>No reviews yet. Be the first!</p>
        ) : (
          <div className="reviews-list">
            {reviews.map((r) => (
              <div key={r.id} className="review-item">
                <div className="review-header">
                  <strong>{r.user}</strong>
                  <span className="gold">{r.rating}/5</span>
                  <time className="text-muted">{new Date(r.created_at).toLocaleDateString()}</time>
                </div>
                {/* VULN(Stored XSS): renders review text as raw HTML */}
                <p dangerouslySetInnerHTML={{ __html: r.text }} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
