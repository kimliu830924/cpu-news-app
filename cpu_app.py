import streamlit as st
import feedparser
import time
import json
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. 介面設定 ---
st.set_page_config(page_title="半導體精準情報站", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #1a1a1a; color: #e0e0e0; }
    .stExpander { border: 1px solid #444 !important; background-color: #262626 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 半導體 & CPU 產業鏈・AI 精準監控")

# --- 2. 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 設定中心")
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    
    hours_limit = st.slider("搜尋過去幾小時？", 1, 48, 12)
    
    st.subheader("🔍 產業鏈關鍵字設定")
    # 這裡我們優化了搜尋關鍵字，加上引號確保精確
    default_config = (
        "🏗️ 設計上游|'CPU architecture' OR 'ARM architecture' OR 'RISC-V' OR 'EDA tool'\n"
        "🏭 代工中游|'TSMC' OR 'Intel Foundry' OR 'Samsung 2nm' OR 'High-NA EUV'\n"
        "📦 封裝中游|'CoWoS' OR 'Advanced Packaging' OR 'Glass Substrate' OR 'Chiplet'\n"
        "❄️ 散熱下游|'Liquid cooling' OR 'Immersion cooling' OR 'Vapor Chamber' OR 'Auras'\n"
        "🚀 品牌終端|'Intel Ultra' OR 'AMD Zen6' OR 'NVIDIA Blackwell' OR 'Snapdragon X'"
    )
    config_input = st.text_area("自定義清單 (類別|關鍵字)", value=default_config, height=250)
    
    use_ai = st.checkbox("開啟 AI 智能去雜訊", value=True if api_key else False)
    run_btn = st.button("START SCAN")

# --- 3. 核心功能 ---

def ai_filter(news_list, api_key):
    """請 AI 批次判斷哪些新聞跟半導體/CPU 產業真的相關"""
    if not api_key: return news_list
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 打包前 15 則新聞
    titles = "\n".join([f"{i}. {n['title']}" for i, n in enumerate(news_list)])
    prompt = f"分析以下標題，判斷是否與半導體、CPU、或相關硬體產業鏈『直接相關』。僅回傳相關標題的數字編號，以逗號隔開：\n{titles}"
    
    try:
        response = model.generate_content(prompt)
        relevant_indexes = [int(s.strip()) for s in response.text.split(",") if s.strip().isdigit()]
        return [news_list[i] for i in relevant_indexes if i < len(news_list)]
    except:
        return news_list # 出錯就回傳原清單

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

# --- 4. 顯示結果 ---
if run_btn:
    lines = config_input.strip().split('\n')
    for line in lines:
        if "|" in line:
            label, kws = line.split('|')
            st.subheader(label)
            
            # 1. 抓取原始數據
            data = get_data(kws, hours_limit)
            
            # 2. AI 智能過濾 (如果開啟)
            if use_ai and api_key and data:
                with st.spinner(f"AI 正在過濾 {label} 的雜訊..."):
                    data = ai_filter(data[:20], api_key) # 限制前 20 則減少 API 負擔
            
            # 3. 呈現結果
            if data:
                # 每排顯示 2 個新聞卡片
                cols = st.columns(2)
                for i, n in enumerate(data[:10]):
                    with cols[i % 2]:
                        with st.expander(f"📌 {n['time']} | {n['title'][:60]}..."):
                            st.write(n['title'])
                            st.link_button("閱讀新聞", n['link'])
            else:
                st.info("目前無相關重要新聞")
            st.divider()
    st.success("精準掃描完成")
