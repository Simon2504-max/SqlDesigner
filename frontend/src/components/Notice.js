/**
 * Notice.js — Petit bandeau de message (succès ou erreur) qui disparaît tout seul.
 */
import React, { useEffect } from "react";

export default function Notice({ notice, onClose }) {
  useEffect(() => {
    if (!notice) return undefined;
    const delay = notice.type === "error" ? 8000 : 3500;
    const timer = setTimeout(onClose, delay);
    return () => clearTimeout(timer); // si un autre message arrive avant, on annule le minuteur
  }, [notice, onClose]);

  if (!notice) return null;
  return (
    <div className={`ed-notice ed-notice-${notice.type} ed-toast`} role="status">
      <span>{notice.text}</span>
      <button type="button" onClick={onClose} aria-label="Close">
        ✕
      </button>
    </div>
  );
}
