(function () {
  const key = 'agi-theme';
  const root = document.documentElement;
  const button = document.getElementById('theme-toggle');

  const stored = localStorage.getItem(key);
  if (stored === 'light' || stored === 'dark') {
    root.setAttribute('data-theme', stored);
  }

  if (button) {
    button.addEventListener('click', function () {
      const current = root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem(key, next);
    });
  }
})();
