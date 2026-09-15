/* Report Export & Social Share Module */
export function generateSocialShareCard(claim, verdict, confidence) {
  if (typeof document === 'undefined') {
    return `data:image/png;base64,mock_${Date.now()}`;
  }

  const canvas = document.createElement("canvas");
  canvas.width = 1200;
  canvas.height = 630;
  const ctx = canvas.getContext("2d");

  // Background
  const gradient = ctx.createLinearGradient(0, 0, 1200, 630);
  gradient.addColorStop(0, "#030712");
  gradient.addColorStop(1, "#0f172a");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 1200, 630);

  // Border Accent
  ctx.strokeStyle = "#6366f1";
  ctx.lineWidth = 8;
  ctx.strokeRect(20, 20, 1160, 590);

  // Header Brand
  ctx.fillStyle = "#38bdf8";
  ctx.font = "bold 36px Inter, sans-serif";
  ctx.fillText("VeriNews AI • Intelligence Verification Report", 60, 90);

  // Verdict Badge
  const isTrue = verdict.toUpperCase().includes("TRUE") || verdict.toUpperCase().includes("SUPPORTED");
  const verdictColor = isTrue ? "#10b981" : "#ef4444";
  ctx.fillStyle = verdictColor;
  ctx.fillRect(60, 140, 260, 60);

  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 28px Inter, sans-serif";
  ctx.fillText(verdict.toUpperCase(), 80, 180);

  // Confidence
  ctx.fillStyle = "#94a3b8";
  ctx.font = "24px Inter, sans-serif";
  ctx.fillText(`Multi-Factor Confidence: ${confidence}%`, 350, 180);

  // Claim Quote
  ctx.fillStyle = "#f8fafc";
  ctx.font = "italic 32px Inter, sans-serif";
  const displayClaim = claim.length > 100 ? claim.substring(0, 97) + "..." : claim;
  ctx.fillText(`"${displayClaim}"`, 60, 300);

  // Footer Tagline
  ctx.fillStyle = "#64748b";
  ctx.font = "20px JetBrains Mono, monospace";
  ctx.fillText("Verified by Cross-Encoder Neural Reranking & Global Evidence Alignment", 60, 540);

  return canvas.toDataURL("image/png");
}

export function shareFactCheckCard(claim, verdict, confidence) {
  const dataUrl = generateSocialShareCard(claim, verdict, confidence);
  if (typeof document !== 'undefined') {
    const link = document.createElement("a");
    link.download = `VeriNews_FactCheck_${Date.now()}.png`;
    link.href = dataUrl;
    link.click();
  }
}
