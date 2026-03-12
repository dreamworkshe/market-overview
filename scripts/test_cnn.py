import requests

def fetch_cnn_fg():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        # Prefer historical data points which are more reliable for past/current context
        comp = data.get('fear_and_greed_historical') or data.get('fear_and_greed')
        if comp:
            return round(comp.get('score', 0), 2)
    except Exception as e:
        print(f"Error: {e}")
    return "N/A"

if __name__ == "__main__":
    print(f"CNN F&G: {fetch_cnn_fg()}")
