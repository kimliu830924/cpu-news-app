import os
import feedparser
import time
import smtplib
import google.generativeai as genai
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# --- 配置區 (從環境變數讀取) ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
EMAIL_SENDER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASS")
EMAIL_RECEIVER = os.environ.get("EMAIL_USER") # 寄給自己

def get_news(query):
    limit = datetime.utcnow() - timedelta(hours=24) # 每天抓過去 24 小時
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    return [{"title": e.title, "link": e.link} for e in feed.entries][:10]

def ai_summarize(news_list):
    if not GEMINI_KEY or not news_list: return "無重大更新。"
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    text = "\n".join([f"- {n['title']}" for n in news_list])
    prompt = f"你是產業分析師。請從以下新聞中挑選 3 個最值得關注的 CPU/半導體動態，並用繁體中文做簡單總結：\n{text}"
    
    try:
        return model.generate_content(prompt).text
    except:
        return "AI 總結失敗，請查看原始連結。"

def send_email(content):
    msg = MIMEText(f"<h2>2026 半導體產業每日情報</h2><p>{content.replace('\n', '<br>')}</p>", 'html')
    msg['Subject'] = f"📊 AI 產業戰報 - {datetime.now().strftime('%Y/%m/%d')}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    # 這裡可以自定義你最關心的關鍵字
    raw_news = get_news("TSMC Intel AMD NVIDIA CPU 'Advanced Packaging'")
    summary = ai_summarize(raw_news)
    send_email(summary)
    print("Email Sent Successfully!")
