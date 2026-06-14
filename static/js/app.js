/* UserVault — Frontend JS */

/* ── Search / filter ─────────────────────────────── */
const searchInput = document.getElementById("search");
if (searchInput) {
  searchInput.addEventListener("input", () => {
    const q = searchInput.value.toLowerCase();
    document.querySelectorAll(".user-row").forEach((row) => {
      const name  = row.querySelector(".td-name span")?.textContent.toLowerCase() || "";
      const email = row.querySelector(".td-email")?.textContent.toLowerCase() || "";
      row.style.display = name.includes(q) || email.includes(q) ? "" : "none";
    });
  });
}

/* ── Toast ───────────────────────────────────────── */
function showToast(msg, duration = 3000) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), duration);
}

/* ── Modal ───────────────────────────────────────── */
let pendingUserId   = null;
let pendingRowEl    = null;
let pendingUserName = null;

function deleteUser(userId, btnEl) {
  pendingUserId   = userId;
  pendingRowEl    = btnEl.closest("tr");
  pendingUserName = pendingRowEl.querySelector(".td-name span").textContent;

  document.getElementById("modal-body").textContent =
    `"${pendingUserName}" will be permanently removed.`;

  openModal();
}

function openModal() {
  document.getElementById("modal-backdrop").classList.add("open");
}

function closeModal() {
  document.getElementById("modal-backdrop").classList.remove("open");
  pendingUserId = pendingRowEl = pendingUserName = null;
}

// Close on backdrop click
document.getElementById("modal-backdrop").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) closeModal();
});

// Confirm delete
document.getElementById("modal-confirm").addEventListener("click", async () => {
  if (!pendingUserId) return;

  const id   = pendingUserId;
  const row  = pendingRowEl;
  const name = pendingUserName;

  closeModal();

  try {
    const res = await fetch(`/delete/${id}`, { method: "DELETE" });
    const data = await res.json();

    if (data.ok) {
      // Animate row out
      row.classList.add("removing");
      row.addEventListener("animationend", () => row.remove(), { once: true });

      // Update counter
      const counter = document.getElementById("total-count");
      if (counter) counter.textContent = parseInt(counter.textContent) - 1;

      showToast(`✓ ${name} deleted successfully`);
    } else {
      showToast(`⚠ ${data.error || "Delete failed"}`);
    }
  } catch (err) {
    showToast("⚠ Network error. Please try again.");
    console.error(err);
  }
});

/* ── Auto-dismiss flash messages ─────────────────── */
document.querySelectorAll(".flash").forEach((el) => {
  setTimeout(() => {
    el.style.transition = "opacity .5s, transform .5s";
    el.style.opacity = "0";
    el.style.transform = "translateY(-6px)";
    setTimeout(() => el.remove(), 500);
  }, 4000);
});
