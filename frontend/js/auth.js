// ===== AccelerateAI - Auth Handler =====

// Real login handler
async function handleLogin(email, password, role) {
  showLoader('Signing you in...');
  try {
    const data = await apiCall('/auth/login', 'POST', { email, password, role });
    setAuth(data.token, data.user);
    showToast('Login successful! Redirecting...', 'success');

    setTimeout(() => {
      // Determine if we are in a subdirectory
      const isSubDir = window.location.pathname.includes('/student/') ||
        window.location.pathname.includes('/company/') ||
        window.location.pathname.includes('/government/') ||
        window.location.pathname.includes('/mentor/');

      const routes = isSubDir ? {
        student: 'dashboard.html',
        company: 'dashboard.html',
        government: 'dashboard.html',
        mentor: 'dashboard.html'
      } : {
        student: 'student/dashboard.html',
        company: 'company/dashboard.html',
        government: 'government/dashboard.html',
        mentor: 'mentor/dashboard.html'
      };

      window.location.href = routes[role] || (isSubDir ? '../index.html' : 'index.html');
    }, 800);
  } catch (err) {
    showToast(err.message || 'Login failed. Check credentials.', 'error');
  } finally {
    hideLoader();
  }
}
