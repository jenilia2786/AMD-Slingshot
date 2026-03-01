// ===== AccelerateAI - Shared Utilities =====

const API_BASE = `http://${window.location.hostname}:8000/api`;

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
    <span>${message}</span>
    <span class="toast-close" onclick="closeToast(this.parentElement)">✕</span>
  `;
  container.appendChild(toast);
  setTimeout(() => closeToast(toast), 4000);
}

function closeToast(toast) {
  toast.classList.add('hiding');
  setTimeout(() => toast.remove(), 300);
}

// ===== LOADER =====
function showLoader(text = 'Loading...') {
  let overlay = document.getElementById('loader-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'loader-overlay';
    overlay.className = 'loader-overlay';
    overlay.innerHTML = `<div class="spinner"></div><div class="loader-text">${text}</div>`;
    document.body.appendChild(overlay);
  } else {
    overlay.querySelector('.loader-text').textContent = text;
    overlay.style.display = 'flex';
  }
}

function hideLoader() {
  const overlay = document.getElementById('loader-overlay');
  if (overlay) overlay.style.display = 'none';
}

// ===== MODAL =====
function openModal(content, title = '') {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal-box">
      ${title ? `<div class="modal-header"><h2 class="modal-title">${title}</h2><span class="modal-close" onclick="closeModal(this)">✕</span></div>` : ''}
      ${content}
    </div>
  `;
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
  document.addEventListener('keydown', function esc(e) {
    if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', esc); }
  });
  document.body.appendChild(overlay);
  return overlay;
}

function closeModal(el) {
  el.closest('.modal-overlay').remove();
}

// ===== COUNTER ANIMATION =====
function animateCounter(element, start, end, duration = 2000, prefix = '', suffix = '') {
  const startTime = performance.now();
  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.floor(start + (end - start) * eased);
    element.textContent = prefix + current.toLocaleString('en-US') + suffix;
    if (progress < 1) requestAnimationFrame(update);
    else element.textContent = prefix + end.toLocaleString('en-US') + suffix;
  }
  requestAnimationFrame(update);
}

// ===== CIRCULAR PROGRESS =====
function createProgressRing(value, size = 120, color = '#1E40AF', label = '') {
  const r = (size - 12) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (value / 100) * circ;
  const textColor = value >= 75 ? '#059669' : value >= 50 ? '#F59E0B' : '#DC2626';
  return `
    <div class="progress-ring" style="width:${size}px;height:${size}px;">
      <svg width="${size}" height="${size}">
        <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="#E5E7EB" stroke-width="8"/>
        <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="${color}" stroke-width="8"
          stroke-dasharray="${circ}" stroke-dashoffset="${offset}" stroke-linecap="round"/>
      </svg>
      <div class="progress-value" style="font-size:${size * 0.18}px;color:${textColor};">${value}</div>
    </div>
    ${label ? `<div style="font-size:12px;color:#6B7280;text-align:center;margin-top:4px;font-weight:600;">${label}</div>` : ''}
  `;
}

// ===== API CALLS =====
async function apiCall(endpoint, method = 'GET', body = null) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const options = { method, headers };
  if (body) {
    if (body instanceof FormData) {
      delete headers['Content-Type'];
      options.body = body;
    } else {
      options.body = JSON.stringify(body);
    }
  }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await res.json();
    if (!res.ok) {
      let msg = 'Request failed';
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          msg = data.detail.map(e => e.msg || e).join(', ');
        } else {
          msg = data.detail;
        }
      }
      throw new Error(msg);
    }
    return data;
  } catch (err) {
    throw err;
  }
}

// ===== AUTH HELPERS =====
function getToken() { return localStorage.getItem('token'); }
function getUser() {
  const u = localStorage.getItem('user');
  return u ? JSON.parse(u) : null;
}
function setAuth(token, user) {
  localStorage.setItem('token', token);
  localStorage.setItem('user', JSON.stringify(user));
}
function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = '/';
}
function requireAuth(role) {
  const token = getToken();
  const user = getUser();
  if (!token || !user) {
    const redirects = { student: '/student/login.html', company: '/company/login.html', government: '/government/login.html' };
    window.location.href = redirects[role] || '/';
    return false;
  }
  return user;
}

// ===== SKELETON LOADERS =====
function skeletonCard() {
  return `<div class="card-flat">
    <div class="skeleton skeleton-line medium"></div>
    <div class="skeleton skeleton-line long" style="margin-top:8px;"></div>
    <div class="skeleton skeleton-line short" style="margin-top:8px;"></div>
    <div class="skeleton" style="height:80px;margin-top:12px;border-radius:8px;"></div>
  </div>`;
}

function renderSkeletons(container, count = 6) {
  container.innerHTML = Array(count).fill(skeletonCard()).join('');
}

// ===== FORMAT HELPERS =====
function formatCurrency(n) {
  if (n >= 1000000) return '$' + (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return '$' + (n / 1000).toFixed(1) + 'K';
  return '$' + n.toLocaleString('en-US');
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
}

function daysLeft(deadline) {
  const d = Math.ceil((new Date(deadline) - new Date()) / (1000 * 60 * 60 * 24));
  return d > 0 ? d + ' days left' : 'Expired';
}

function difficultyBadge(d) {
  const map = { Easy: 'green', Medium: 'gold', Hard: 'red' };
  return `<span class="badge badge-${map[d] || 'gray'}">${d}</span>`;
}

// ===== DEBOUNCE =====
function debounce(fn, delay = 300) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

// ===== PAGE FADE IN =====
document.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('page-fade');
  // Inject toast container
  if (!document.getElementById('toast-container')) {
    const tc = document.createElement('div');
    tc.id = 'toast-container';
    document.body.appendChild(tc);
  }
});
