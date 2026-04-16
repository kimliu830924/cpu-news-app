import os
import feedparser
import time
import smtplib
import google.generativeai as genai
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# --- 1. 從 GitHub Secrets 讀取設定 ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
EMAIL_SENDER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASS")
EMAIL_RECEIVER = os.environ.get("EMAIL_USER") # 預設寄給自己

# --- 2. 抓取過去 24 小時新聞 ---
def get_news(query):
    # 抓取 24 小時內的資訊
    limit = datetime.utcnow() - timedelta(hours=24)
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    
    results = []
    for e in feed.entries:
        try:
            pt = datetime.fromtimestamp(time.mktime(e.published_parsed))
            if pt >= limit:
                results.append({"title": e.title, "link": e.link})
        except:
            continue
    return results[:15] # 限制前 15 則給 AI 分析

# --- 3. 呼叫 AI 進行產業總結 ---
def ai_summarize(news_list):
    if not GEMINI_KEY or not news_list:
        return "今日暫無重大產業更新。"
    
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        text = "\n".join([f"- {n['title']}" for n in news_list])
        prompt = f"""
        你是一位專業的半導體產業分析師。請分析以下新聞標題，挑選出 3-5 個最值得關注的動態（如 Intel, TSMC, NVIDIA 或 AI 晶片相關）。
        請用繁體中文整理，每個重點包含：
        1. 標題摘要
        2. 為什麼這很重要（一句話分析）
        
        新聞清單：
        {text}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 總結失敗：{str(e)}"

# --- 4. 發送電子郵件 (修正語法錯誤版) ---
def send_email(content):
    # 先處理換行符號，避開 f-string 內的反斜線限制
    html_body = content.replace('\n', '<br>')
    
    # 建立郵件內文
    html_template = f"""
    <html>
    <body style="font-family: sans-serif; line-height: 1.6;">
        <h2 style="color: #2c3e50;">📊 每日半導體 & CPU 產業戰報</h2>
        <p style="background-color: #f8f9fa; padding: 15px; border-left: 5px solid #3498db;">
            {html_body}
        </p>
        <p style="font-size: 0.8em; color: #7f8c8d;">
            發送時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (自動發送)
        </p>
    </body>
    </html>
    """
    
    msg = MIMEText(html_template, 'html', 'utf-8')
    msg['Subject'] = f"📊 AI 產業戰報 - {datetime.now().strftime('%Y/%m/%d')}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("✅ Email Sent Successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

# --- 5. 執行主程式 ---
if __name__ == "__main__":
    # 你可以在這裡更改你每天想收到的關鍵字
    target_query = "TSMC Intel AMD NVIDIA CPU 'Advanced Packaging' CoWoS"
    
    print(f"正在掃描 {target_query} 的最新動態...")
    raw_news = get_news(target_query)
    
    print("正在請求 AI 進行總結...")
    summary = ai_summarize(raw_news)
    
    print("正在發送每日郵件...")
    send_email(summary)
