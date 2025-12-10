import feedparser
import google.generativeai as genai
import requests
import os
import time
import json

# --- 設定區域 ---
# 修改 1：這裡改成列表 (List)，可以放入無限多個 RSS 網址
RSS_URLS = [
    "https://feeds.bbci.co.uk/zhongwen/trad/rss.xml",           # BBC 中文
    "https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW:zh-Hant", # Google News 台灣
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",    #紐約時報
    "https://news.google.com/rss/topics/CAAqKQgKIiNDQkFTRkFvTEwyY3ZNVEl4Y0Raa09UQVNCWHBvTFZSWEtBQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant" ,     #Google教育新聞
]

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

# --- 初始化 Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def send_line_push(msg):
    """使用 LINE Messaging API 推播訊息"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + LINE_ACCESS_TOKEN
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": msg
            }
        ]
    }
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        if r.status_code == 200:
            print("✅ LINE 訊息推播成功！")
        else:
            print(f"❌ 推播失敗 (Code: {r.status_code}): {r.text}")
    except Exception as e:
        print(f"❌ 連線錯誤: {e}")

def summarize_text(text, source_name):
    """請 Gemini 做摘要"""
    prompt = f"""
    請幫我摘要這則來自【{source_name}】的新聞，適合在 LINE 手機上閱讀。
    
    格式要求：
    1. 第一行只要新聞標題 (前面加上來源標籤)。
    2. 下面列出 3 個重點 (使用條列式)。
    3. 總字數控制在 200 字以內。
    4. 不要使用 markdown 語法 (如 ** 或 ##)。
    
    新聞內容：
    {text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

def main():
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        print("錯誤：找不到 LINE 設定，請檢查 GitHub Secrets (LINE_ACCESS_TOKEN, LINE_USER_ID)。")
        return

    # 修改 2：外層迴圈遍歷所有網站
    for url in RSS_URLS:
        print(f"正在讀取 RSS: {url} ...")
        feed = feedparser.parse(url)
        
        # 取得網站名稱 (如果是空的就顯示 '新聞')
        site_name = feed.feed.title if 'title' in feed.feed else "新聞快訊"
        print(f"來源：{site_name} | 共抓到 {len(feed.entries)} 則新聞")

        # 修改 3：內層迴圈改成取前 5 篇 ([:5])
        # 如果你想改回 3 篇，就把 5 改成 3
        process_count = 0
        for entry in feed.entries[:5]: 
            process_count += 1
            title = entry.title
            link = entry.link
            content = entry.summary if 'summary' in entry else entry.title 
            
            print(f"  [{process_count}/5] 正在處理：{title}")
            
            # 傳入 site_name 讓 AI 知道來源
            summary = summarize_text(content, site_name)
            
            if summary:
                # 組合訊息
                line_message = f"{summary}\n\n🔗 {link}"
                
                # 發送！
                send_line_push(line_message)
                
                # 修改 4：避免瞬間發送太快，暫停 2 秒
                time.sleep(2) 
            else:
                print("  - 摘要失敗")
        
        print(f"--- {site_name} 處理完畢 ---\n")

if __name__ == "__main__":
    main()
