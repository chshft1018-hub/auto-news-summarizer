import feedparser
import google.generativeai as genai
import requests
import os
import time
import json

# --- 設定區域 ---
RSS_URL = "https://feeds.bbci.co.uk/zhongwen/trad/rss.xml" 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# 改用 Messaging API 需要這兩個變數
LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

# --- 初始化 Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def send_line_push(msg):
    """使用 LINE Messaging API 推播訊息 (替代 Notify)"""
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

def summarize_text(text):
    """請 Gemini 做摘要"""
    prompt = f"""
    請幫我摘要這則新聞，適合在 LINE 手機上閱讀。
    
    格式要求：
    1. 第一行只要新聞標題。
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

    print("正在讀取 RSS...")
    feed = feedparser.parse(RSS_URL)
    
    print(f"共抓到 {len(feed.entries)} 則新聞，準備處理最新的 1 則...")

    for entry in feed.entries[:1]:
        title = entry.title
        link = entry.link
        content = entry.summary if 'summary' in entry else entry.title 
        
        print(f"正在處理：{title}")
        
        summary = summarize_text(content)
        
        if summary:
            # 組合訊息
            line_message = f"📰 {summary}\n\n🔗 {link}"
            
            # 發送！
            send_line_push(line_message)
            time.sleep(1) 
        else:
            print(" - 摘要失敗")

if __name__ == "__main__":
    main()
