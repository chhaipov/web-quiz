const RARITY_COLORS = {
  common: '#9ca3af',
  uncommon: '#22c55e',
  rare: '#3b82f6',
  legendary: '#daa520',
};

export default function RarityBadge({ rarity }) {
  const color = RARITY_COLORS[rarity] || RARITY_COLORS.common;
  const label = rarity ? rarity.charAt(0).toUpperCase() + rarity.slice(1) : 'Common';
  return (
    <span className="rarity-badge" style={{ '--rarity-color': color }}>
      {label}
    </span>
  );
}
