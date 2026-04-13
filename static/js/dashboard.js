/**
 * Modernized BehaviourAI Dashboard JavaScript
 */

const COLORS = ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ef4444"];
const SEGMENT_LABELS = { 0: "Low Value", 1: "Medium Value", 2: "High Value" };
const API_KEY = "demo-secret-key"; // Embedded for demo purposes

// ── Utility Functions ─────────────────────────────────────
function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = `<div class="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-sm my-4">${message}</div>`;
}

function clearError(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = "";
}

async function fetchJSON(url, options = {}) {
    options.headers = options.headers || {};
    options.headers["X-API-Key"] = API_KEY;
    if (!options.headers["Content-Type"] && options.method === "POST") {
        options.headers["Content-Type"] = "application/json";
    }

    try {
        const res = await fetch(url, options);
        if (!res.ok) {
            const error = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
            throw new Error(error.error || error.message || `HTTP ${res.status}`);
        }
        return await res.json();
    } catch (err) {
        console.error(`Fetch failed: ${url}`, err); // Fixed logger bug
        throw err;
    }
}

// ── Load Stats ───────────────────────────────────────────
async function loadStats() {
    clearError("statsError");
    try {
        const d = await fetchJSON("/api/stats");
        document.getElementById("totalUsers").textContent = d.total_users;
        document.getElementById("avgClicks").textContent = d.avg_clicks.toFixed(1);
        document.getElementById("avgTime").textContent = d.avg_time_spent.toFixed(1);
        document.getElementById("avgPurchases").textContent = d.avg_purchases.toFixed(1);

        const segs = d.segments;
        new Chart(document.getElementById("segmentChart"), {
            type: "doughnut",
            data: {
                labels: Object.keys(segs).map(k => SEGMENT_LABELS[k] || k),
                datasets: [{
                    data: Object.values(segs),
                    backgroundColor: COLORS,
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { position: 'right', labels: { color: "#a1a1aa", font: { family: 'Inter', size: 12 } } },
                    tooltip: { backgroundColor: 'rgba(24, 24, 27, 0.9)', titleColor: '#fff', bodyColor: '#fff', padding: 12, cornerRadius: 8 }
                },
                cutout: "70%"
            }
        });
    } catch (err) {
        showError("statsError", `Failed to load statistics: ${err.message}`);
    }
}

// ── Load Clusters ───────────────────────────────────────
async function loadClusters() {
    clearError("clusterError");
    try {
        const pts = await fetchJSON("/api/cluster");
        const datasets = [0, 1, 2].map(c => ({
            label: ["Low Engagement", "Mid Engagement", "High Engagement"][c],
            data: pts.filter(p => p.cluster === c).map(p => ({ x: p.x, y: p.y })),
            backgroundColor: COLORS[c] + "AA",
            pointRadius: 6,
            pointHoverRadius: 8,
            borderWidth: 1,
            borderColor: COLORS[c]
        }));

        new Chart(document.getElementById("clusterChart"), {
            type: "scatter",
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: "Clicks", color: "#71717a" }, grid: { color: "#27272a", drawBorder: false }, ticks: { color: "#71717a" } },
                    y: { title: { display: true, text: "Time Spent (min)", color: "#71717a" }, grid: { color: "#27272a", drawBorder: false }, ticks: { color: "#71717a" } }
                },
                plugins: { 
                    legend: { position: 'top', labels: { color: "#a1a1aa", font: { family: 'Inter', size: 12 } } },
                    tooltip: { backgroundColor: 'rgba(24, 24, 27, 0.9)', titleColor: '#fff', bodyColor: '#fff', padding: 12, cornerRadius: 8 }
                }
            }
        });
    } catch (err) {
        showError("clusterError", `Failed to load clusters: ${err.message}`);
    }
}

// ── Load Trends ──────────────────────────────────────────
async function loadTrends() {
    clearError("trendsError");
    try {
        const data = await fetchJSON("/api/trends");
        const order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
        data.sort((a, b) => order.indexOf(a.month) - order.indexOf(b.month));

        new Chart(document.getElementById("trendChart"), {
            type: "line",
            data: {
                labels: data.map(d => d.month),
                datasets: [
                    {
                        label: "Avg Purchases",
                        data: data.map(d => d.avg_purchases.toFixed(2)),
                        borderColor: COLORS[0],
                        backgroundColor: COLORS[0] + "20",
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 4
                    },
                    {
                        label: "Avg Clicks",
                        data: data.map(d => d.avg_clicks.toFixed(2)),
                        borderColor: COLORS[1],
                        backgroundColor: COLORS[1] + "20",
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false }, ticks: { color: "#71717a" } },
                    y: { grid: { color: "#27272a", drawBorder: false }, ticks: { color: "#71717a" } }
                },
                plugins: { 
                    legend: { position: 'top', labels: { color: "#a1a1aa", font: { family: 'Inter', size: 12 } } },
                    tooltip: { mode: 'index', intersect: false, backgroundColor: 'rgba(24, 24, 27, 0.9)', titleColor: '#fff', bodyColor: '#fff', padding: 12, cornerRadius: 8 }
                }
            }
        });
    } catch (err) {
        showError("trendsError", `Failed to load trends: ${err.message}`);
    }
}

// ── Train Model ─────────────────────────────────────────
async function trainModel() {
    const btn = document.getElementById("trainBtn");
    const status = document.getElementById("trainStatus");

    btn.disabled = true;
    const oldText = btn.innerHTML;
    btn.innerHTML = `<span class="animate-spin inline-block">↻</span> Training...`;
    
    status.className = "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20";
    status.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span> Training Model...`;
    status.style.display = "inline-flex";

    try {
        const d = await fetchJSON("/api/train", { method: "POST" });
        status.className = "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
        status.innerHTML = `✅ v${d.version || 'New'} | Accuracy: ${d.accuracy}%`;
    } catch (err) {
        status.className = "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20";
        status.innerHTML = `❌ Failed: ${err.message}`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = oldText;
    }
}

// ── Predict ─────────────────────────────────────────────
async function predict() {
    const resultBox = document.getElementById("predictResult");
    const inputs = {
        clicks: document.getElementById("p_clicks"),
        time_spent: document.getElementById("p_time"),
        purchase_count: document.getElementById("p_purchases"),
        page_views: document.getElementById("p_pageviews"),
        cart_additions: document.getElementById("p_cart")
    };

    // Client-side validation
    for (const [field, input] of Object.entries(inputs)) {
        const val = parseFloat(input.value);
        if (isNaN(val) || val < 0) {
            resultBox.innerHTML = `<div class="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-sm">Please enter valid positive numbers for all fields.</div>`;
            return;
        }
    }

    const payload = Object.fromEntries(
        Object.entries(inputs).map(([k, v]) => [k, parseFloat(v.value)])
    );

    resultBox.innerHTML = `
        <div class="flex flex-col items-center justify-center gap-3">
            <div class="w-8 h-8 rounded-full border-2 border-purple-500 border-t-transparent animate-spin"></div>
            <p class="text-sm text-gray-400 font-medium">Analyzing patterns...</p>
        </div>
    `;

    try {
        const d = await fetchJSON("/api/predict", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        if (d.status === "error") {
            resultBox.innerHTML = `<div class="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-sm w-full text-left">${d.message || d.error}</div>`;
            return;
        }

        // Color coding for different segments
        const segColor = d.segment.includes("High") ? "text-emerald-400" : (d.segment.includes("Medium") ? "text-blue-400" : "text-amber-400");
        const dotColor = d.segment.includes("High") ? "bg-emerald-400" : (d.segment.includes("Medium") ? "bg-blue-400" : "bg-amber-400");

        resultBox.innerHTML = `
            <div class="w-full text-left animate-[fadeIn_0.5s_ease-out]">
                <div class="flex items-center gap-3 mb-2">
                    <span class="w-3 h-3 rounded-full ${dotColor} shadow-[0_0_10px_currentColor]"></span>
                    <h4 class="text-3xl font-bold ${segColor} tracking-tight">${d.segment}</h4>
                </div>
                <div class="text-sm text-gray-400 mb-6 flex items-center justify-between">
                    <span>Confidence Score</span>
                    <span class="font-mono text-white bg-white/10 px-2 py-0.5 rounded">${d.confidence}%</span>
                </div>
                
                <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Recommended Actions</h5>
                <ul class="space-y-3">
                    ${d.recommendations.map(r => `
                        <li class="flex items-start gap-3 bg-black/40 rounded-lg p-3 border border-white/5 hover:border-white/10 transition-colors">
                            <span class="text-purple-400 mt-0.5">↳</span>
                            <span class="text-sm text-gray-300 leading-relaxed">${r}</span>
                        </li>
                    `).join("")}
                </ul>
            </div>
        `;
    } catch (err) {
        resultBox.innerHTML = `<div class="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-sm w-full text-left">Prediction failed: ${err.message}</div>`;
    }
}

// ── Load Health Status ──────────────────────────────────
async function loadHealth() {
    try {
        const health = await fetchJSON("/api/health");
        const statusEl = document.getElementById("healthStatus");
        if (statusEl) {
            if (health.data_loaded && health.model_loaded) {
                statusEl.className = "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                statusEl.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> System Healthy`;
            } else {
                statusEl.className = "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20";
                statusEl.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Needs Setup`;
            }
        }
    } catch (err) {
        const statusEl = document.getElementById("healthStatus");
        if (statusEl) {
            statusEl.className = "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20";
            statusEl.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-red-400"></span> Offline`;
        }
    }
}

// Add simple CSS animation dynamically
const style = document.createElement('style');
style.innerHTML = `
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
`;
document.head.appendChild(style);

// ── Initialize ──────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadHealth().then(() => {
        loadStats();
        loadClusters();
        loadTrends();
    });
});
