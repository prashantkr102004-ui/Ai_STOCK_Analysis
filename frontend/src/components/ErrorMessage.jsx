import React from "react";

export default function ErrorMessage({ title = "Something went wrong", message }) {
  if (!message) return null;
  return (
    <div className="error" role="alert">
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  );
}
