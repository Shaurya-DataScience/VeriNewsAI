/* State Management Module */
const getStorageItem = (key, fallback) => {
  if (typeof localStorage !== 'undefined') {
    return localStorage.getItem(key) || fallback;
  }
  return fallback;
};

export const state = {
  loading: false,
  history: JSON.parse(getStorageItem('verinews_history', '[]')),
  loadingTimers: [],
  theme: getStorageItem('theme', 'dark'),
  faviconCache: new Map(),
  currentResult: null
};

export function saveRecentSearch(claim, verdict, confidence) {
  if (!claim) return;
  const item = { claim, verdict, confidence, timestamp: new Date().toISOString() };
  state.history = [item, ...state.history.filter(h => h.claim !== claim)].slice(0, 10);
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('verinews_history', JSON.stringify(state.history));
  }
}
