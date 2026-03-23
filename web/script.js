// ============================================================
//  MARRY — Personal AI Assistant (v4.0)
// ============================================================

// ============== TIME & GREETING ==============
(function initGreeting() {
    const greetingEl = document.getElementById('greeting');
    const updateTime = () => {
        const now = new Date();
        const hours = now.getHours();
        
        // Dynamic Greeting
        if (hours < 12) greetingEl.textContent = "Good Morning, User!";
        else if (hours < 18) greetingEl.textContent = "Good Afternoon, User!";
        else greetingEl.textContent = "Good Evening, User!";

        // Clock display
        const clockEl = document.getElementById('clock');
        if (clockEl) {
            clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
        }
    };
    setInterval(updateTime, 1000);
    updateTime();
})();

// ============== MOUSE TRACKING (EYES) ==============
document.addEventListener('mousemove', (e) => {
    const eyes = document.querySelector('.orb-eyes');
    if (!eyes) return;
    
    const x = (e.clientX / window.innerWidth - 0.5) * 20;
    const y = (e.clientY / window.innerHeight - 0.5) * 15;
    
    eyes.style.transform = `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
});

// ============== WAVE CANVAS (VISUALIZER) ==============
const canvas = document.getElementById('waveCanvas');
const ctx = canvas.getContext('2d');
let isActive = false;
let particles = [];

function resize() {
    if (!canvas) return;
    canvas.width = canvas.parentElement.offsetWidth;
    canvas.height = canvas.parentElement.offsetHeight;
}
window.addEventListener('resize', resize);
resize();

class Particle {
    constructor() {
        this.reset();
    }
    reset() {
        this.x = Math.random() * canvas.width;
        this.y = canvas.height / 2;
        this.baseY = this.y;
        this.size = Math.random() * 3 + 1;
        this.speedX = (Math.random() - 0.5) * 1.5;
        this.angle = Math.random() * Math.PI * 2;
        this.amplitude = Math.random() * 40 + 10;
        this.freq = 0.05 + Math.random() * 0.05;
        this.color = Math.random() > 0.5 ? 'rgba(157, 141, 242, 0.4)' : 'rgba(163, 204, 244, 0.4)'; 
    }
    update() {
        this.x += this.speedX;
        let currentAmp = isActive ? this.amplitude * 2.5 : this.amplitude * 0.2;
        this.y = this.baseY + Math.sin(this.angle) * currentAmp;
        this.angle += (isActive ? 0.15 : 0.04);
        if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
    }
    draw() {
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

for (let i = 0; i < 200; i++) particles.push(new Particle());

function animate() {
    if (!canvas) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(animate);
}
animate();

// ============== DJANGO API SYNC ==============
let prevStatus = '';
let prevQuery = '';

// Polling for state every 500ms
setInterval(() => {
    fetch('/api/state')
        .then(r => r.json())
        .then(data => {
            // Update status if changed
            if (data.status !== prevStatus) {
                update_status(data.status);
                prevStatus = data.status;
            }

            // Update transcription if changed
            if (data.query !== prevQuery) {
                update_query(data.query);
                prevQuery = data.query;
            }

            // Update knowledge panel
            if (data.knowledge && data.knowledge.content !== "Awaiting Query...") {
                update_knowledge(data.knowledge.title, data.knowledge.content);
            }

            // Append new logs
            if (data.new_logs && data.new_logs.length > 0) {
                data.new_logs.forEach(log => update_log(log.speaker, log.text));
            }
        })
        .catch(err => console.error("API Error:", err));
}, 500);

// Update overall UI state (Status, Orb animation, Mic state)
function update_status(status) {
    const statusEl = document.getElementById('status');
    const globe = document.getElementById('globe');
    const micBtn = document.getElementById('mic-btn');
    const hdrStatus = document.getElementById('headerStatus');

    if (statusEl) statusEl.textContent = status.toUpperCase();
    if (hdrStatus) hdrStatus.textContent = status.toUpperCase();

    const active = status.toLowerCase().includes("listen") || 
                   status.toLowerCase().includes("process") || 
                   status.toLowerCase().includes("speak") ||
                   status.toLowerCase().includes("initialize");

    isActive = active;
    if (globe) globe.classList.toggle('active', active);
    if (micBtn) micBtn.classList.toggle('listening', active);
}

// Log assistant/user activity in the sidebar
function update_log(speaker, text) {
    const term = document.getElementById('terminalLog');
    if (!term) return;
    const p = document.createElement('p');
    if (speaker === "You") {
        p.innerHTML = `<span style="color:#2d2d4d; font-weight:700;">[USER]</span> ${text}`;
    } else if (speaker === "System") {
        p.innerHTML = `<span class="log-sys">[SYS]</span> ${text}`;
    } else {
        p.innerHTML = `<span style="color:#8b5cf6; font-weight:700;">[MARRY]</span> ${text}`;
    }
    term.appendChild(p);
    term.scrollTop = term.scrollHeight;
}

// Update the intelligence panel on the right
function update_knowledge(title, content) {
    const titleEl = document.getElementById('knock-title');
    const contentEl = document.getElementById('knock-content');
    const webStatus = document.getElementById('webStatus');

    if (titleEl) titleEl.textContent = title;
    if (contentEl) contentEl.textContent = content;
    
    if (webStatus) {
        webStatus.textContent = "UPDATING";
        webStatus.style.color = "#8b5cf6";
        setTimeout(() => {
            webStatus.textContent = "STANDBY";
            webStatus.style.color = "";
        }, 3000);
    }
}

// Update the transcription text (center bottom)
function update_query(q) {
    const tranEl = document.getElementById('transcription');
    if (tranEl) tranEl.textContent = q;
}

// ============== USER ACTIONS ==============
function toggleListening() {
    fetch('/api/toggle_listen')
        .then(r => r.json())
        .then(data => {
            console.log("Toggle success:", data);
        })
        .catch(err => {
            console.error("Toggle error:", err);
        });
}

// Send a manual command via API (for quick actions or text input)
function send_manual_command(cmd) {
    if (!cmd) return;
    fetch('/api/send_command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd })
    })
    .then(r => r.json())
    .catch(err => console.error("Send command error:", err));
}

// Allow clicking the orb to start listening
document.addEventListener('DOMContentLoaded', () => {
    const orb = document.getElementById('globe');
    if (orb) {
        orb.addEventListener('click', toggleListening);
    }

    // Attach listeners to Quick Action cards
    const actionCards = document.querySelectorAll('.action-card');
    actionCards.forEach(card => {
        card.addEventListener('click', () => {
            const cmdText = card.querySelector('p')?.textContent.toLowerCase();
            const titleText = card.querySelector('h4')?.textContent.toLowerCase();

            if (titleText.includes("web automation") || cmdText.includes("google") || cmdText.includes("youtube")) {
                if (cmdText.includes("google")) send_manual_command("open google");
                else send_manual_command("open youtube");
            } else if (titleText.includes("knowledge") || cmdText.includes("wikipedia")) {
                send_manual_command("wikipedia artificial intelligence");
            } else if (titleText.includes("media") || cmdText.includes("play") || cmdText.includes("spotify")) {
                if (cmdText.includes("on youtube") || titleText.includes("media player")) {
                    send_manual_command("play shape of you on youtube");
                } else {
                    send_manual_command("open spotify");
                }
            } else if (titleText.includes("system") || cmdText.includes("notepad") || cmdText.includes("calc") || cmdText.includes("word") || cmdText.includes("ppt") || cmdText.includes("figma")) {
                if (cmdText.includes("notepad")) send_manual_command("open notepad");
                else if (cmdText.includes("calc")) send_manual_command("open calculator");
                else if (cmdText.includes("word")) send_manual_command("open word");
                else if (cmdText.includes("ppt") || cmdText.includes("powerpoint")) send_manual_command("open powerpoint");
                else if (cmdText.includes("figma")) send_manual_command("open figma");
                else if (cmdText.includes("linkedin")) send_manual_command("open linkedin");
            }
        });
    });
});
