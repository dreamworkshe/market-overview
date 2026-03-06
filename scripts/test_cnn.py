import requests
from bs4 import BeautifulSoup

def fetch_cnn_fg():
    url = "https://www.cnn.com/markets/fear-and-greed"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    element = soup.find('div', class_='market-fng-gauge__dial-number-value')
    if element:
        return element.text.strip()
    # Try finding it in script if UI changed
    import re
    match = re.search(r'"ratingValue":\s*(\d+)', response.text)
    if match:
        return match.group(1)
    return "N/A"

if __name__ == "__main__":
    print(f"CNN F&G: {fetch_cnn_fg()}")
