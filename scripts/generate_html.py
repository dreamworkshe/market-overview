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

DASHBOARD_BODY = """
        <div id="regimeSection"></div>

        <div id="dashboardGroups" class="space-y-8">
            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-sky-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">市場情緒 Sentiment</h2>
                </div>
                <div class="grid grid-cols-5 gap-3" id="sentimentGrid"></div>
            </section>

            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-emerald-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">市場廣度 Breadth</h2>
                </div>
                <div class="grid grid-cols-5 gap-3" id="breadthGrid"></div>
            </section>

            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-blue-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">宏觀流動性 Liquidity</h2>
                </div>
                <div class="grid grid-cols-5 gap-3" id="liquidityGrid"></div>
            </section>

            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-amber-500 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">信用與風險 Credit & Risk</h2>
                </div>
                <div class="grid grid-cols-5 gap-3" id="creditGrid"></div>
            </section>

            <section>
                <div class="flex items-center gap-2 mb-2 px-1">
                    <div class="w-1 h-3 bg-indigo-600 rounded-full"></div>
                    <h2 class="text-[11px] font-black text-slate-500 uppercase tracking-widest leading-none">跨市分析 Intermarket</h2>
                </div>
                <div class="grid grid-cols-5 gap-3" id="macroGrid"></div>
            </section>

                <div class="grid grid-cols-5 gap-3" id="macroGrid"></div>
            </section>
        </div>

    <script>
        const rawData = {{ history_json }};
        const maData = {{ ma_json }};
        const latest = rawData[rawData.length - 1];
        const latestMA = maData.find(m => m.Date === latest.Date) || {};

        const formatVal = (v, sfx) => {
            if (v === undefined || v === null || v === '--') return '--';
            let num = parseFloat(v);
            if (isNaN(num)) return v;
            
            // Special handling for Big liquidity numbers (Billions -> Trillions if too big)
            if (sfx === 'B' && Math.abs(num) >= 1000) {
                return (num / 1000).toFixed(2) + 'T';
            }
            
            // Add commas for large numbers
            if (Math.abs(num) >= 1000) {
                return num.toLocaleString(undefined, { maximumFractionDigits: 2 }) + sfx;
            }
            
            return num + sfx;
        };

        const getTrend = (v1, v2, v3, reverse = false) => {
            if (v1 === undefined || v2 === undefined || v3 === undefined || v1 === '--' || v2 === '--' || v3 === '--') 
                return { icon: '', color: '' };
            
            const upColor = reverse ? 'text-red-500' : 'text-emerald-500';
            const downColor = reverse ? 'text-emerald-500' : 'text-red-500';

            if (v1 > v2 && v2 > v3) return { icon: 'trending-up', color: upColor };
            if (v1 < v2 && v2 < v3) return { icon: 'trending-down', color: downColor };
            return { icon: 'minus', color: 'text-slate-400' };
        };

        const categories = {
            sentimentGrid: [
                { label: 'CNN F&G', col: 'CNN' },
                { label: 'VIX', col: 'VIX', reverse: true },
                { label: 'VIX/VIX3M', col: 'VIX/VIX3M Ratio' },
                { label: 'SKEW', col: 'SKEW' },
                { label: 'Dark Pool (DIX)', col: 'DIX', suffix: '%' },
                { label: 'Gamma (GEX)', col: 'GEX', suffix: 'B' },
                { label: 'Total P/C', col: 'Total P/C Ratio', reverse: true },
                { label: 'Equity P/C', col: 'Equity P/C Ratio', reverse: true },
                { label: 'NAAIM 曝險', col: 'NAAIM', weekly: true },
                { label: 'AAII Spread', col: 'AAII B-B', weekly: true }
            ],
            breadthGrid: [
                { label: 'NYSE 淨新高', col: 'Net New Highs', suffix: '%' },
                { label: 'NYSE > 20D', col: 'NYSE above 20MA', suffix: '%' },
                { label: 'NASD > 20D', col: 'NASDAQ above 20MA', suffix: '%' },
                { label: 'NYSE > 50D', col: 'NYSE above 50MA', suffix: '%' },
                { label: 'NASD > 50D', col: 'NASDAQ above 50MA', suffix: '%' },
                { label: 'McClellan 指數', col: 'McClellan Summation' }
            ],
            liquidityGrid: [
                { label: 'Fed 淨流動性', col: 'Fed Liquidity', suffix: 'B' },
                { label: '逆回購 (RRP)', col: 'RRP', suffix: 'B', reverse: true },
                { label: '財政部 TGA', col: 'TGA', suffix: 'B', reverse: true },
                { label: 'DXY 美元指數', col: 'DXY', reverse: true },
                { label: 'TLT 長債 ETF', col: 'TLT' }
            ],
            creditGrid: [
                { label: '10Y-3M Spread', col: '10Y-3M Spread' },
                { label: 'HYG/LQD', col: 'HYG/LQD Ratio' },
                { label: 'HYG/IEF', col: 'HYG/IEF Ratio' },
                { label: 'HY OAS', col: 'HY OAS', reverse: true }
            ],
            macroGrid: [
                { label: 'Copper/Gold', col: 'Copper/Gold Ratio' },
                { label: 'QQQ/SPY', col: 'QQQ/SPY Ratio' },
                { label: 'RSP/SPY', col: 'RSP/SPY Ratio' },
                { label: 'XLY/XLP', col: 'XLY/XLP Ratio' },
                { label: 'KBE/SPY', col: 'KBE/SPY Ratio' }
            ]
        };

        const renderSparkline = (canvasId, data, color) => {
            const el = document.getElementById(canvasId);
            if (!el) return;
            const ctx = el.getContext('2d');
            const sparkColor = '#94a3b8';
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

        const calculateRegimeScore = () => {
            const parseVal = (v) => {
                if (v === undefined || v === null || v === '--') return null;
                const n = parseFloat(v);
                return isNaN(n) ? null : n;
            };
            
            const getVal = (col) => {
                let v = parseVal(latest[col]);
                if (v !== null) return v;
                for (let i = rawData.length - 2; i >= 0; i--) {
                    v = parseVal(rawData[i][col]);
                    if (v !== null) return v;
                }
                return 50;
            };
            
            const getMA = (col, period) => {
                const v = parseVal(latestMA[col + '_' + period + 'MA']);
                return v !== null ? v : 50;
            };

            const norm = (val, min, max, rev = false) => {
                const nv = parseVal(val) ?? 50;
                if (max === min) return 50;
                let p = (nv - min) / (max - min) * 100;
                if (rev) p = 100 - p;
                return Math.max(0, Math.min(100, p));
            };

            const breadthScore = (norm(getVal('NYSE above 50MA'), 30, 75) + norm(getVal('McClellan Summation'), -100, 100)) / 2;
            const creditScore = (norm(getVal('HY OAS'), 5.0, 2.5) + norm(getVal('VIX'), 35, 12) + (getMA('HYG/LQD Ratio', 5) > getMA('HYG/LQD Ratio', 20) ? 100 : 20)) / 3;
            const flowScore = (norm(getVal('DIX'), 38, 48) + norm(getVal('GEX'), -2, 8)) / 2;
            const sentimentScore = (norm(getVal('CNN'), 80, 20) + norm(getVal('AAII B-B'), 30, -20) + norm(getVal('VIX/VIX3M Ratio'), 0.7, 1.1) + norm(getVal('SKEW'), 145, 115)) / 4;
            const macroScore = ((getMA('Fed Liquidity', 5) > getMA('Fed Liquidity', 20) ? 100 : 20) + norm(getVal('DXY'), 106, 100)) / 2;
            const intermarketScore = getMA('XLY/XLP Ratio', 5) > getMA('XLY/XLP Ratio', 20) ? 100 : 20;

            const totalScore = Math.round(breadthScore*0.25 + creditScore*0.20 + flowScore*0.20 + sentimentScore*0.15 + macroScore*0.15 + intermarketScore*0.05);

            return {
                total: totalScore,
                breadth: Math.round(breadthScore), credit: Math.round(creditScore),
                flow: Math.round(flowScore), sentiment: Math.round(sentimentScore), macro: Math.round(macroScore)
            };
        };

        const renderRegimeHeader = () => {
            const score = calculateRegimeScore();
            let label, color, bgColor, icon, insight;
            if (score.total >= 75) { label = '積極做多'; color = 'text-emerald-500'; bgColor = 'bg-emerald-500'; icon = 'rocket'; insight = '市場環境極佳，各項指標均顯示強勁動能。'; }
            else if (score.total >= 60) { label = '偏多看待'; color = 'text-emerald-500'; bgColor = 'bg-emerald-500'; icon = 'trending-up'; insight = '市場處於上升趨勢，風險偏好回升。'; }
            else if (score.total >= 40) { label = '中性盤整'; color = 'text-amber-500'; bgColor = 'bg-amber-400'; icon = 'minus'; insight = '市場多空交戰，方向不明。建議保持中性倉位。'; }
            else if (score.total >= 25) { label = '保守警戒'; color = 'text-orange-500'; bgColor = 'bg-orange-400'; icon = 'alert-triangle'; insight = '環境轉弱，風險指標升溫。建議縮減倉位。'; }
            else { label = '極度危險'; color = 'text-red-600'; bgColor = 'bg-red-500'; icon = 'shield-alert'; insight = '市場處於極端負面環境，建議觀望防禦。'; }

            if (score.flow > score.breadth + 30) insight = '🔥 偵測到「聰明錢底部吸納」模式：暗池買進力道極強。';
            if (score.breadth > score.sentiment + 30) insight = '⚖️ 偵測到「隱性健康」模式：內部廣度正悄悄改善。';
            if (score.sentiment > score.flow + 30) insight = '⚠️ 偵測到「誘多陷阱」模式：情緒過熱但資金流向撤退。';

            const container = document.getElementById('regimeSection');
            if (!container) return;
            container.innerHTML = `
                <div class="bg-white p-3 px-4 rounded-2xl border border-slate-200 shadow-sm mb-4">
                    <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
                        <div class="flex items-center gap-3">
                            <div class="w-11 h-11 rounded-xl ${bgColor} flex items-center justify-center text-white shadow-md shadow-current/10 shrink-0">
                                <span class="text-lg font-black">${score.total}</span>
                            </div>
                            <div>
                                <div class="flex items-center gap-1.5"><h2 class="text-sm font-black text-slate-800 tracking-tight">${label}</h2><i data-lucide="${icon}" class="${color} w-3.5 h-3.5"></i></div>
                                <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest leading-none">Market Regime Index</p>
                            </div>
                        </div>
                        <div class="flex flex-1 flex-col md:flex-row md:items-center gap-4 md:px-6">
                            <div class="flex-1 max-w-xs"><div class="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-100"><div class="h-full rounded-full ${bgColor} transition-all duration-1000" style="width: ${score.total}%"></div></div></div>
                            <div class="flex gap-3 text-[9px] font-black uppercase tracking-widest">
                                <span class="flex items-center gap-1 text-slate-400">廣度 <span class="text-slate-700">${score.breadth}</span></span>
                                <span class="flex items-center gap-1 text-slate-400">信用 <span class="text-slate-700">${score.credit}</span></span>
                                <span class="flex items-center gap-1 text-slate-400">資金 <span class="text-slate-700">${score.flow}</span></span>
                                <span class="flex items-center gap-1 text-slate-400">情緒 <span class="text-slate-700">${score.sentiment}</span></span>
                                <span class="flex items-center gap-1 text-slate-400">宏觀 <span class="text-slate-700">${score.macro}</span></span>
                            </div>
                        </div>
                        <div class="md:text-right shrink-0">
                            <span class="text-[10px] font-bold text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100 inline-flex items-center gap-2"><span class="w-1 h-1 rounded-full bg-slate-300"></span>${insight}</span>
                        </div>
                    </div>
                </div>
            `;
            lucide.createIcons();
        };

        const renderGrid = (id, items) => {
            const grid = document.getElementById(id);
            if (!grid) return;
            items.forEach((m, idx) => {
                let targetIdx = rawData.length - 1;
                let val = latest[m.col];
                let isStale = (val === undefined || val === null || val === '--');
                if (isStale) {
                    for (let i = rawData.length - 2; i >= 0; i--) {
                        if (rawData[i][m.col] !== undefined && rawData[i][m.col] !== null && rawData[i][m.col] !== '--') {
                            val = rawData[i][m.col]; targetIdx = i; break;
                        }
                    }
                }
                const sfx = m.suffix || '', canvasId = `sparkline-${id}-${idx}`;
                let v1, v2, v3, labels, trend;
                if (m.weekly) {
                    v1 = rawData[targetIdx - 5] ? rawData[targetIdx - 5][m.col] : '--';
                    v2 = rawData[targetIdx - 10] ? rawData[targetIdx - 10][m.col] : '--';
                    v3 = rawData[targetIdx - 15] ? rawData[targetIdx - 15][m.col] : '--';
                    labels = ['1W', '2W', '3W'];
                    trend = getTrend(val, v1, v2);
                } else {
                    const lma = maData.find(ma => ma.Date === rawData[targetIdx].Date) || {};
                    v1 = lma[m.col + '_5MA'] || '--'; v2 = lma[m.col + '_10MA'] || '--'; v3 = lma[m.col + '_20MA'] || '--';
                    labels = ['5MA', '10MA', '20MA']; trend = getTrend(v1, v2, v3, m.reverse);
                }
                const sparkData = rawData.slice(-20).map(d => d[m.col]).filter(v => v !== undefined && v !== null);
                grid.innerHTML += `
                    <div class="bg-white p-3 px-4 rounded-2xl card-hover border border-slate-200 shadow-sm transition-all duration-300 ${isStale ? 'stale-card' : ''}">
                        <div class="flex items-center justify-between mb-1"><div class="flex items-center gap-2"><span class="text-slate-400 text-[9px] font-bold uppercase tracking-widest">${m.label}</span>${isStale ? '<span class="stale-tag">DELAYED</span>' : ''}</div><i data-lucide="${trend.icon}" class="${trend.color} w-3.5 h-3.5"></i></div>
                        <div class="flex items-end justify-between gap-1 mb-2">
                            <div class="text-2xl font-black tracking-tighter text-slate-900">${formatVal(val, sfx)}</div>
                            <div class="w-16 h-8"><canvas id="${canvasId}"></canvas></div>
                        </div>
                        <div class="mt-1 pt-2 border-t border-slate-50 flex justify-between items-center text-[10px] font-bold text-slate-400">
                            <div class="flex flex-col"><span class="text-[8px] uppercase tracking-tighter text-slate-300">${labels[0]}</span><span class="text-slate-500 font-mono">${formatVal(v1, sfx)}</span></div>
                            <div class="flex flex-col"><span class="text-[8px] uppercase tracking-tighter text-slate-300">${labels[1]}</span><span class="text-slate-500 font-mono">${formatVal(v2, sfx)}</span></div>
                            <div class="flex flex-col"><span class="text-[8px] uppercase tracking-tighter text-slate-300">${labels[2]}</span><span class="text-slate-500 font-mono">${formatVal(v3, sfx)}</span></div>
                        </div>
                    </div>
                `;
                setTimeout(() => renderSparkline(canvasId, sparkData, m.color), 0);
            });
        };
        renderGrid('sentimentGrid', categories.sentimentGrid);
        renderGrid('breadthGrid', categories.breadthGrid);
        renderGrid('liquidityGrid', categories.liquidityGrid);
        renderGrid('creditGrid', categories.creditGrid);
        renderGrid('macroGrid', categories.macroGrid);
        renderRegimeHeader();
    </script>
"""

HISTORY_BODY = """
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div class="flex flex-wrap gap-1.5 p-1 bg-slate-100 rounded-2xl border border-slate-200">
                <button onclick="switchTab('sentiment')" id="tab-sentiment" class="px-5 py-2 rounded-xl text-xs font-bold transition-all active-tab shadow-sm">市場情緒</button>
                <button onclick="switchTab('breadth')" id="tab-breadth" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">市場廣度</button>
                <button onclick="switchTab('liquidity')" id="tab-liquidity" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">宏觀流動性</button>
                <button onclick="switchTab('credit')" id="tab-credit" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">信用與風險</button>
                <button onclick="switchTab('macro')" id="tab-macro" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">跨市分析</button>
                <button onclick="switchTab('all')" id="tab-all" class="px-5 py-2 rounded-xl text-xs font-bold transition-all hover:bg-white text-slate-500">全部紀錄</button>
            </div>
            <div class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-2xl shadow-sm">
                <i data-lucide="keyboard" class="w-4 h-4 text-slate-400"></i>
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">方向鍵 ← → 切換分頁</span>
            </div>
        </div>

        <div class="bg-white rounded-[2rem] overflow-hidden shadow-xl border border-slate-200">
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse min-w-[1000px]">
                    <thead class="bg-slate-50 text-slate-400 text-[9px] font-black uppercase tracking-[0.15em] border-b border-slate-200">
                        <tr>
                            <th class="p-4 px-5">日期</th>
                            <th class="p-4 col-sentiment">CNN</th><th class="p-4 col-sentiment">VIX</th><th class="p-4 col-sentiment">VIX/3M</th><th class="p-4 col-sentiment">SKEW</th><th class="p-4 col-sentiment">DIX</th><th class="p-4 col-sentiment">GEX</th><th class="p-4 col-sentiment">Tot P/C</th><th class="p-4 col-sentiment">Eq P/C</th><th class="p-4 col-sentiment">NAAIM</th><th class="p-4 col-sentiment">AAII</th>
                            <th class="p-4 col-breadth">Net Highs</th><th class="p-4 col-breadth">NY 20</th><th class="p-4 col-breadth">NQ 20</th><th class="p-4 col-breadth">NY 50</th><th class="p-4 col-breadth">NQ 50</th><th class="p-4 col-breadth">McClellan</th>
                            <th class="p-4 col-liquidity">Fed Liq</th><th class="p-4 col-liquidity">RRP</th><th class="p-4 col-liquidity">TGA</th><th class="p-4 col-liquidity">DXY</th><th class="p-4 col-liquidity">TLT</th>
                            <th class="p-4 col-credit">10Y-3M</th><th class="p-4 col-credit">HYG/LQD</th><th class="p-4 col-credit">HYG/IEF</th><th class="p-4 col-credit">HY OAS</th>
                            <th class="p-4 col-macro">C/G Ratio</th><th class="p-4 col-macro">QQQ/SPY</th><th class="p-4 col-macro">XLY/XLP</th><th class="p-4 col-macro">RSP/SPY</th><th class="p-4 col-macro">KBE/SPY</th>
                        </tr>
                    </thead>
                    <tbody id="dataTableBody" class="text-slate-600"></tbody>
                </table>
            </div>
        </div>

    <script>
        const rawData = {{ history_json }};
        const tableBody = document.getElementById('dataTableBody');
        
        const formatVal = (v, sfx = '') => {
            if (v === undefined || v === null || v === '--') return '--';
            let num = parseFloat(v);
            if (isNaN(num)) return v;
            if (sfx === 'B' && Math.abs(num) >= 1000) {
                return (num / 1000).toFixed(2) + 'T';
            }
            if (Math.abs(num) >= 1000) {
                return num.toLocaleString(undefined, { maximumFractionDigits: 2 }) + sfx;
            }
            return num + sfx;
        };

        const renderTable = () => {
            tableBody.innerHTML = '';
            [...rawData].sort((a,b) => new Date(b.Date) - new Date(a.Date)).forEach(row => {
                const tr = document.createElement('tr');
                tr.className = 'border-t border-slate-100 hover:bg-slate-50/50 transition-colors';
                tr.innerHTML = `
                    <td class="p-4 px-5 text-[11px] font-black text-slate-800 bg-slate-50/20">${row.Date}</td>
                    <td class="p-4 text-[11px] font-black text-sky-700 col-sentiment">${row.CNN || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row.VIX || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment font-mono">${row['VIX/VIX3M Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment font-mono">${row.SKEW || '--'}</td>
                    <td class="p-4 text-[11px] text-blue-700 font-bold col-sentiment">${row.DIX || '--'}%</td>
                    <td class="p-4 text-[11px] text-purple-700 font-black col-sentiment">${formatVal(row.GEX, 'B')}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row['Total P/C Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row['Equity P/C Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row.NAAIM || '--'}</td>
                    <td class="p-4 text-[11px] col-sentiment">${row['AAII B-B'] || '--'}</td>
                    <td class="p-4 text-[11px] col-breadth font-black text-emerald-600">${row['Net New Highs'] || '--'}%</td>
                    <td class="p-4 text-[11px] col-breadth">${row['NYSE above 20MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] col-breadth">${row['NASDAQ above 20MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] col-breadth">${row['NYSE above 50MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] col-breadth">${row['NASDAQ above 50MA'] || '--'}%</td>
                    <td class="p-4 text-[11px] col-breadth font-black text-emerald-600">${row['McClellan Summation'] || '--'}</td>
                    <td class="p-4 text-[11px] col-liquidity font-mono text-blue-700">${formatVal(row['Fed Liquidity'], 'B')}</td>
                    <td class="p-4 text-[11px] col-liquidity font-mono">${formatVal(row.RRP, 'B')}</td>
                    <td class="p-4 text-[11px] col-liquidity font-mono">${formatVal(row.TGA, 'B')}</td>
                    <td class="p-4 text-[11px] col-liquidity font-bold">${row.DXY || '--'}</td>
                    <td class="p-4 text-[11px] col-liquidity font-bold">${row.TLT || '--'}</td>
                    <td class="p-4 text-[11px] col-credit ${row['10Y-3M Spread'] < 0 ? 'text-red-500 font-black' : ''}">${row['10Y-3M Spread'] || '--'}</td>
                    <td class="p-4 text-[11px] col-credit font-mono">${row['HYG/LQD Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-credit font-mono">${row['HYG/IEF Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-credit font-bold text-red-600">${row['HY OAS'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-amber-600">${row['Copper/Gold Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-blue-600">${row['QQQ/SPY Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-pink-600">${row['XLY/XLP Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-slate-600">${row['RSP/SPY Ratio'] || '--'}</td>
                    <td class="p-4 text-[11px] col-macro font-bold text-indigo-600">${row['KBE/SPY Ratio'] || '--'}</td>
                `;
                tableBody.appendChild(tr);
            });
        };
        const switchTab = (cat) => {
            currentTab = cat;
            document.querySelectorAll('button[id^="tab-"]').forEach(btn => btn.classList.remove('active-tab'));
            document.getElementById('tab-' + cat).classList.add('active-tab');
            const cols = {
                sentiment: document.querySelectorAll('.col-sentiment'), breadth: document.querySelectorAll('.col-breadth'),
                liquidity: document.querySelectorAll('.col-liquidity'), credit: document.querySelectorAll('.col-credit'),
                macro: document.querySelectorAll('.col-macro')
            };
            Object.values(cols).forEach(list => list.forEach(el => el.style.display = 'none'));
            if (cat === 'all') Object.values(cols).forEach(list => list.forEach(el => el.style.display = ''));
            else if (cols[cat]) cols[cat].forEach(el => el.style.display = '');
        };
        const tabs = ['sentiment', 'breadth', 'liquidity', 'credit', 'macro', 'all'];
        let currentTab = 'sentiment';
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                let idx = tabs.indexOf(currentTab);
                if (e.key === 'ArrowRight') idx = (idx + 1) % tabs.length;
                else idx = (idx - 1 + tabs.length) % tabs.length;
                switchTab(tabs[idx]);
            }
        });
        renderTable(); switchTab('sentiment');
    </script>
"""

def main():
    if not os.path.exists(DATA_FILE): return
    with open(DATA_FILE, 'r') as f: history = json.load(f)
    ma_history = []
    if os.path.exists(MA_FILE):
        with open(MA_FILE, 'r') as f: ma_history = json.load(f)
    latest = history[-1]
    ctx = { "last_date": latest['Date'], "history_json": json.dumps(history), "ma_json": json.dumps(ma_history) }
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w") as f: f.write(Template(BASE_HEAD + DASHBOARD_BODY + BASE_FOOTER).render(title="儀表板", active_dash="active-tab", active_hist="", **ctx))
    with open("public/history.html", "w") as f: f.write(Template(BASE_HEAD + HISTORY_BODY + BASE_FOOTER).render(title="歷史紀錄", active_dash="", active_hist="active-tab", **ctx))
    print("Pages generated successfully.")

if __name__ == "__main__":
    main()
