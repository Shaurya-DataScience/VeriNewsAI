import { state, saveRecentSearch } from '../src/js/state.js';
import { generateSocialShareCard } from '../src/js/exports.js';

function assert(condition, message) {
  if (!condition) {
    console.error(`❌ TEST FAILED: ${message}`);
    process.exit(1);
  }
}

console.log("=== Running Frontend ES Module Unit Tests ===");

// Test 1: Default State
assert(state.theme === 'light' || state.theme === 'dark', "Theme initialized");
assert(Array.isArray(state.history), "History array initialized");
console.log("  ✓ State initialization test passed");

// Test 2: Recent Search
saveRecentSearch("NASA discovered water on Mars", "SUPPORTED", 98);
assert(state.history.length > 0, "History has items");
assert(state.history[0].claim === "NASA discovered water on Mars", "First claim matches");
console.log("  ✓ Save recent search test passed");

// Test 3: Canvas Data URL
const dataUrl = generateSocialShareCard("Test Claim Text", "SUPPORTED", 95);
assert(typeof dataUrl === 'string' && dataUrl.startsWith('data:image/png;base64,'), "Social card PNG generated");
console.log("  ✓ Social card PNG generator test passed");

console.log("\n✅ ALL FRONTEND ES MODULE TESTS PASSED PERFECTLY!");
