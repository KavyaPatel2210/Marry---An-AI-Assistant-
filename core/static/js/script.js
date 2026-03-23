// ============== WAVE CANVAS ==============
const canvas = document.getElementById('waveCanvas');
const ctx = canvas.getContext('2d');
let isActive = false;
let particles = [];

function resizeCanvas() {
    const wrapper = canvas.parentElement;
    canvas.width  = wrapper.offsetWidth * 1.3;
    canvas.height = wrapper.offsetHeight * 1.3;
    canvas.style.left = `-${(canvas.width  - wrapper.offsetWidth)  / 2}px`;
    canvas.style.top  = `-${(canvas.height - wrapper.offsetHeight) / 2}px`;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

class Particle {
    constructor() { this.reset(); }
    reset() {
        this.x = Math.random() * canvas.width;
        this.baseY = canvas.height / 2;
        this.y = this.baseY;
        this.size = Math.random() * 2.5 + 0.5;
        this.speedX = (Math.random() - 0.5) * 1.5;
        this.angle  = Math.random() * Math.PI * 2;
        this.freq   = Math.random() * 0.06 + 0.02;
        this.amp    = Math.random() * 60 + 20;
        this.hue    = Math.random() > 0.5 ? '0,255,136' : '0,200,255';
    }
    update() {
        this.x += this.speedX;
        const amp = isActive ? this.amp * 1.6 : this.amp * 0.25;
        this.y = this.baseY + Math.sin(this.angle) * amp;
        this.angle += isActive ? this.freq * 2.5 : this.freq;
        if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
    }
    draw() {
        const alpha = isActive ? 0.85 : 0.25;
        ctx.fillStyle = `rgba(${this.hue},${alpha})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

for (let i = 0; i < 400; i++) particles.push(new Particle());

function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(animate);
}
animate();

// ============== CLOCK ==============
function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2,'0');
    const m = String(now.getMinutes()).padStart(2,'0');
    const s = String(now.getSeconds()).padStart(2,'0');
    const el = document.getElementById('clock');
    if (el) el.textContent = `${h}:${m}:${s}`;
}
setInterval(updateClock, 1000);
updateClock();

// ============== SESSION TIMER ==============
let sessionStarted = false;
let sessionSeconds = 0;
function startSessionTimer() {
    if (sessionStarted) return;
    sessionStarted = true;
    setInterval(() => {
        sessionSeconds++;
        const m = String(Math.floor(sessionSeconds/60)).padStart(2,'0');
        const s = String(sessionSeconds % 60).padStart(2,'0');
        const el = document.getElementById('sessionTime');
        if (el) el.textContent = `${m}:${s}`;
    }, 1000);
}

// ============== Stats ==============
let commandCount = 0;
function incCommand() {
    commandCount++;
    const el = document.getElementById('commandCount');
    if (el) el.textContent = commandCount;
}

// ============== LOG ==============
function addLog(speaker, text) {
    const term = document.getElementById('terminalLog');
    const p = document.createElement('p');
    if (speaker === 'You') {
        p.innerHTML = `<span class="log-user">[YOU]</span> ${text}`;
        incCommand();
    } else if (speaker === 'System') {
        p.innerHTML = `<span class="log-sys">[SYS]</span> ${text}`;
    } else {
        p.innerHTML = `<span class="log-aura">[AURA]</span> ${text}`;
    }
    term.appendChild(p);
    term.scrollTop = term.scrollHeight;
}

// ============== STATUS UPDATE ==============
function setStatus(status) {
    const statusEl   = document.getElementById('status');
    const headerStat = document.getElementById('headerStatus');
    const hexCore    = document.getElementById('hexCore');
    const micBtn     = document.getElementById('mic-btn');
    const micDot     = document.getElementById('micDot');
    const micStat    = document.getElementById('micStatus');
    const hcInner    = hexCore ? hexCore.querySelector('.hc-inner') : null;

    if (statusEl)   statusEl.textContent   = status.toUpperCase();
    if (headerStat) headerStat.textContent = status.toUpperCase();

    const active = status.toLowerCase().includes('listen') ||
                   status.toLowerCase().includes('process') ||
                   status.toLowerCase().includes('speak');

    isActive = active;
    if (hcInner) hcInner.classList.toggle('active', active);
    if (micBtn)  micBtn.classList.toggle('listening', active);

    // Mic module indicator
    if (status.toLowerCase().includes('standby') || status.toLowerCase().includes('offline') || status.toLowerCase().includes('initialize')) {
        if (micDot)  { micDot.className  = 'module-dot red'; }
        if (micStat) { micStat.textContent = 'OFFLINE'; micStat.className = 'module-status red-text'; }
    } else {
        if (micDot)  { micDot.className  = 'module-dot green'; }
        if (micStat) { micStat.textContent = 'ONLINE'; micStat.className = 'module-status green-text'; }
    }
}

// ============== KNOWLEDGE PANEL ==============
function setKnowledge(title, content) {
    const titleEl   = document.getElementById('knock-title');
    const contentEl = document.getElementById('knock-content');
    const webDot    = document.getElementById('webDot');
    const webStat   = document.getElementById('webStatus');

    if (titleEl)   titleEl.textContent   = title;
    if (contentEl) contentEl.textContent = content;

    // flash
    if (webDot)  { webDot.className  = 'module-dot green'; webDot.style.background  = '#00c8ff'; }
    if (webStat) { webStat.textContent = 'ACTIVE'; webStat.className = 'module-status blue-text'; }
    setTimeout(() => {
        if (webDot)  { webDot.className  = 'module-dot yellow'; webDot.style.background = ''; }
        if (webStat) { webStat.textContent = 'STANDBY'; webStat.className = 'module-status yellow-text'; }
    }, 3000);
}

// ============== AJAX POLLING (every 500ms) ==============
let prevStatus = '';
let prevQuery  = '';

setInterval(() => {
    fetch('/api/state')
        .then(r => r.json())
        .then(data => {
            if (data.status !== prevStatus) {
                setStatus(data.status);
                prevStatus = data.status;
            }
            const tranEl = document.getElementById('transcription');
            if (tranEl && data.query !== prevQuery) {
                tranEl.textContent = data.query;
                prevQuery = data.query;
            }
            if (data.knowledge) {
                setKnowledge(data.knowledge.title, data.knowledge.content);
            }
            if (data.new_logs && data.new_logs.length > 0) {
                data.new_logs.forEach(log => addLog(log.speaker, log.text));
            }
        })
        .catch(() => {}); // silent fail
}, 500);

// ============== MIC TOGGLE ==============
function toggleListening() {
    startSessionTimer();
    fetch('/api/toggle_listen')
        .then(r => r.json())
        .then(() => {})
        .catch(() => {});
}
