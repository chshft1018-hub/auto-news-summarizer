import feedparser
import google.generativeai as genai
import gkeepapi
import time
import os  # 新增這個，用來讀取環境變數

# --- 設定區域 (修改為讀取環境變數) ---
# 這些變數我們等一下會在 GitHub 網站上設定，不要寫死在這裡
RSS_URL = "https://feeds.bbci.co.uk/zhongwen/trad/rss.xml" 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_EMAIL = os.environ.get("GOOGLE_EMAIL")
GOOGLE_APP_PASSWORD = os.environ.get("GOOGLE_APP_PASSWORD")

# --- 初始化 Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def summarize_text(text):
    # (這部分與之前相同，略過不重複顯示以節省篇幅)
    prompt = f"""
    請幫我摘要這則新聞，請使用繁體中文。
    格式要求：
    1. 用一句話說明主旨 (加粗)。
    2. 列出 3 個關鍵重點 (條列式)。
    3. 語氣客觀專業。
    
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
    if not GEMINI_API_KEY or not GOOGLE_APP_PASSWORD:
        print("錯誤：找不到環境變數，請確認 GitHub Secrets 設定是否正確。")
        return

    print("正在讀取 RSS...")
    feed = feedparser.parse(RSS_URL)
    
    print("正在登入 Google Keep...")
    keep = gkeepapi.Keep()
    
    # 這裡加入一個嘗試恢復 token 的機制會更穩定，但為了簡單，我們先直接登入
    try:
        success = keep.login(GOOGLE_EMAIL, GOOGLE_APP_PASSWORD)
    except Exception as e:
        print(f"登入發生錯誤: {e}")
        return

    if not success:
        print("Google Keep 登入失敗")
        return

    # 讀取最新的 3 則 (避免超時)
    for entry in feed.entries[:3]:
        title = entry.title
        link = entry.link
        content = entry.summary if 'summary' in entry else entry.title 
        
        print(f"正在處理：{title}")
        
        # 簡單防重複檢查
        existing_notes = keep.find(query=title)
        if any(n for n in existing_notes):
            print(" - 跳過 (已存在)")
            continue

        summary = summarize_text(content)
        
        if summary:
            note_body = f"{summary}\n\n原文連結：{link}"
            note = keep.createNote(title, note_body)
            note.color = gkeepapi.node.ColorValue.TEAL
            note.labels.add('AI News') 
            print(" - 筆記已建立")
            time.sleep(2)
        else:
            print(" - 摘要失敗")

    print("正在同步到 Google Keep...")
    keep.sync()
    print("完成！")

if __name__ == "__main__":

    main()
