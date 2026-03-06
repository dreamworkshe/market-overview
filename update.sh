#!/bin/bash
# Market Overview Local Update Script

# Get the script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=== 市場數據自動更新程序 ==="

# Check for .venv
if [ ! -d ".venv" ]; then
    echo "未偵測到 .venv，正在建立..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r scripts/requirements.txt
else
    source .venv/bin/activate
fi

echo "正在抓取最新數據..."
python3 scripts/fetch_data.py

echo "正在生成儀表板..."
python3 scripts/generate_html.py

echo "完成！您可以打開 index.html 查看結果。"
deactivate
