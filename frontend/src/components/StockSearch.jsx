import React from "react";
import { Search } from "lucide-react";

export default function StockSearch({ stocks, selected, onSelect, search, onSearch }) {
  const filtered = stocks.filter((stock) => stock.symbol.toLowerCase().includes(search.toLowerCase()));
  return (
    <section className="stockSelector" aria-label="Stock selector">
      <label className="fieldLabel" htmlFor="stock-search">Search stock</label>
      <div className="searchBox">
        <Search size={18} />
        <input
          id="stock-search"
          value={search}
          onChange={(event) => onSearch(event.target.value)}
          placeholder="RELIANCE"
          autoComplete="off"
        />
      </div>
      <label className="fieldLabel" htmlFor="stock-select">Select stock</label>
      <select id="stock-select" value={selected} onChange={(event) => onSelect(event.target.value)}>
        {filtered.map((stock) => (
          <option key={stock.symbol} value={stock.symbol}>
            {stock.symbol}
          </option>
        ))}
      </select>
    </section>
  );
}
