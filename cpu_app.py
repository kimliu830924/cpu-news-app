import streamlit as st
import feedparser
import time
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. 介面與風格設定 ---
st.set_page_config(page_title="半導體精準情報站", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #1a1a1a; color: #e0e0e0; }
    .stExpander { border: 1px solid #444 !important; background-color: #262626 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 半導體 & CPU 產業鏈・AI 監控")

# --- 2. 側邊欄設定 (控制台) ---
with st.sidebar:
    st.header("⚙️ 設定中心")
    
    # 這裡會優先檢查你剛才在 Secrets 填的金鑰
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ 已從系統讀取 API Key")
    else:
        api_key = st.text_input("手動輸入 Gemini API Key", type="password")
    
    hours_limit = st.slider("搜尋過去幾小時？", 1, 48, 12)
    
    st.subheader("🔍 產業鏈關鍵字")
    default_config = (
        "🏗️ 設計上游|'CPU architecture' OR 'ARM architecture' OR 'RISC-V' OR 'EDA tool'\n"
        "🏭 代工中游|'TSMC' OR 'Intel Foundry' OR 'Samsung 2nm' OR 'High-NA EUV'\n"
        "📦 封裝中游|'CoWoS' OR 'Advanced Packaging' OR 'Glass Substrate' OR 'Chiplet'\n"
        "❄️ 散熱下游|'Liquid cooling' OR 'Immersion cooling' OR 'Vapor Chamber' OR 'Auras'\n"
        "🚀 品牌終端|'Intel Ultra' OR 'AMD Zen6' OR 'NVIDIA Blackwell' OR 'Snapdragon X'"
    )
    config_input = st.text_area("自定義清單 (類別|關鍵字)", value=default_config, height=250)
    
    # 統一按鈕名稱為 run_btn
    run_btn = st.button("🚀 START SCAN")

# --- 3. 核心功能函數 ---
def ai_filter(news_list, key):
    if not key: return news_list
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        titles = "\n".join([f"{i}. {n['title']}" for i, n in enumerate(news_list)])
        prompt = f"分析以下標題，判斷是否與半導體、CPU、或硬體產業鏈直接相關。僅回傳相關標題的數字編號，以半角逗號隔開：\n{titles}"
        response = model.generate_content(prompt)
        relevant_indexes = [int(s.strip()) for s in response.text.split(",") if s.strip().isdigit()]
        return [news_list[i] for i in relevant_indexes if i < len(news_list)]
    except:
        return news_list

def get_data(q_str, h):
    limit = datetime.utcnow() - timedelta(hours=h)
    url = f"https://news.google.com/rss/search?q={q_str.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    res = []
    for e in feed.entries:
        try:
            pt = datetime.fromtimestamp(time.mktime(e.published_parsed))
            if pt >= limit:
                res.append({"time": pt.strftime('%H:%M'), "title": e.title, "link": e.link})
        except: continue
    return res

# --- 4. 顯示結果 (執行邏輯) ---
if run_btn:
    lines = config_input.strip().split('\n')
    for line in lines:
        if "|" in line:
            label, kws = line.split('|')
            st.subheader(label)
            
            data = get_data(kws, hours_limit)
            
            # AI 過濾
            if api_key and data:
                with st.spinner(f"AI 正在精煉 {label}..."):
                    data = ai_filter(data[:15], api_key)
            
            if data:
                cols = st.columns(2)
                for i, n in enumerate(data[:8]):
                    with cols[i % 2]:
                        with st.expander(f"📌 {n['time']} | {n['title'][:50]}..."):
                            st.write(n['title'])
                            st.link_button("閱讀新聞", n['link'])
            else:
                st.caption("目前無相關重要新聞")
            st.divider()
    st.success("精準掃描完成")
else:
    st.info("請點擊左側 START SCAN 開始掃描全球數據。")
