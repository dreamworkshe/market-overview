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
            <!-- Overview Section: Crucial Market Signals -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-red-600 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">盤勢總覽 Overview</h2>
                </div>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-3" id="overviewGrid"></div>
            </section>

            <!-- Breadth Section -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-emerald-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">市場廣度 Market Breadth</h2>
                </div>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-3" id="breadthGrid"></div>
            </section>

            <!-- Sentiment Section: Full Width Row -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-sky-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">市場情緒 Sentiment</h2>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3" id="sentimentGrid"></div>
            </section>

            <!-- Macro Section: Full Width Row -->
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-blue-600 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">宏觀趨勢 Macro</h2>
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
                return { icon: 'minus', color: 'text-slate-300' };
            if (v1 > v2 && v2 > v3) return { icon: 'trending-up', color: 'text-emerald-500' };
            if (v1 < v2 && v2 < v3) return { icon: 'trending-down', color: 'text-red-500' };
            return { icon: 'minus', color: 'text-slate-300' };
        };

        const categories = {
            overviewGrid: [
                { label: 'Dark Pool (DIX)', col: 'DIX', suffix: '%' },
                { label: 'Gamma (GEX)', col: 'GEX', suffix: 'B' },
                { label: 'Equity P/C', col: 'Equity P/C Ratio' },
                { label: 'Total P/C', col: 'Total P/C Ratio' }
            ],
            breadthGrid: [
                { label: 'NYSE > 20MA', col: 'NYSE above 20MA', suffix: '%' },
                { label: 'NASD > 20MA', col: 'NASDAQ above 20MA', suffix: '%' },
                { label: 'NYSE > 50MA', col: 'NYSE above 50MA', suffix: '%' },
                { label: 'NASD > 50MA', col: 'NASDAQ above 50MA', suffix: '%' }
            ],
            sentimentGrid: [
                { label: 'CNN F&G', col: 'CNN' },
                { label: 'VIX 指數', col: 'VIX' },
                { label: 'NAAIM 曝險', col: 'NAAIM', weekly: true },
                { label: 'AAII Spread', col: 'AAII B-B', weekly: true },
                { label: 'Crypto F&G', col: 'Crypto F&G' }
            ],
            macroGrid: [
                { label: '10Y-3M Spread', col: '10Y-3M Spread' },
                { label: 'HYG/LQD', col: 'HYG/LQD Ratio' },
                { label: 'XLY/XLP', col: 'XLY/XLP Ratio' },
                { label: 'Copper/Gold', col: 'Copper/Gold Ratio' },
                { label: 'KBE/SPY', col: 'KBE/SPY Ratio' }
            ]
        };

        const renderGrid = (id, items) => {
            const grid = document.getElementById(id);
            if (!grid) return;
            items.forEach(m => {
                const val = latest[m.col];
                const sfx = m.suffix || '';
                
                let v1, v2, v3, labels;
                if (m.weekly) {
                    const idx = rawData.length - 1;
                    // Stride by 5 days for weekly data
                    v1 = rawData[idx - 5] ? rawData[idx - 5][m.col] : '--';
                    v2 = rawData[idx - 10] ? rawData[idx - 10][m.col] : '--';
                    v3 = rawData[idx - 15] ? rawData[idx - 15][m.col] : '--';
                    labels = ['1W', '2W', '3W'];
                } else {
                    v1 = latestMA[m.col + '_5MA'] || '--';
                    v2 = latestMA[m.col + '_10MA'] || '--';
                    v3 = latestMA[m.col + '_20MA'] || '--';
                    labels = ['5MA', '10MA', '20MA'];
                }

                const trend = getTrend(v1, v2, v3);

                grid.innerHTML += `
                    <div class="bg-white p-3 px-4 rounded-2xl card-hover border border-slate-200 shadow-sm transition-all duration-300">
                        <div class="flex items-center justify-between mb-1">
                            <span class="text-slate-400 text-[9px] font-bold uppercase tracking-widest">${m.label}</span>
                            <i data-lucide="${trend.icon}" class="${trend.color} w-3.5 h-3.5"></i>
                        </div>
                        <div class="flex items-baseline gap-1">
                            <div class="text-2xl font-black tracking-tighter text-slate-900">${val !== undefined ? val + sfx : '--'}</div>
                        </div>
                        <div class="mt-2 pt-2 border-t border-slate-50 flex justify-between items-center text-[10px] font-bold text-slate-400">
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
            });
        };

        Object.keys(categories).forEach(id => renderGrid(id, categories[id]));
    </script>
"""

# --- HISTORY PAGE ---
HISTORY_BODY = """
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div class="flex flex-wrap gap-1.5 p-1 bg-slate-100 rounded-2xl border border-slate-200">
                <button onclick="switchTab('overview')" id="tab-overview" class="px-5 py-2 rounded-xl text-xs font-bold transition-all active-tab shadow-sm">盤勢總覽</button>
                <button onclick="switchTab('breadth')" id="tab-breadth" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">市場廣度</button>
                <button onclick="switchTab('sentiment')" id="tab-sentiment" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">市場情緒</button>
                <button onclick="switchTab('macro')" id="tab-macro" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">宏觀趨勢</button>
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
                            <th class="p-4 col-overview">DIX</th>
                            <th class="p-4 col-overview">GEX</th>
                            <th class="p-4 col-overview">Eq P/C</th>
                            <th class="p-4 col-overview">Tot P/C</th>
                            <th class="p-4 col-breadth text-nowrap">NY 20</th>
                            <th class="p-4 col-breadth text-nowrap">NQ 20</th>
                            <th class="p-4 col-breadth text-nowrap">NY 50</th>
                            <th class="p-4 col-breadth text-nowrap">NQ 50</th>
                            <th class="p-4 col-sentiment text-nowrap">CNN</th>
                            <th class="p-4 col-sentiment">VIX</th>
                            <th class="p-4 col-sentiment">NAAIM</th>
                            <th class="p-4 col-sentiment">AAII</th>
                            <th class="p-4 col-sentiment">Crypto</th>
                            <th class="p-4 col-macro">10Y-3M</th>
                            <th class="p-4 col-macro">HYG/LQD</th>
                            <th class="p-4 col-macro">XLY/XLP</th>
                            <th class="p-4 col-macro text-nowrap">C/G Ratio</th>
                            <th class="p-4 col-macro text-nowrap">KBE/SPY</th>
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
                    <td class="p-4 text-[11px] text-blue-700 font-bold col-overview">${row.DIX || '--'}%</td>
                    <td class="p-4 text-[11px] text-purple-700 font-black col-overview">${row.GEX || '--'}B</td>
                    <td class="p-4 text-[11px] col-overview">${row['Equity P/C Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-overview">${row['Total P/C Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] text-emerald-600 font-black col-breadth">${row['NYSE above 20MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] text-emerald-600 font-black col-breadth">${row['NASDAQ above 20MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] text-indigo-500 font-bold col-breadth">${row['NYSE above 50MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] text-indigo-500 font-bold col-breadth">${row['NASDAQ above 50MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] font-black text-sky-700 col-sentiment">${row.CNN || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row.VIX || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row.NAAIM || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row['AAII B-B'] || '--'}</td>
                    <td class="p-4 text-[11px] font-bold text-amber-600 col-sentiment">${row['Crypto F&G'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro ${row['10Y-3M Spread'] < 0 ? 'text-red-500 font-black' : ''}">${row['10Y-3M Spread'] || '--'}</td>
                    <td class="p-4 text-[11px] font-bold text-orange-600 col-macro">${row['HYG/LQD Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] font-bold text-pink-600 col-macro">${row['XLY/XLP Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-amber-600">${row['Copper/Gold Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-indigo-600">${row['KBE/SPY Ratio'] || '--'}</td>
                `;
                tableBody.appendChild(tr);
            });
        };

        const switchTab = (cat) => {
            currentTab = cat;
            document.querySelectorAll('button[id^="tab-"]').forEach(btn => btn.classList.remove('active-tab'));
            document.getElementById('tab-' + cat).classList.add('active-tab');

            const allCols = ['col-overview', 'col-breadth', 'col-sentiment', 'col-macro'];
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

        const tabs = ['overview', 'breadth', 'sentiment', 'macro', 'all'];
        let currentTab = 'overview';

        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                let idx = tabs.indexOf(currentTab);
                if (e.key === 'ArrowRight') idx = (idx + 1) % tabs.length;
                else idx = (idx - 1 + tabs.length) % tabs.length;
                switchTab(tabs[idx]);
            }
        });

        renderTable();
        switchTab('overview');
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
