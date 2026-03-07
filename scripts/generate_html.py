import json
import os
from datetime import datetime
from jinja2 import Template

DATA_FILE = "data/history.json"

def get_cnn_color(val):
    if not val: return "text-slate-400"
    if val < 25: return "text-red-600"
    if val < 45: return "text-orange-600"
    if val < 55: return "text-slate-600"
    if val < 75: return "text-emerald-600"
    return "text-sky-600"

# --- CORE TEMPLATE ---
BASE_HEAD = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | Trendsetter</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📈</text></svg>">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; color: #0f172a; }
        .glass { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(0, 0, 0, 0.05); }
        .gradient-text { background: linear-gradient(135deg, #020617, #475569); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .card-hover:hover { transform: translateY(-1px); box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); transition: all 0.2s ease; }
        .active-tab { background: #0f172a; color: white !important; font-weight: 700; }
    </style>
</head>
<body class="p-2 md:p-3">
    <div class="max-w-5xl mx-auto">
        <header class="flex flex-col md:flex-row justify-between items-center mb-5 gap-3 bg-white p-3 px-6 rounded-3xl shadow-sm border border-slate-200">
            <div class="flex items-center gap-4">
                <div class="flex flex-col md:flex-row md:items-baseline gap-2">
                    <h1 class="text-xl md:text-2xl font-black gradient-text tracking-tighter">Trendsetter</h1>
                    <span class="text-xs md:text-sm font-bold text-slate-400 font-mono">:: {{ last_date }}</span>
                </div>
            </div>
            
            <nav class="flex gap-1 p-1 bg-slate-100 rounded-xl border border-slate-200 text-[13px] font-bold">
                <a href="index.html" class="px-5 py-2 rounded-lg transition-all text-slate-500 hover:text-slate-900 {{ active_dash }}">儀表板</a>
                <a href="charts.html" class="px-5 py-2 rounded-lg transition-all text-slate-500 hover:text-slate-900 {{ active_charts }}">圖表區</a>
                <a href="history.html" class="px-5 py-2 rounded-lg transition-all text-slate-500 hover:text-slate-900 {{ active_hist }}">歷史紀錄</a>
            </nav>
        </header>
"""

BASE_FOOTER = """
        <footer class="text-center text-slate-400 text-sm py-12">
            <p>© 2026 Trendsetter Dashboard</p>
        </footer>
    </div>
    <script>
        lucide.createIcons();
    </script>
</body>
</html>
"""

# --- DASHBOARD_BODY ---
DASHBOARD_BODY = """
        <div class="space-y-6">
            <!-- Macro Section: Full Width Row -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-blue-600 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">宏觀趨勢 Macro</h2>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3" id="macroGrid"></div>
            </section>

            <!-- Sentiment Section: Full Width Row -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-sky-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">市場情緒 Sentiment</h2>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3" id="sentimentGrid"></div>
            </section>

            <!-- Risk Section: Full Width Row -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-purple-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">風險與期權 Risk</h2>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-3 gap-3" id="riskGrid"></div>
            </section>

            <!-- Internals Section: Full Width Row -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-emerald-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">內部資金與廣度 Internals</h2>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3" id="internalGrid"></div>
            </section>
        </div>

    <script>
        const rawData = {{ history_json }};
        const latest = rawData[rawData.length - 1];

        const categories = {
            macroGrid: [
                { label: '10Y-3M Spread', value: latest['10Y-3M Spread'], icon: 'trending-down', color: latest['10Y-3M Spread'] < 0 ? 'text-red-500' : 'text-blue-600' },
                { label: 'HYG/LQD Ratio', value: latest['HYG/LQD Ratio'], icon: 'landmark', color: 'text-orange-600' },
                { label: 'XLY/XLP Ratio', value: latest['XLY/XLP Ratio'], icon: 'shopping-bag', color: 'text-pink-600' },
                { label: 'Copper/Gold Ratio', value: latest['Copper/Gold Ratio'], icon: 'coins', color: 'text-amber-600' },
                { label: 'KBE/SPY Ratio', value: latest['KBE/SPY Ratio'], icon: 'building', color: 'text-indigo-600' }
            ],
            sentimentGrid: [
                { label: 'CNN Fear & Greed', value: '{{ cnn_val }}', icon: 'gauge', color: 'text-sky-600' },
                { label: 'VIX 指數', value: latest.VIX, icon: 'alert-triangle', color: 'text-orange-500' },
                { label: 'NAAIM 曝險', value: latest.NAAIM, icon: 'user-check', color: 'text-emerald-600' },
                { label: 'AAII Spread', value: latest['AAII B-B'], icon: 'users', color: 'text-rose-500' },
                { label: 'Crypto F&G', value: latest['Crypto F&G'], icon: 'bitcoin', color: 'text-amber-500' }
            ],
            riskGrid: [
                { label: 'Gamma (GEX)', value: latest.GEX + 'B', icon: 'zap', color: 'text-purple-600' },
                { label: 'Equity P/C Ratio', value: latest['Equity P/C Ratio'], icon: 'trending-up', color: 'text-rose-600' },
                { label: 'Total P/C Ratio', value: latest['Total P/C Ratio'], icon: 'activity', color: 'text-indigo-600' }
            ],
            internalGrid: [
                { label: 'Dark Pool (DIX)', value: latest.DIX ? latest.DIX + '%' : '--%', icon: 'shield-check', color: 'text-blue-600' },
                { label: 'NYSE > 50MA', value: latest['NYSE above 50MA'] ? latest['NYSE above 50MA'] + '%' : '--%', icon: 'bar-chart', color: 'text-indigo-500' },
                { label: 'NASD > 50MA', value: latest['NASDAQ above 50MA'] ? latest['NASDAQ above 50MA'] + '%' : '--%', icon: 'bar-chart', color: 'text-indigo-500' }
            ]
        };

        const renderGrid = (id, items) => {
            const grid = document.getElementById(id);
            if (!grid) return;
            items.forEach(m => {
                grid.innerHTML += `
                    <div class="bg-white p-3 px-4 rounded-2xl card-hover border border-slate-200 shadow-sm transition-all duration-300">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-slate-400 text-[9px] font-bold uppercase tracking-widest">${m.label}</span>
                            <div class="p-1 px-1.5 bg-slate-50 rounded-lg">
                                <i data-lucide="${m.icon}" class="${m.color} w-3 h-3"></i>
                            </div>
                        </div>
                        <div class="text-2xl font-black tracking-tighter text-slate-900">${m.value || '--'}</div>
                    </div>
                `;
            });
        };

        Object.keys(categories).forEach(id => renderGrid(id, categories[id]));
    </script>
"""

# --- CHARTS PAGE ---
CHARTS_BODY = """
        <div class="grid grid-cols-1 gap-10">
            <div class="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-200">
                <div class="flex items-center justify-between mb-8">
                    <h3 class="text-xl font-black flex items-center gap-3 text-slate-800">
                        <i data-lucide="trending-up" class="text-sky-500"></i> 情緒指標趨勢
                    </h3>
                    <div class="flex gap-4 text-xs font-bold text-slate-400 uppercase tracking-widest">
                        <span>CNN</span> • <span>NAAIM</span> • <span>VIX</span>
                    </div>
                </div>
                <div class="h-[450px]">
                    <canvas id="sentimentChart"></canvas>
                </div>
            </div>
            <div class="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="text-lg font-black flex items-center gap-3 text-slate-800">
                        <i data-lucide="bar-chart-3" class="text-purple-500"></i> 市場廣度 Breadth
                    </h3>
                </div>
                <div class="h-[450px]">
                    <canvas id="breadthChart"></canvas>
                </div>
            </div>
        </div>

    <script>
        const rawData = {{ history_json }};
        const latest = rawData[rawData.length - 1];
        
        Chart.defaults.color = '#64748b';
        Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";

        const labels = rawData.map(d => d.Date);

        new Chart(document.getElementById('sentimentChart'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    { label: 'CNN F&G', data: rawData.map(d => d.CNN), borderColor: '#0ea5e9', tension: 0.3, fill: false, borderWidth: 4, pointRadius: 0, pointHoverRadius: 6 },
                    { label: 'NAAIM', data: rawData.map(d => d.NAAIM), borderColor: '#10b981', tension: 0.3, fill: false, borderWidth: 2, pointRadius: 0 },
                    { label: 'VIX (x2)', data: rawData.map(d => d.VIX * 2), borderColor: '#f43f5e', tension: 0.3, borderDash: [6, 6], borderWidth: 1.5, pointRadius: 0 }
                ]
            },
            options: { 
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { 
                    x: { grid: { display: false }, ticks: { font: { size: 10, weight: '600' } } },
                    y: { grid: { color: '#f1f5f9' }, border: { dash: [4, 4] }, ticks: { font: { weight: '600' } } }
                }
            }
        });

        new Chart(document.getElementById('breadthChart'), {
            type: 'bar',
            data: {
                labels: ['NYSE > 20MA', 'NASD > 20MA', 'NYSE > 50MA', 'NASD > 50MA'],
                datasets: [{
                    data: [
                        latest['NYSE above 20MA'], 
                        latest['NASDAQ above 20MA'], 
                        latest['NYSE above 50MA'], 
                        latest['NASDAQ above 50MA']
                    ],
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#10b981', '#6366f1'],
                    borderRadius: 16,
                    barThickness: 60
                }]
            },
            options: { 
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { 
                    y: { min: 0, max: 100, grid: { color: '#f1f5f9' }, ticks: { font: { weight: '600' } } },
                    x: { grid: { display: false }, ticks: { font: { size: 12, weight: '800' } } }
                }
            }
        });
    </script>
"""

# --- HISTORY PAGE ---
HISTORY_BODY = """
        <div class="flex flex-wrap gap-2 mb-10 p-1.5 bg-slate-100 rounded-2xl border border-slate-200 max-w-fit mx-auto md:mx-0">
            <button onclick="switchTab('all')" id="tab-all" class="px-8 py-2.5 rounded-xl text-sm font-bold transition-all active-tab shadow-sm">全部紀錄</button>
            <button onclick="switchTab('macro')" id="tab-macro" class="px-8 py-2.5 rounded-xl text-sm font-bold transition-all hover:bg-white text-slate-500">宏觀趨勢</button>
            <button onclick="switchTab('sentiment')" id="tab-sentiment" class="px-8 py-2.5 rounded-xl text-sm font-bold transition-all hover:bg-white text-slate-500">市場情緒</button>
            <button onclick="switchTab('risk')" id="tab-risk" class="px-8 py-2.5 rounded-xl text-sm font-bold transition-all hover:bg-white text-slate-500">風險與期權</button>
            <button onclick="switchTab('internals')" id="tab-internals" class="px-8 py-2.5 rounded-xl text-sm font-bold transition-all hover:bg-white text-slate-500">內部資金</button>
        </div>

        <div class="bg-white rounded-[2.5rem] overflow-hidden shadow-xl border border-slate-200">
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse min-w-[1200px]">
                    <thead class="bg-slate-50 text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] border-b border-slate-200">
                        <tr>
                            <th class="p-6">交易日期</th>
                            <th class="p-6 col-macro">10Y-3M</th>
                            <th class="p-6 col-macro">HYG/LQD</th>
                            <th class="p-6 col-macro">XLY/XLP</th>
                            <th class="p-6 col-macro text-nowrap">C/G Ratio</th>
                            <th class="p-6 col-macro text-nowrap">KBE/SPY</th>
                            <th class="p-6 col-sentiment text-nowrap">CNN F&G</th>
                            <th class="p-6 col-sentiment">VIX</th>
                            <th class="p-6 col-sentiment">NAAIM</th>
                            <th class="p-6 col-sentiment">AAII Spread</th>
                            <th class="p-6 col-sentiment">Crypto</th>
                            <th class="p-6 col-risk">Gamma (GEX)</th>
                            <th class="p-6 col-risk">Equity P/C</th>
                            <th class="p-6 col-risk">Total P/C</th>
                            <th class="p-6 col-internals text-nowrap">Dark Pool</th>
                            <th class="p-6 col-internals text-nowrap">NYSE 20</th>
                            <th class="p-6 col-internals text-nowrap">NASD 20</th>
                            <th class="p-6 col-internals text-nowrap">NYSE 50</th>
                            <th class="p-6 col-internals text-nowrap">NASD 50</th>
                        </tr>
                    </thead>
                    <tbody id="dataTableBody" class="text-slate-600">
                    </tbody>
                </table>
            </div>
        </div>

    <script>
        const rawData = {{ history_json }};
        const tableBody = document.getElementById('dataTableBody');
        
        const renderTable = () => {
            tableBody.innerHTML = '';
            [...rawData].sort((a,b) => new Date(b.Date) - new Date(a.Date)).forEach(row => {
                const tr = document.createElement('tr');
                tr.className = 'border-t border-slate-100 hover:bg-slate-50 transition-colors';
                tr.innerHTML = `
                    <td class="p-6 text-xs font-black text-slate-900 bg-slate-50/30">${row.Date}</td>
                    <td class="p-6 text-xs col-macro ${row['10Y-3M Spread'] < 0 ? 'text-red-500 font-black' : ''}">${row['10Y-3M Spread'] || '--'}</td>
                    <td class="p-6 text-xs font-bold text-orange-600 col-macro">${row['HYG/LQD Ratio'] || '--'}</td>
                    <td class="p-6 text-xs font-bold text-pink-600 col-macro">${row['XLY/XLP Ratio'] || '--'}</td>
                    <td class="p-6 text-xs col-macro font-bold text-amber-600">${row['Copper/Gold Ratio'] || '--'}</td>
                    <td class="p-6 text-xs col-macro font-bold text-indigo-600">${row['KBE/SPY Ratio'] || '--'}</td>
                    <td class="p-6 text-xs font-black text-sky-700 col-sentiment">${row.CNN || '--'}</td>
                    <td class="p-6 text-xs col-sentiment">${row.VIX || '--'}</td>
                    <td class="p-6 text-xs col-sentiment">${row.NAAIM || '--'}</td>
                    <td class="p-6 text-xs col-sentiment">${row['AAII B-B'] || '--'}</td>
                    <td class="p-6 text-xs font-bold text-amber-600 col-sentiment">${row['Crypto F&G'] || '--'}</td>
                    <td class="p-6 text-xs text-purple-700 font-black col-risk">${row.GEX || '--'}B</td>
                    <td class="p-6 text-xs col-risk">${row['Equity P/C Ratio'] || '--'}</td>
                    <td class="p-6 text-xs col-risk">${row['Total P/C Ratio'] || '--'}</td>
                    <td class="p-6 text-xs text-blue-700 font-bold col-internals">${row.DIX || '--'}%</td>
                    <td class="p-6 text-xs text-emerald-600 font-black col-internals">${row['NYSE above 20MA'] || '--'}%</td>
                    <td class="p-6 text-xs text-emerald-600 font-black col-internals">${row['NASDAQ above 20MA'] || '--'}%</td>
                    <td class="p-6 text-xs text-indigo-500 font-bold col-internals">${row['NYSE above 50MA'] || '--'}%</td>
                    <td class="p-6 text-xs text-indigo-500 font-bold col-internals">${row['NASDAQ above 50MA'] || '--'}%</td>
                `;
                tableBody.appendChild(tr);
            });
        };

        const switchTab = (cat) => {
            currentTab = cat;
            document.querySelectorAll('button[id^="tab-"]').forEach(btn => btn.classList.remove('active-tab'));
            document.getElementById('tab-' + cat).classList.add('active-tab');

            const allCols = ['col-sentiment', 'col-risk', 'col-internals', 'col-macro'];
            allCols.forEach(cls => {
                const elements = document.getElementsByClassName(cls);
                for (let el of elements) {
                    if (cat === 'all' || cls === 'col-' + cat) {
                        el.style.display = '';
                    } else {
                        el.style.display = 'none';
                    }
                }
            });
        };

        const tabs = ['all', 'macro', 'sentiment', 'risk', 'internals'];
        let currentTab = 'all';

        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                let idx = tabs.indexOf(currentTab);
                if (e.key === 'ArrowRight') idx = (idx + 1) % tabs.length;
                else idx = (idx - 1 + tabs.length) % tabs.length;
                switchTab(tabs[idx]);
            }
        });

        renderTable();
        switchTab('all');
    </script>
"""

def main():
    if not os.path.exists(DATA_FILE):
        print("No data found.")
        return

    with open(DATA_FILE, 'r') as f:
        history = json.load(f)

    latest = history[-1]
    last_date = latest['Date']
    cnn_val = latest.get('CNN', '-')
    cnn_color = get_cnn_color(latest.get('CNN'))

    # Context
    ctx = {
        "last_date": last_date,
        "cnn_val": cnn_val,
        "cnn_color": cnn_color,
        "history_json": json.dumps(history),
        "active_dash": "",
        "active_charts": "",
        "active_hist": ""
    }

    # index.html
    ctx.update({"title": "儀表板", "active_dash": "active-tab"})
    index_html = Template(BASE_HEAD + DASHBOARD_BODY + BASE_FOOTER).render(**ctx)
    
    # charts.html
    ctx.update({"title": "圖表區", "active_dash": "", "active_charts": "active-tab"})
    charts_html = Template(BASE_HEAD + CHARTS_BODY + BASE_FOOTER).render(**ctx)

    # history.html
    ctx.update({"title": "歷史紀錄", "active_charts": "", "active_hist": "active-tab"})
    history_html = Template(BASE_HEAD + HISTORY_BODY + BASE_FOOTER).render(**ctx)

    os.makedirs("public", exist_ok=True)
    
    pages = {
        "index.html": index_html,
        "charts.html": charts_html,
        "history.html": history_html
    }
    
    for name, content in pages.items():
        with open(f"public/{name}", "w") as f: f.write(content)

    print("Three pages generated successfully.")

if __name__ == "__main__":
    main()
