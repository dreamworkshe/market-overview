import json
import os
from jinja2 import Template

DATA_FILE = "data/history.json"
OUTPUT_FILE = "index.html"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>市場概況儀表板 | Market Overview</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .gradient-text { background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .card-hover:hover { transform: translateY(-4px); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto">
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
            <div>
                <h1 class="text-4xl font-bold gradient-text">市場數據儀表板</h1>
                <p class="text-slate-400 mt-2">最後交易日: <span id="lastUpdated" class="text-slate-200">正在載入...</span> (美股日期 / NY Time)</p>
            </div>
            <div class="glass px-6 py-3 rounded-2xl flex items-center gap-4">
                <div class="flex flex-col">
                    <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">CNN Fear & Greed</span>
                    <span id="cnnValue" class="text-2xl font-bold">-</span>
                </div>
                <div id="cnnGauge" class="w-12 h-12 rounded-full border-4 border-slate-700 flex items-center justify-center">
                    <div class="w-2 h-2 rounded-full bg-sky-400 animate-pulse"></div>
                </div>
            </div>
        </header>

        <!-- Metrics Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10" id="metricsGrid">
            <!-- Cards will be injected by JS -->
        </div>

        <!-- Charts Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
            <div class="glass p-6 rounded-3xl">
                <h3 class="text-xl font-semibold mb-6 flex items-center gap-2">
                    <i data-lucide="trending-up" class="text-sky-400"></i> 情緒指標趨勢
                </h3>
                <div class="h-80">
                    <canvas id="sentimentChart"></canvas>
                </div>
            </div>
            <div class="glass p-6 rounded-3xl">
                <h3 class="text-xl font-semibold mb-6 flex items-center gap-2">
                    <i data-lucide="bar-chart-3" class="text-purple-400"></i> 市場廣度 (Moving Averages)
                </h3>
                <div class="h-80">
                    <canvas id="breadthChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Data Table -->
        <div class="glass rounded-3xl overflow-hidden mb-10">
            <div class="p-6 border-b border-white/10">
                <h3 class="text-xl font-semibold">歷史數據紀錄</h3>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-white/5 text-slate-400 text-sm uppercase">
                        <tr>
                            <th class="p-4">交易日期 (US)</th>
                            <th class="p-4">CNN</th>
                            <th class="p-4">VIX</th>
                            <th class="p-4">Total P/C</th>
                            <th class="p-4">Equity P/C</th>
                            <th class="p-4">NAAIM</th>
                            <th class="p-4">AAII DIFF</th>
                            <th class="p-4">NYSE 20</th>
                            <th class="p-4">NASD 20</th>
                            <th class="p-4">NYSE 50</th>
                            <th class="p-4">NASD 50</th>
                        </tr>
                    </thead>
                    <tbody id="dataTableBody" class="text-slate-300">
                        <!-- Table rows injected here -->
                    </tbody>
                </table>
            </div>
        </div>
        
        <footer class="text-center text-slate-500 text-sm py-8">
            <p>本網頁由 AI 自動定時抓取更新 | 免費金融數據方案</p>
        </footer>
    </div>

    <script>
        const rawData = {{ history_json }};
        const latest = rawData[rawData.length - 1];

        document.getElementById('lastUpdated').innerText = latest.Date;
        document.getElementById('cnnValue').innerText = latest.CNN || 'N/A';
        
        // Color for CNN
        const cnnGauge = document.getElementById('cnnGauge');
        if (latest.CNN < 25) cnnGauge.style.borderColor = '#ef4444';
        else if (latest.CNN < 45) cnnGauge.style.borderColor = '#f97316';
        else if (latest.CNN < 55) cnnGauge.style.borderColor = '#eab308';
        else if (latest.CNN < 75) cnnGauge.style.borderColor = '#84cc16';
        else cnnGauge.style.borderColor = '#22c55e';

        // Main Metrics UI
        const metrics = [
            { label: 'VIX 指數', value: latest.VIX, icon: 'alert-triangle', color: 'text-orange-400' },
            { label: 'Total P/C Ratio', value: latest['Total P/C Ratio'], icon: 'activity', color: 'text-indigo-400' },
            { label: 'NAAIM 曝險', value: latest.NAAIM, icon: 'user-check', color: 'text-emerald-400' },
            { label: 'AAII B-B Spread', value: latest['AAII B-B'], icon: 'users', color: 'text-pink-400' }
        ];

        const grid = document.getElementById('metricsGrid');
        metrics.forEach(m => {
            const card = document.createElement('div');
            card.className = 'glass p-6 rounded-3xl card-hover';
            card.innerHTML = `
                <div class="flex items-center justify-between mb-4">
                    <span class="text-slate-400 text-sm font-medium uppercase tracking-tight">${m.label}</span>
                    <i data-lucide="${m.icon}" class="${m.color} w-5 h-5"></i>
                </div>
                <div class="text-3xl font-bold">${m.value || 'N/A'}</div>
            `;
            grid.appendChild(card);
        });

        // Charts
        const labels = rawData.map(d => d.Date);

        new Chart(document.getElementById('sentimentChart'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    { label: 'CNN F&G', data: rawData.map(d => d.CNN), borderColor: '#38bdf8', tension: 0.3, fill: false },
                    { label: 'NAAIM', data: rawData.map(d => d.NAAIM), borderColor: '#10b981', tension: 0.3, fill: false },
                    { label: 'VIX (Scaled 2x)', data: rawData.map(d => d.VIX * 2), borderColor: '#f43f5e', tension: 0.3, borderDash: [5, 5] }
                ]
            },
            options: { 
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#94a3b8' } } },
                scales: { 
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
                }
            }
        });

        new Chart(document.getElementById('breadthChart'), {
            type: 'bar',
            data: {
                labels: ['NYSE > 20MA', 'NASD > 20MA', 'NYSE > 50MA', 'NASD > 50MA'],
                datasets: [{
                    label: '最新比例 (%)',
                    data: [
                        latest['NYSE above 20MA'], 
                        latest['NASDAQ above 20MA'], 
                        latest['NYSE above 50MA'], 
                        latest['NASDAQ above 50MA']
                    ],
                    backgroundColor: ['#60a5fa', '#a78bfa', '#34d399', '#f472b6'],
                    borderRadius: 12
                }]
            },
            options: { 
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { 
                    y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                }
            }
        });

        // Table
        const tableBody = document.getElementById('dataTableBody');
        [...rawData].reverse().forEach(row => {
            const tr = document.createElement('tr');
            tr.className = 'border-t border-white/5 hover:bg-white/5 transition-colors';
            tr.innerHTML = `
                <td class="p-4 text-sm">${row.Date}</td>
                <td class="p-4 font-semibold text-sky-400">${row.CNN || '-'}</td>
                <td class="p-4">${row.VIX || '-'}</td>
                <td class="p-4">${row['Total P/C Ratio'] || '-'}</td>
                <td class="p-4">${row['Equity P/C Ratio'] || '-'}</td>
                <td class="p-4">${row.NAAIM || '-'}</td>
                <td class="p-4">${row['AAII B-B'] || '-'}</td>
                <td class="p-4 text-emerald-400 text-xs">${row['NYSE above 20MA'] || '-'}%</td>
                <td class="p-4 text-emerald-400 text-xs">${row['NASDAQ above 20MA'] || '-'}%</td>
                <td class="p-4 text-indigo-400 text-xs">${row['NYSE above 50MA'] || '-'}%</td>
                <td class="p-4 text-indigo-400 text-xs">${row['NASDAQ above 50MA'] || '-'}%</td>
            `;
            tableBody.appendChild(tr);
        });

        lucide.createIcons();
    </script>
</body>
</html>
"""

def main():
    if not os.path.exists(DATA_FILE):
        print("No data file found.")
        return

    with open(DATA_FILE, 'r') as f:
        history = json.load(f)

    # Simple Jinja-like injection (or use Jinja if available)
    html_content = HTML_TEMPLATE.replace("{{ history_json }}", json.dumps(history))
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html_content)
    
    # Also save to public/ for web serving
    if not os.path.exists("public"):
        os.makedirs("public")
    with open("public/index.html", "w") as f:
        f.write(html_content)

    print("HTML Dashboard generated successfully.")

if __name__ == "__main__":
    main()
