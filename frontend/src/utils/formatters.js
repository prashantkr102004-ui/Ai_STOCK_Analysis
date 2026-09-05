export function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(Number(value));
}

export function formatNumber(value, options = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  return new Intl.NumberFormat("en-IN", options).format(Number(value));
}

export function formatPercent(value, alreadyPercent = false) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  const percent = alreadyPercent ? Number(value) : Number(value) * 100;
  return `${percent.toFixed(2)}%`;
}

export function formatProbability(value) {
  return formatPercent(value, false);
}

export function formatDate(value) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "2-digit"
  });
}

export function formatCompact(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  return new Intl.NumberFormat("en-IN", {
    notation: "compact",
    maximumFractionDigits: 2
  }).format(Number(value));
}
