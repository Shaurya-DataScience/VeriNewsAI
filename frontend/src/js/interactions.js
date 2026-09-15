/* User Interaction & Event Handlers Module */
export function initHeroMouseTracking() {
  const hero = document.getElementById("hero-header");
  if (!hero) return;

  hero.addEventListener("mousemove", (e) => {
    hero.style.setProperty("--mouse-x", `${e.clientX}px`);
    hero.style.setProperty("--mouse-y", `${e.clientY}px`);
  });
}

export function initFocusTrap(modalElement) {
  if (!modalElement) return;

  const focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  
  modalElement.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;

    const focusables = modalElement.querySelectorAll(focusableSelectors);
    if (!focusables.length) return;

    const first = focusables[0];
    const last = focusables[focusables.length - 1];

    if (e.shiftKey) {
      if (document.activeElement === first) {
        last.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === last) {
        first.focus();
        e.preventDefault();
      }
    }
  });
}

export function initDrawerSwipe(drawerElement, closeCallback) {
  if (!drawerElement) return;

  let startX = 0;
  drawerElement.addEventListener("touchstart", (e) => {
    startX = e.touches[0].clientX;
  }, { passive: true });

  drawerElement.addEventListener("touchend", (e) => {
    const endX = e.changedTouches[0].clientX;
    if (endX - startX > 80) { // Swipe right to close
      if (closeCallback) closeCallback();
    }
  }, { passive: true });
}
