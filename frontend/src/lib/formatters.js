const isFiniteNumber = (value) => {
  const numeric = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(numeric) ? numeric : null;
};

const formatNumber = (value, { digits = 2, fallback = '-' } = {}) => {
  const numeric = isFiniteNumber(value);
  return numeric === null ? fallback : numeric.toFixed(digits);
};

const formatCurrency = (
  value,
  { digits = 2, prefix = '$', fallback = '-' } = {}
) => {
  const numeric = isFiniteNumber(value);
  return numeric === null ? fallback : `${prefix}${numeric.toFixed(digits)}`;
};

const formatPercent = (value, { digits = 2, showPlus = false, fallback = '-' } = {}) => {
  const numeric = isFiniteNumber(value);
  if (numeric === null) {
    return fallback;
  }
  const sign = showPlus && numeric > 0 ? '+' : '';
  return `${sign}${numeric.toFixed(digits)}%`;
};

const formatDateTime = (value, { locale, fallback = '-' } = {}) => {
  if (!value) {
    return fallback;
  }
  const parsed = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return fallback;
  }
  return parsed.toLocaleString(locale);
};

export { formatNumber, formatCurrency, formatPercent, formatDateTime };
