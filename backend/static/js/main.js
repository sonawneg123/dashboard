/* NexusDB — Frontend JS */

/* ── Sidebar mobile toggle ───────────────────────── */
const sidebar  = document.getElementById('sidebar');
const hamburger = document.getElementById('topbar-hamburger');
const sideClose = document.getElementById('sidebar-close');

hamburger?.addEventListener('click', () => sidebar.classList.toggle('open'));
sideClose?.addEventListener('click', () => sidebar.classList.remove('open'));

document.addEventListener('click', (e) => {
  if (sidebar.classList.contains('open') &&
      !sidebar.contains(e.target) &&
      !hamburger.contains(e.target)) {
    sidebar.classList.remove('open');
  }
});

/* ── Modal ───────────────────────────────────────── */
const backdrop = document.getElementById('modal-backdrop');

function openModal() {
  backdrop.classList.add('open');
  backdrop.setAttribute('aria-hidden', 'false');
}

function closeModal() {
  backdrop.classList.remove('open');
  backdrop.setAttribute('aria-hidden', 'true');
}

// Close on backdrop click
backdrop?.addEventListener('click', (e) => {
  if (e.target === backdrop) closeModal();
});

// Close on Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});

/* ── Toast ───────────────────────────────────────── */
function showToast(msg, type = 'success', duration = 3500) {
  const region = document.getElementById('toast-region');
  const item = document.createElement('div');
  item.className = `toast-item toast-item--${type}`;
  const icon = type === 'success' ? '✓' : '⚠';
  item.innerHTML = `<span>${icon}</span><span>${msg}</span>`;
  region.appendChild(item);
  setTimeout(() => {
    item.style.transition = 'opacity .4s, transform .4s';
    item.style.opacity = '0';
    item.style.transform = 'translateX(20px)';
    setTimeout(() => item.remove(), 400);
  }, duration);
}

/* ── Auto-dismiss flash messages ─────────────────── */
document.querySelectorAll('.flash').forEach((el) => {
  setTimeout(() => {
    el.style.transition = 'opacity .5s, max-height .5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  }, 5000);
});

/* ── Dynamic live search (AJAX) ──────────────────── */
let debounceTimer;
const searchInput = document.querySelector('.search-input');

if (searchInput) {
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      // Native form submit keeps URL query params clean
      searchInput.closest('form')?.submit();
    }, 450);
  });
}

/* ── Row click → view user ───────────────────────── */
document.querySelectorAll('.tr-user').forEach((row) => {
  row.addEventListener('click', (e) => {
    // Don't navigate if clicking a button or anchor
    if (e.target.closest('a, button, .action-group')) return;
    const uid = row.dataset.uid;
    if (uid) window.location.href = `/users/${uid}`;
  });
  row.style.cursor = 'pointer';
});

/* ── Inline status toggle via API ────────────────── */
async function toggleStatus(uid, current) {
  const next = current === 'active' ? 'inactive' : 'active';
  try {
    const res = await fetch(`/api/v1/users/${uid}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: next }),
    });
    if (res.ok) {
      showToast(`Status updated to "${next}".`, 'success');
      setTimeout(() => location.reload(), 600);
    } else {
      showToast('Failed to update status.', 'error');
    }
  } catch {
    showToast('Network error.', 'error');
  }
}

/* ── Keyboard shortcut: Ctrl+K → focus search ────── */
document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    searchInput?.focus();
  }
});
