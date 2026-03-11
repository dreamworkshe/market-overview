import json
import os
from datetime import datetime
from jinja2 import Template

DATA_FILE = "data/history.json"
MA_FILE = "data/history_ma.json"

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
        .stale-card { opacity: 0.65; background-color: #f1f5f9 !important; filter: grayscale(0.2); }
        .stale-tag { font-size: 8px; color: #94a3b8; border: 1px solid #e2e8f0; padding: 1px 4px; border-radius: 4px; }
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
            <!-- Sentiment Section: Full Width Row -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-sky-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">市場情緒 Sentiment</h2>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3" id="sentimentGrid"></div>
            </section>

            <!-- Breadth Section -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-emerald-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">市場廣度 Breadth</h2>
                </div>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-3" id="breadthGrid"></div>
            </section>

            <!-- Credit Spread Section -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-amber-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">信用利差 Credit Spreads</h2>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3" id="creditGrid"></div>
            </section>

            <!-- Macro Section: Full Width Row -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-blue-600 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">跨市分析 Intermarket Analysis</h2>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3" id="macroGrid"></div>
            </section>
        </div>

    <script>
        const rawData = {{ history_json }};
        const maData = {{ ma_json }};
        const latest = rawData[rawData.length - 1];
        const latestMA = maData.find(m => m.Date === latest.Date) || {};

        const getTrend = (v1, v2, v3) => {
            if (v1 === undefined || v2 === undefined || v3 === undefined || v1 === '--' || v2 === '--' || v3 === '--') 
                return { icon: '', color: '' };
            if (v1 > v2 && v2 > v3) return { icon: 'trending-up', color: 'text-emerald-500' };
            if (v1 < v2 && v2 < v3) return { icon: 'trending-down', color: 'text-red-500' };
            return { icon: '', color: '' };
        };

        const categories = {
            sentimentGrid: [
                { label: 'CNN F&G', col: 'CNN' },
                { label: 'VIX 指數', col: 'VIX', reverse: true },
                { label: 'Crypto F&G', col: 'Crypto F&G' },
                { label: 'Dark Pool (DIX)', col: 'DIX', suffix: '%' },
                { label: 'Gamma (GEX)', col: 'GEX', suffix: 'B' },
                { label: 'Total P/C', col: 'Total P/C Ratio', reverse: true },
                { label: 'Equity P/C', col: 'Equity P/C Ratio', reverse: true },
                { label: 'NAAIM 曝險', col: 'NAAIM', weekly: true },
                { label: 'AAII Spread', col: 'AAII B-B', weekly: true }
            ],
            breadthGrid: [
                { label: 'NYSE > 20MA', col: 'NYSE above 20MA', suffix: '%' },
                { label: 'NASD > 20MA', col: 'NASDAQ above 20MA', suffix: '%' },
                { label: 'NYSE > 50MA', col: 'NYSE above 50MA', suffix: '%' },
                { label: 'NASD > 50MA', col: 'NASDAQ above 50MA', suffix: '%' }
            ],
            creditGrid: [
                { label: '10Y-3M Spread', col: '10Y-3M Spread' },
                { label: 'HYG/LQD', col: 'HYG/LQD Ratio' },
                { label: 'HYG/IEF', col: 'HYG/IEF Ratio' },
                { label: 'HY OAS', col: 'HY OAS' }
            ],
            macroGrid: [
                { label: 'QQQ/SPY', col: 'QQQ/SPY Ratio' },
                { label: 'RSP/SPY', col: 'RSP/SPY Ratio' },
                { label: 'KBE/SPY', col: 'KBE/SPY Ratio' },
                { label: 'XLY/XLP', col: 'XLY/XLP Ratio' },
                { label: 'Copper/Gold', col: 'Copper/Gold Ratio' }
            ]
        };

        const renderSparkline = (canvasId, data, color) => {
            const ctx = document.getElementById(canvasId).getContext('2d');
            const sparkColor = '#94a3b8'; // Force simple gray
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map((_, i) => i),
                    datasets: [{
                        data: data,
                        borderColor: sparkColor,
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: true,
                        backgroundColor: (context) => {
                            const gradient = context.chart.ctx.createLinearGradient(0, 0, 0, 40);
                            gradient.addColorStop(0, 'rgba(148, 163, 184, 0.1)');
                            gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
                            return gradient;
                        },
                        tension: 0.4
                    }]
                },
                options: {
                    events: [],
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: { enabled: false } },
                    scales: { x: { display: false }, y: { display: false } }
                }
            });
        };

        const renderGrid = (id, items) => {
            const grid = document.getElementById(id);
            if (!grid) return;
            items.forEach((m, idx) => {
                let targetIdx = rawData.length - 1;
                let val = latest[m.col];
                let isStale = false;
                
                // Fallback to previous data if missing
                if (val === undefined || val === null || val === '--') {
                    for (let i = rawData.length - 2; i >= 0; i--) {
                        if (rawData[i][m.col] !== undefined && rawData[i][m.col] !== null && rawData[i][m.col] !== '--') {
                            val = rawData[i][m.col];
                            targetIdx = i;
                            isStale = true;
                            break;
                        }
                    }
                }

                const sfx = m.suffix || '';
                const canvasId = `sparkline-${id}-${idx}`;
                
                let v1, v2, v3, labels;
                if (m.weekly) {
                    v1 = rawData[targetIdx - 5] ? rawData[targetIdx - 5][m.col] : '--';
                    v2 = rawData[targetIdx - 10] ? rawData[targetIdx - 10][m.col] : '--';
                    v3 = rawData[targetIdx - 15] ? rawData[targetIdx - 15][m.col] : '--';
                    labels = ['1W', '2W', '3W'];
                } else {
                    const targetDate = rawData[targetIdx].Date;
                    const lookupMA = maData.find(ma => ma.Date === targetDate) || {};
                    v1 = lookupMA[m.col + '_5MA'] || '--';
                    v2 = lookupMA[m.col + '_10MA'] || '--';
                    v3 = lookupMA[m.col + '_20MA'] || '--';
                    labels = ['5MA', '10MA', '20MA'];
                }

                const trend = getTrend(v1, v2, v3);
                
                // Get last 20 days for sparkline
                const sparkData = rawData.slice(-20).map(d => d[m.col]).filter(v => v !== undefined && v !== null);

                grid.innerHTML += `
                    <div class="bg-white p-3 px-4 rounded-2xl card-hover border border-slate-200 shadow-sm transition-all duration-300 ${isStale ? 'stale-card' : ''}">
                        <div class="flex items-center justify-between mb-1">
                            <div class="flex items-center gap-2">
                                <span class="text-slate-400 text-[9px] font-bold uppercase tracking-widest">${m.label}</span>
                                ${isStale ? '<span class="stale-tag">DELAYED</span>' : ''}
                            </div>
                            <i data-lucide="${trend.icon}" class="${trend.color} w-3.5 h-3.5"></i>
                        </div>
                        <div class="flex items-end justify-between gap-1 mb-2">
                            <div class="text-2xl font-black tracking-tighter text-slate-900">${val !== undefined ? val + sfx : '--'}</div>
                            <div class="w-16 h-8">
                                <canvas id="${canvasId}"></canvas>
                            </div>
                        </div>
                        <div class="mt-1 pt-2 border-t border-slate-50 flex justify-between items-center text-[10px] font-bold text-slate-400">
                            <div class="flex flex-col">
                                <span class="text-[8px] uppercase tracking-tighter text-slate-300">${labels[0]}</span>
                                <span class="text-slate-500 font-mono">${v1}${sfx}</span>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-[8px] uppercase tracking-tighter text-slate-300">${labels[1]}</span>
                                <span class="text-slate-500 font-mono">${v2}${sfx}</span>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-[8px] uppercase tracking-tighter text-slate-300">${labels[2]}</span>
                                <span class="text-slate-500 font-mono">${v3}${sfx}</span>
                            </div>
                        </div>
                    </div>
                `;
                
                // Render sparkline after a tiny delay to ensure DOM is ready
                setTimeout(() => renderSparkline(canvasId, sparkData, m.color), 0);
            });
        };

        Object.keys(categories).forEach(id => renderGrid(id, categories[id]));
    </script>
"""

# --- HISTORY PAGE ---
HISTORY_BODY = """
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div class="flex flex-wrap gap-1.5 p-1 bg-slate-100 rounded-2xl border border-slate-200">
                <button onclick="switchTab('sentiment')" id="tab-sentiment" class="px-5 py-2 rounded-xl text-xs font-bold transition-all active-tab shadow-sm">市場情緒</button>
                <button onclick="switchTab('breadth')" id="tab-breadth" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">市場廣度</button>
                <button onclick="switchTab('credit')" id="tab-credit" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">信用利差</button>
                <button onclick="switchTab('macro')" id="tab-macro" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">跨市分析</button>
                <button onclick="switchTab('all')" id="tab-all" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">全部紀錄</button>
            </div>
            <div class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-2xl shadow-sm">
                <i data-lucide="keyboard" class="w-4 h-4 text-slate-400"></i>
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">可用方向鍵 <kbd class="px-1.5 py-0.5 bg-slate-100 border border-slate-300 rounded text-slate-600">←</kbd> <kbd class="px-1.5 py-0.5 bg-slate-100 border border-slate-300 rounded text-slate-600">→</kbd> 切換分頁</span>
            </div>
        </div>

        <div class="bg-white rounded-[2rem] overflow-hidden shadow-xl border border-slate-200">
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse min-w-[1000px]">
                    <thead class="bg-slate-50 text-slate-400 text-[9px] font-black uppercase tracking-[0.15em] border-b border-slate-200">
                        <tr>
                            <th class="p-4 px-5">日期</th>
                            <th class="p-4 col-sentiment text-nowrap">CNN</th>
                            <th class="p-4 col-sentiment">VIX</th>
                            <th class="p-4 col-credit">HY OAS</th>
                            <th class="p-4 col-sentiment">Crypto</th>
                            <th class="p-4 col-sentiment">DIX</th>
                            <th class="p-4 col-sentiment">GEX</th>
                            <th class="p-4 col-sentiment">Tot P/C</th>
                            <th class="p-4 col-sentiment">Eq P/C</th>
                            <th class="p-4 col-sentiment">NAAIM</th>
                            <th class="p-4 col-sentiment">AAII</th>
                            <th class="p-4 col-breadth text-nowrap">NY 20</th>
                            <th class="p-4 col-breadth text-nowrap">NQ 20</th>
                            <th class="p-4 col-breadth text-nowrap">NY 50</th>
                            <th class="p-4 col-breadth text-nowrap">NQ 50</th>
                            <th class="p-4 col-credit">10Y-3M</th>
                            <th class="p-4 col-credit">HYG/LQD</th>
                            <th class="p-4 col-macro">XLY/XLP</th>
                            <th class="p-4 col-macro text-nowrap">C/G Ratio</th>
                            <th class="p-4 col-macro text-nowrap">KBE/SPY</th>
                            <th class="p-4 col-macro text-nowrap">QQQ/SPY</th>
                            <th class="p-4 col-macro text-nowrap">RSP/SPY</th>
                            <th class="p-4 col-credit">HYG/IEF</th>
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
                tr.className = 'border-t border-slate-100 hover:bg-slate-50/50 transition-colors';
                tr.innerHTML = `
                    <td class="p-4 px-5 text-[11px] font-black text-slate-800 bg-slate-50/20">${row.Date}</td>
                    <td class="p-4 text-[11px] font-black text-sky-700 col-sentiment">${row.CNN || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row.VIX || '--'}</td>
                    <td class="p-4 text-[11px] font-bold text-red-600 col-credit">${row['HY OAS'] || '--'}</td>
                    <td class="p-4 text-[11px] font-bold text-amber-600 col-sentiment">${row['Crypto F&G'] || '--'}</td>
                    <td class="p-4 text-[11px] text-blue-700 font-bold col-sentiment">${row.DIX || '--'}%</td>
                    <td class="p-4 text-[11px] text-purple-700 font-black col-sentiment">${row.GEX || '--'}B</td>
                    <td class="p-4 text-[11px] col-sentiment">${row['Total P/C Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row['Equity P/C Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row.NAAIM || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row['AAII B-B'] || '--'}</td>
                    <td class="p-4 text-[11px] text-emerald-600 font-black col-breadth">${row['NYSE above 20MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] text-emerald-600 font-black col-breadth">${row['NASDAQ above 20MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] text-indigo-500 font-bold col-breadth">${row['NYSE above 50MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] text-indigo-500 font-bold col-breadth">${row['NASDAQ above 50MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] col-credit ${row['10Y-3M Spread'] < 0 ? 'text-red-500 font-black' : ''}">${row['10Y-3M Spread'] || '--'}</td>
                    <td class="p-4 text-[11px] font-bold text-orange-600 col-credit">${row['HYG/LQD Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] font-bold text-pink-600 col-macro">${row['XLY/XLP Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-amber-600">${row['Copper/Gold Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-indigo-600">${row['KBE/SPY Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-blue-600">${row['QQQ/SPY Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-slate-600">${row['RSP/SPY Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-credit font-bold text-red-600">${row['HYG/IEF Ratio'] || '--'}</td>
                `;
                tableBody.appendChild(tr);
            });
        };

        const switchTab = (cat) => {
            currentTab = cat;
            document.querySelectorAll('button[id^="tab-"]').forEach(btn => btn.classList.remove('active-tab'));
            document.getElementById('tab-' + cat).classList.add('active-tab');

            const allCols = ['col-breadth', 'col-sentiment', 'col-macro', 'col-credit'];
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

        const tabs = ['sentiment', 'breadth', 'credit', 'macro', 'all'];
        let currentTab = 'sentiment';

        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                let idx = tabs.indexOf(currentTab);
                if (e.key === 'ArrowRight') idx = (idx + 1) % tabs.length;
                else idx = (idx - 1 + tabs.length) % tabs.length;
                switchTab(tabs[idx]);
            }
        });

        renderTable();
        switchTab('sentiment');
    </script>
"""

def main():
    if not os.path.exists(DATA_FILE):
        print("No data found.")
        return

    with open(DATA_FILE, 'r') as f:
        history = json.load(f)

    ma_history = []
    if os.path.exists(MA_FILE):
        with open(MA_FILE, 'r') as f:
            ma_history = json.load(f)

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
        "ma_json": json.dumps(ma_history),
        "active_dash": "",
        "active_hist": ""
    }

    # index.html
    ctx.update({"title": "儀表板", "active_dash": "active-tab", "active_hist": ""})
    index_html = Template(BASE_HEAD + DASHBOARD_BODY + BASE_FOOTER).render(**ctx)
    
    # history.html
    ctx.update({"title": "歷史紀錄", "active_dash": "", "active_hist": "active-tab"})
    history_html = Template(BASE_HEAD + HISTORY_BODY + BASE_FOOTER).render(**ctx)

    os.makedirs("public", exist_ok=True)
    
    pages = {
        "index.html": index_html,
        "history.html": history_html
    }
    
    for name, content in pages.items():
        with open(f"public/{name}", "w") as f: f.write(content)

    print("Pages generated successfully.")

if __name__ == "__main__":
    main()
