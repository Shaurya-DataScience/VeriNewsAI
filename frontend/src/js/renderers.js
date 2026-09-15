/* UI Rendering Module */
import { state } from './state.js';

const $ = (id) => document.getElementById(id);

export function renderConfidenceBreakdown(breakdown) {
  const container = $("confidence-bars-container");
  if (!container) return;

  const items = [
    { label: "Semantic Similarity", value: breakdown.semantic_similarity || 0, desc: "Neural vector alignment with verified archives" },
    { label: "Cross Encoder Rerank", value: breakdown.cross_encoder || 0, desc: "Sentence transformer deep semantic reranking score" },
    { label: "Source Credibility Index", value: breakdown.source_credibility || 0, desc: "Domain authority & journalistic trust index" },
    { label: "Date & Timeframe Verification", value: breakdown.date_verification || 100, desc: "Event timeline and publication recency alignment" },
    { label: "Evidence Consistency", value: breakdown.evidence_consistency || 0, desc: "Absence of contradiction across independent reporting" }
  ];

  container.innerHTML = items.map(item => `
    <div class="breakdown-item" data-tooltip="${item.desc}">
      <div class="item-label-row">
        <span>${item.label}</span>
        <strong style="color:var(--accent-cyan);font-family:var(--font-mono);">${Math.round(item.value)}%</strong>
      </div>
      <div class="item-bar-bg">
        <div class="item-bar-fill" style="width: ${Math.max(0, Math.min(100, Math.round(item.value)))}%;"></div>
      </div>
    </div>
  `).join('');
}

export function renderSourceCards(id, sources, openDrawerCallback) {
  const container = $(id);
  if (!container) return;

  container.innerHTML = "";

  if (!sources || !sources.length) {
    container.innerHTML = `<div class="empty-state-badge">No articles indexed for this category.</div>`;
    return;
  }

  sources.forEach((source, index) => {
    const card = document.createElement("div");
    card.className = "evidence-card";
    card.style.animation = "fadeIn 0.3s ease forwards";
    card.style.animationDelay = `${index * 0.08}s`;
    card.style.cursor = "pointer";

    let domain = source.domain || "";
    if (!domain && source.url) {
      try { domain = new URL(source.url).hostname.replace(/^www\./, ''); } catch (e) { domain = "news"; }
    }
    const faviconUrl = domain ? `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64` : "";
    const credScore = Math.round(source.credibility || 50);
    const relScore = Math.round(source.final_score || source.similarity || 0);

    card.innerHTML = `
      <div class="evidence-card-header">
        ${faviconUrl ? `<img src="${faviconUrl}" alt="${domain}" class="source-favicon" onerror="this.style.display='none'">` : ''}
        <div>
          <h4 class="source-title line-clamp-2">${source.title || domain || "Verified Article"}</h4>
          <span class="source-stars">${source.stars || "★★★★☆"}</span>
        </div>
      </div>
      <div class="source-badges">
        <span class="source-pill pill-credibility">${credScore}% Credibility</span>
        <span class="source-pill pill-relevance">${relScore}% Match</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.6rem;">
        <span class="source-link" style="font-size:0.8rem;color:var(--accent-cyan);font-weight:700;">Inspect Source 🔍</span>
        <a href="${source.url || '#'}" target="_blank" rel="noopener noreferrer" class="source-link" onclick="event.stopPropagation();">Original Link ↗</a>
      </div>
    `;

    if (openDrawerCallback) {
      card.addEventListener("click", () => openDrawerCallback(source));
    }
    container.appendChild(card);
  });

  // Batch icon hydration once per card set
  if (window.lucide?.createIcons) window.lucide.createIcons();
}
