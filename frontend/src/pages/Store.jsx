import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { itemsApi, cartApi } from '../api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import PageSkeleton from '../components/PageSkeleton';
import EmptyState from '../components/EmptyState';
import RarityBadge from '../components/RarityBadge';

const PAGE_SIZE = 12;

export default function Store() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState({ rarity: '', category: '' });
  const [search, setSearch] = useState('');
  const [ordering, setOrdering] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [addingId, setAddingId] = useState(null);
  const { isAuthenticated } = useAuth();
  const toast = useToast();

  const fetchItems = useCallback(() => {
    setLoading(true);
    setError(null);
    const params = { ...filter, page, page_size: PAGE_SIZE };
    if (search.trim()) params.search = search.trim();
    if (ordering) params.ordering = ordering;
    itemsApi
      .list(params)
      .then((data) => {
        if (data.results) {
          setItems(data.results);
          setTotalPages(data.total_pages);
          setTotalCount(data.count);
        } else {
          setItems(data);
          setTotalPages(1);
          setTotalCount(data.length);
        }
      })
      .catch((e) => {
        setError(e.response?.data?.detail || 'Failed to load items');
        setItems([]);
      })
      .finally(() => setLoading(false));
  }, [filter.rarity, filter.category, search, ordering, page]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const resetPage = () => setPage(1);

  const handleFilterChange = (key, value) => {
    setFilter((f) => ({ ...f, [key]: value }));
    resetPage();
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    resetPage();
  };

  const handleAddToCart = (itemId, name, qty = 1) => {
    if (!isAuthenticated) {
      toast.info('Please log in to add items to your cart');
      return;
    }
    setAddingId(itemId);
    cartApi
      .add(itemId, qty)
      .then(() => toast.success(`Added ${name} to cart`))
      .catch((e) => toast.error(e.response?.data?.detail || 'Failed to add to cart'))
      .finally(() => setAddingId(null));
  };

  return (
    <div className="page">
      <header className="page-header">
        <h1>Dota 2 Item Shop</h1>
        <p className="subtitle">
          Browse legendary items from the battlefield.
        </p>
      </header>

      {error && (
        <div className="alert alert-error" role="alert">
          {error}
        </div>
      )}

      <form className="store-toolbar" onSubmit={handleSearchSubmit}>
        <div className="search-box">
          <input
            type="search"
            placeholder="Search items…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search items"
          />
          <button type="submit" className="btn btn-sm">Search</button>
        </div>

        <div className="filters">
          <select
            value={filter.rarity}
            onChange={(e) => handleFilterChange('rarity', e.target.value)}
            aria-label="Filter by rarity"
          >
            <option value="">All rarities</option>
            <option value="common">Common</option>
            <option value="uncommon">Uncommon</option>
            <option value="rare">Rare</option>
            <option value="legendary">Legendary</option>
          </select>
          <select
            value={filter.category}
            onChange={(e) => handleFilterChange('category', e.target.value)}
            aria-label="Filter by category"
          >
            <option value="">All categories</option>
            <option value="core">Core</option>
            <option value="support">Support</option>
            <option value="neutral">Neutral</option>
            <option value="consumable">Consumable</option>
            <option value="hero_skin">Hero Skins</option>
          </select>
          <select
            value={ordering}
            onChange={(e) => { setOrdering(e.target.value); resetPage(); }}
            aria-label="Sort by"
          >
            <option value="">Default order</option>
            <option value="name">Name A-Z</option>
            <option value="-name">Name Z-A</option>
            <option value="price">Price low-high</option>
            <option value="-price">Price high-low</option>
            <option value="gold">Gold low-high</option>
            <option value="-gold">Gold high-low</option>
          </select>
        </div>
      </form>

      {loading ? (
        <PageSkeleton type="grid" />
      ) : items.length === 0 && !error ? (
        <EmptyState
          title="No items found"
          description="Try adjusting your filters or search."
          actionLabel="Clear filters"
          actionHref="/"
        />
      ) : (
        <>
          {/* VULN(Reflected XSS): renders search term as raw HTML */}
          {search && (
            <p className="results-count"
               dangerouslySetInnerHTML={{ __html: `Showing results for: <b>${search}</b>` }}
            />
          )}
          <p className="results-count">{totalCount} item{totalCount !== 1 ? 's' : ''} found</p>
          <div className="item-grid">
            {items.map((item) => (
              <article key={item.id} className="item-card">
                {item.image_src && (
                  <img
                    src={item.image_src}
                    alt=""
                    className="item-img"
                    loading="lazy"
                    onError={(e) => (e.target.style.display = 'none')}
                  />
                )}
                <div className="item-card-body">
                  <RarityBadge rarity={item.rarity} />
                  <h2 className="item-title">{item.name}</h2>
                  <div className="item-pricing">
                    <span className="gold">{item.gold_cost}g</span>
                    <span className="price">${item.usd_price}</span>
                  </div>
                  <p className="desc">{item.description?.slice(0, 90)}{item.description?.length > 90 ? '…' : ''}</p>
                </div>
                <div className="card-actions">
                  <Link to={`/item/${item.id}`} className="btn btn-sm">
                    Details
                  </Link>
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => handleAddToCart(item.id, item.name)}
                    disabled={addingId === item.id}
                    aria-label={`Add ${item.name} to cart`}
                  >
                    {addingId === item.id ? 'Adding…' : 'Add to Cart'}
                  </button>
                </div>
              </article>
            ))}
          </div>

          {totalPages > 1 && (
            <nav className="pagination" aria-label="Store pagination">
              <button
                className="btn btn-sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn-sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                Next
              </button>
            </nav>
          )}
        </>
      )}
    </div>
  );
}
