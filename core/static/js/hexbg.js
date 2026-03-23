// ============== ANIMATED HEX BACKGROUND + NEURAL NETWORK ==============

// --- HEX BACKGROUND CANVAS ---
(function() {
    const canvas = document.getElementById('hexBg');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let W, H;
    function resize() {
        W = canvas.width  = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    function drawHex(x, y, r, alpha) {
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const angle = Math.PI / 3 * i - Math.PI / 6;
            const px = x + r * Math.cos(angle);
            const py = y + r * Math.sin(angle);
            i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.strokeStyle = `rgba(0,255,136,${alpha})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
    }

    const HEX_R = 32;
    const HW = HEX_R * Math.sqrt(3);
    const HH = HEX_R * 2;

    let t = 0;

    function drawHexGrid() {
        ctx.clearRect(0, 0, W, H);
        const cols = Math.ceil(W / HW) + 2;
        const rows = Math.ceil(H / (HH * 0.75)) + 2;

        for (let row = -1; row < rows; row++) {
            for (let col = -1; col < cols; col++) {
                const offsetX = (row % 2) * (HW / 2);
                const cx = col * HW + offsetX;
                const cy = row * (HH * 0.75);

                // Oscillating glow wave sweeping diagonally
                const wave = Math.sin((cx * 0.008) + (cy * 0.005) - t * 0.6);
                const alpha = 0.03 + wave * 0.04;

                if (alpha > 0.005) {
                    drawHex(cx, cy, HEX_R - 1, Math.max(0, alpha));
                }
            }
        }
    }

    function animHex() {
        t += 0.015;
        drawHexGrid();
        requestAnimationFrame(animHex);
    }
    animHex();
})();


// --- NEURAL NETWORK CANVAS ---
(function() {
    const canvas = document.getElementById('neuralCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    function resize() {
        canvas.width  = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    }
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    resize();

    const NODE_COUNT = 22;
    let nodes = [];
    let t = 0;

    function init() {
        nodes = [];
        const W = canvas.width;
        const H = canvas.height;
        for (let i = 0; i < NODE_COUNT; i++) {
            // Distribute nodes in an annular ring around the center
            const angle  = (i / NODE_COUNT) * Math.PI * 2 + (Math.random() - 0.5) * 0.5;
            const radius = 55 + Math.random() * 90;
            nodes.push({
                bx: W / 2 + Math.cos(angle) * radius,
                by: H / 2 + Math.sin(angle) * radius,
                x: 0, y: 0,
                vx: (Math.random() - 0.5) * 0.15,
                vy: (Math.random() - 0.5) * 0.15,
                dx: (Math.random() - 0.5) * 14,
                dy: (Math.random() - 0.5) * 14,
                phase: Math.random() * Math.PI * 2,
                size: Math.random() * 2 + 1,
                speed: 0.3 + Math.random() * 0.4,
            });
        }
    }

    const MAX_DIST = 130;

    function drawNeural() {
        const W = canvas.width;
        const H = canvas.height;
        ctx.clearRect(0, 0, W, H);
        t += 0.012;

        // Update positions
        nodes.forEach(n => {
            n.x = n.bx + n.dx * Math.sin(t * n.speed + n.phase);
            n.y = n.by + n.dy * Math.cos(t * n.speed + n.phase);
        });

        // Draw connections
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const a = nodes[i], b = nodes[j];
                const dx = a.x - b.x, dy = a.y - b.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < MAX_DIST) {
                    const alpha = (1 - dist / MAX_DIST) * 0.28;
                    const pulse = 0.5 + 0.5 * Math.sin(t * 1.2 + i * 0.5);
                    ctx.beginPath();
                    ctx.moveTo(a.x, a.y);
                    ctx.lineTo(b.x, b.y);
                    ctx.strokeStyle = `rgba(0,255,136,${alpha * pulse})`;
                    ctx.lineWidth = 0.6;
                    ctx.stroke();
                }
            }
        }

        // Draw nodes
        nodes.forEach((n, i) => {
            const pulse = 0.6 + 0.4 * Math.sin(t * 1.5 + n.phase);
            // glow
            const grad = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.size * 5);
            grad.addColorStop(0, `rgba(0,255,136,${0.5 * pulse})`);
            grad.addColorStop(1, 'rgba(0,255,136,0)');
            ctx.beginPath();
            ctx.arc(n.x, n.y, n.size * 5, 0, Math.PI * 2);
            ctx.fillStyle = grad;
            ctx.fill();

            // core dot
            ctx.beginPath();
            ctx.arc(n.x, n.y, n.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0,255,136,${0.8 * pulse})`;
            ctx.fill();
        });
    }

    init();
    function loop() {
        drawNeural();
        requestAnimationFrame(loop);
    }
    loop();

    window.addEventListener('resize', () => {
        resize();
        init();
    });
})();
