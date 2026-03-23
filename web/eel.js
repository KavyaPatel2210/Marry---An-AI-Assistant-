// Polyfill for eel.js when running as static Django - logs to console instead of Eel
window.eel = {
  expose: function(func, name) { console.log('Exposed', name); },
  start: function() { console.log('Eel start polyfill'); }
};

function toggle_voice_assistant() {
  console.log('Django mic toggle called');
  fetch('/api/toggle_listen', {method: 'POST'})
    .then(() => getState());
}

function getState() {
  fetch('/api/state')
    .then(r => r.json())
    .then(updateUI);
}

function updateUI(data) {
  console.log('State:', data);
  // Update DOM based on data - adapt Marry UI functions
  const statusEl = document.getElementById('status');
  if (statusEl) statusEl.textContent = data.status || 'IDLE';
}

setInterval(getState, 2000);
