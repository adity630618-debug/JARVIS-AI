// J.A.R.V.I.S UI Frontend Logic & Animations

let ws = null;
let currentStatus = "STANDBY";
let rotationAngle1 = 0;
let rotationAngle2 = 0;
let rotationAngle3 = 0;

// Setup Canvas elements
const reactorCanvas = document.getElementById("reactor-canvas");
const rCtx = reactorCanvas ? reactorCanvas.getContext("2d") : null;

const waveCanvas = document.getElementById("wave-canvas");
const wCtx = waveCanvas ? waveCanvas.getContext("2d") : null;

// Clock
function updateClock() {
    const clockEl = document.getElementById("live-clock");
    if (!clockEl) return;
    const now = new Date();
    clockEl.innerText = now.toLocaleTimeString();
}
setInterval(updateClock, 1000);
updateClock();

// ==========================================
// Arc Reactor Canvas Animation
// ==========================================
function drawArcReactor() {
    if (!rCtx) return;
    const width = reactorCanvas.width;
    const height = reactorCanvas.height;
    const cx = width / 2;
    const cy = height / 2;

    rCtx.clearRect(0, 0, width, height);

    // Speed multiplier based on state
    let speed = 0.006;
    let strokeColor = "#00f2fe";
    let glowColor = "rgba(0, 242, 254, 0.4)";

    if (currentStatus === "LISTENING") {
        speed = 0.02;
        strokeColor = "#00e676";
        glowColor = "rgba(0, 230, 118, 0.5)";
    } else if (currentStatus === "PROCESSING") {
        speed = 0.035;
        strokeColor = "#ffd600";
        glowColor = "rgba(255, 214, 0, 0.5)";
    } else if (currentStatus === "SPEAKING") {
        speed = 0.015;
        strokeColor = "#00f2fe";
        glowColor = "rgba(0, 242, 254, 0.8)";
    }

    rotationAngle1 += speed;
    rotationAngle2 -= speed * 0.7;
    rotationAngle3 += speed * 1.3;

    // Outer Ring with Ticks
    rCtx.save();
    rCtx.translate(cx, cy);
    rCtx.rotate(rotationAngle1);
    rCtx.strokeStyle = strokeColor;
    rCtx.shadowColor = glowColor;
    rCtx.shadowBlur = 15;
    rCtx.lineWidth = 2;

    // Circle 1
    rCtx.beginPath();
    rCtx.arc(0, 0, 165, 0, Math.PI * 2);
    rCtx.stroke();

    // Outer segments
    for (let i = 0; i < 36; i++) {
        const angle = (i * Math.PI) / 18;
        const x1 = Math.cos(angle) * 155;
        const y1 = Math.sin(angle) * 155;
        const x2 = Math.cos(angle) * 165;
        const y2 = Math.sin(angle) * 165;
        rCtx.beginPath();
        rCtx.moveTo(x1, y1);
        rCtx.lineTo(x2, y2);
        rCtx.stroke();
    }
    rCtx.restore();

    // Middle Ring with Dashes
    rCtx.save();
    rCtx.translate(cx, cy);
    rCtx.rotate(rotationAngle2);
    rCtx.strokeStyle = strokeColor;
    rCtx.shadowColor = glowColor;
    rCtx.shadowBlur = 12;
    rCtx.lineWidth = 3;
    rCtx.setLineDash([20, 12, 6, 12]);

    rCtx.beginPath();
    rCtx.arc(0, 0, 130, 0, Math.PI * 2);
    rCtx.stroke();
    rCtx.restore();

    // Inner Rotating Geometric Triangles / Ring
    rCtx.save();
    rCtx.translate(cx, cy);
    rCtx.rotate(rotationAngle3);
    rCtx.strokeStyle = strokeColor;
    rCtx.lineWidth = 1.5;
    rCtx.setLineDash([8, 6]);

    rCtx.beginPath();
    rCtx.arc(0, 0, 95, 0, Math.PI * 2);
    rCtx.stroke();

    // Inner Nodes
    for (let i = 0; i < 8; i++) {
        const angle = (i * Math.PI) / 4;
        const nx = Math.cos(angle) * 95;
        const ny = Math.sin(angle) * 95;
        rCtx.fillStyle = strokeColor;
        rCtx.beginPath();
        rCtx.arc(nx, ny, 3, 0, Math.PI * 2);
        rCtx.fill();
    }
    rCtx.restore();

    requestAnimationFrame(drawArcReactor);
}

// ==========================================
// Audio Waveform Animation
// ==========================================
let wavePhase = 0;
function drawWaveform() {
    if (!wCtx) return;
    const w = waveCanvas.parentElement.clientWidth;
    waveCanvas.width = w;
    const h = waveCanvas.height;
    wCtx.clearRect(0, 0, w, h);

    const bars = 40;
    const barWidth = 4;
    const spacing = (w - (bars * barWidth)) / (bars + 1);

    wavePhase += 0.08;

    let baseAmp = 4;
    if (currentStatus === "SPEAKING") {
        baseAmp = 22;
    } else if (currentStatus === "LISTENING") {
        baseAmp = 14;
    }

    wCtx.fillStyle = (currentStatus === "LISTENING") ? "#00e676" : "#00f2fe";
    wCtx.shadowColor = wCtx.fillStyle;
    wCtx.shadowBlur = 10;

    for (let i = 0; i < bars; i++) {
        const x = spacing + i * (barWidth + spacing);
        // Sinusoidal oscillation
        const barHeight = Math.abs(Math.sin(wavePhase + i * 0.3) * Math.cos(wavePhase * 0.7 + i * 0.2)) * baseAmp + 4;
        const y = (h - barHeight) / 2;

        wCtx.fillRect(x, y, barWidth, barHeight);
    }

    requestAnimationFrame(drawWaveform);
}

// ==========================================
// State Updates & UI Reactions
// ==========================================
function updateStatus(status, text) {
    currentStatus = status;
    const stateBadge = document.getElementById("state-badge");
    const stateText = document.getElementById("state-text");
    const subtitle = document.getElementById("live-subtitle");

    if (stateText) stateText.innerText = status;
    if (subtitle && text) subtitle.innerText = `"${text}"`;

    document.body.className = `state-${status.toLowerCase()}`;

    if (status === "LISTENING") {
        document.getElementById("mic-btn-text").innerText = "LISTENING...";
    } else {
        document.getElementById("mic-btn-text").innerText = "ACTIVE";
    }
}

// Browser Web Speech Engine for Mobile & Cloud Playback
function speakTextWeb(text) {
    if (!('speechSynthesis' in window) || !text) return;
    try {
        window.speechSynthesis.cancel(); // cancel previous speech
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        // Try to pick an Indian English or natural voice if available in browser
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => v.lang.includes('en-IN') || v.name.includes('India') || v.name.includes('Ravi') || v.name.includes('Google'));
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        window.speechSynthesis.speak(utterance);
    } catch (e) {
        console.warn("[WebTTS] Could not speak:", e);
    }
}

function addTranscript(sender, text, imageUrl = null) {
    const feed = document.getElementById("transcript-feed");
    if (!feed) return;

    const item = document.createElement("div");
    item.className = `feed-item ${sender.toLowerCase()}`;
    
    const timeSpan = document.createElement("span");
    timeSpan.className = "timestamp";
    timeSpan.innerText = `[${sender.toUpperCase()}]`;
    item.appendChild(timeSpan);

    if (imageUrl) {
        const img = document.createElement("img");
        img.src = imageUrl;
        img.className = "feed-image";
        item.appendChild(img);
    }

    if (text) {
        const p = document.createElement("p");
        p.innerText = text;
        item.appendChild(p);
    }

    feed.appendChild(item);

    // Keep scrolling to the newest message
    feed.scrollTop = feed.scrollHeight;
    requestAnimationFrame(() => {
        feed.scrollTop = feed.scrollHeight;
    });
}

// ==========================================
// WebSocket Connection
// ==========================================
function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host || "127.0.0.1:7890";
    const wsUrl = `${protocol}//${host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("[J.A.R.V.I.S WebSocket] Connected.");
        document.getElementById("system-status-text").innerText = "SYSTEM ONLINE";
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === "status") {
                updateStatus(msg.status, msg.text);
            } else if (msg.type === "transcript") {
                addTranscript(msg.sender, msg.text);
                if (msg.sender.toLowerCase() === "jarvis") {
                    document.getElementById("live-subtitle").innerText = `"${msg.text}"`;
                    speakTextWeb(msg.text);
                }
            } else if (msg.type === "metrics") {
                if (msg.cpu !== undefined) {
                    document.getElementById("cpu-bar").style.width = `${msg.cpu}%`;
                    document.getElementById("cpu-val").innerText = `${msg.cpu}%`;
                }
                if (msg.ram !== undefined) {
                    document.getElementById("ram-bar").style.width = `${msg.ram}%`;
                    document.getElementById("ram-val").innerText = `${msg.ram}%`;
                }
            } else if (msg.type === "ai_status") {
                const aiEl = document.getElementById("ai-status");
                if (aiEl) {
                    aiEl.innerText = msg.status;
                    if (msg.status === "GEMINI ONLINE") {
                        aiEl.style.color = "#00e676";
                        aiEl.style.textShadow = "0 0 10px #00e676";
                    }
                }
            } else if (msg.type === "api_key_status") {
                const msgEl = document.getElementById("modal-msg");
                const btn = document.getElementById("save-key-btn");
                if (btn) btn.innerText = "ACTIVATE BRAIN";
                if (msgEl) {
                    msgEl.innerText = msg.message;
                    msgEl.className = `modal-msg ${msg.success ? 'success' : 'error'}`;
                }
                if (msg.success) {
                    setTimeout(() => {
                        closeApiKeyModal();
                    }, 1400);
                }
            }
        } catch (e) {
            console.error("Error parsing WebSocket message:", e);
        }
    };

    ws.onclose = () => {
        console.log("[J.A.R.V.I.S WebSocket] Disconnected. Reconnecting in 3 seconds...");
        document.getElementById("system-status-text").innerText = "RECONNECTING...";
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (err) => {
        console.error("[J.A.R.V.I.S WebSocket] Error:", err);
    };
}

// ==========================================
// File / Image Attachment System
// ==========================================
let attachedFileData = null; // { name, base64, mimeType, previewUrl }

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        const fullDataUrl = e.target.result;
        // Extract pure base64
        const commaIdx = fullDataUrl.indexOf(",");
        const base64 = commaIdx !== -1 ? fullDataUrl.substring(commaIdx + 1) : fullDataUrl;

        attachedFileData = {
            name: file.name,
            base64: base64,
            mimeType: file.type || "image/png",
            previewUrl: fullDataUrl
        };

        // Show pill
        const pill = document.getElementById("file-preview-pill");
        const pillImg = document.getElementById("file-preview-img");
        const pillName = document.getElementById("file-preview-name");
        if (pill && pillImg && pillName) {
            pillImg.src = fullDataUrl;
            pillName.innerText = file.name;
            pill.style.display = "inline-flex";
        }
    };
    reader.readAsDataURL(file);
}

function removeAttachedFile(event) {
    if (event) event.stopPropagation();
    attachedFileData = null;
    const pill = document.getElementById("file-preview-pill");
    const fileInput = document.getElementById("file-upload-input");
    if (pill) pill.style.display = "none";
    if (fileInput) fileInput.value = "";
}

function sendCommand(cmdText) {
    if (!cmdText) return;
    addTranscript("user", cmdText);
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "command", text: cmdText }));
    } else {
        console.warn("WebSocket not connected. Cannot send command.");
    }
}

function handleFormSubmit(e) {
    e.preventDefault();
    const input = document.getElementById("command-input");
    const val = input.value.trim();

    if (!val && !attachedFileData) return;

    if (attachedFileData) {
        const promptText = val || "Analyze this image and explain everything in detail, Sir.";
        addTranscript("user", promptText, attachedFileData.previewUrl);

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: "image_command",
                text: promptText,
                image: attachedFileData.base64,
                mime_type: attachedFileData.mimeType,
                filename: attachedFileData.name
            }));
        }

        // Clean up input & file pill
        input.value = "";
        removeAttachedFile();
        return;
    }

    // Text only command
    if (val) {
        sendCommand(val);
        input.value = "";
    }
}

function toggleListening() {
    sendCommand("listen");
}

// ==========================================
// Gemini API Key Modal Management
// ==========================================
function openApiKeyModal() {
    const modal = document.getElementById("api-modal");
    if (modal) modal.style.display = "flex";
    const msgEl = document.getElementById("modal-msg");
    if (msgEl) msgEl.innerText = "";
    const input = document.getElementById("api-key-input");
    if (input) input.focus();
}

function closeApiKeyModal() {
    const modal = document.getElementById("api-modal");
    if (modal) modal.style.display = "none";
}

function saveApiKey() {
    const input = document.getElementById("api-key-input");
    const msgEl = document.getElementById("modal-msg");
    const btn = document.getElementById("save-key-btn");
    const key = input ? input.value.trim() : "";

    if (!key) {
        if (msgEl) {
            msgEl.innerText = "Please paste a valid Gemini API key.";
            msgEl.className = "modal-msg error";
        }
        return;
    }

    if (btn) btn.innerText = "TESTING...";
    if (msgEl) {
        msgEl.innerText = "Connecting to Google Gemini...";
        msgEl.className = "modal-msg";
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "save_api_key", key: key }));
    } else {
        if (msgEl) {
            msgEl.innerText = "System offline. Please restart JARVIS.";
            msgEl.className = "modal-msg error";
        }
        if (btn) btn.innerText = "ACTIVATE BRAIN";
    }
}

function quitJarvis() {
    if (confirm("Are you sure you want to shut down J.A.R.V.I.S, Sir?")) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "shutdown" }));
        }
        setTimeout(() => {
            window.close();
        }, 500);
    }
}

// Start animations, service worker, and connection
window.addEventListener("DOMContentLoaded", () => {
    drawArcReactor();
    drawWaveform();
    connectWebSocket();

    // Register PWA Service Worker for Phone App Support
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('[PWA] Service Worker registered:', reg.scope))
            .catch(err => console.log('[PWA] Service Worker registration failed:', err));
    }
});
