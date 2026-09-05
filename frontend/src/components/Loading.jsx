import React from "react";

export default function Loading({ label = "Loading market intelligence..." }) {
  return <div className="loading">{label}</div>;
}
