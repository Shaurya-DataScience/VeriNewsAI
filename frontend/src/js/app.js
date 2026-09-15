/* Main Application Orchestration Entry Point */
import { state } from './state.js';
import { fetchVerification, fetchAdminStats, fetchAnalyticsSummary, saveAdminConfig } from './api.js';
import { renderConfidenceBreakdown, renderSourceCards } from './renderers.js';
import { initHeroMouseTracking, initFocusTrap, initDrawerSwipe } from './interactions.js';
import { shareFactCheckCard } from './exports.js';

console.log("VeriNews AI Enterprise ES Module Orchestrator Initialized 🚀");

document.addEventListener("DOMContentLoaded", () => {
  initHeroMouseTracking();
  fetchAnalyticsSummary();
});
