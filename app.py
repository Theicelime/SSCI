import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# --- 1. 高级 UI 样式定义 (真正的应用感) ---
def apply_premium_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Noto+Sans+SC:wght@300;500;900&display=swap');
    
    :root {
        --primary: #2563eb;
        --bg-main: #f8fafc;
        --card-bg: rgba(255, 255, 255, 0.8);
    }

    .stApp { background-color: var(--bg-main); }
    
    /* 极致卡片设计 */
    .paper-card {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .paper-card:hover {
        transform: translateY(-5px) scale(1.01);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border-color: var(--primary);
    }

    /* 刊名与标签 */
    .journal-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 700;
        background: #dbeafe;
        color: #1e40af;
        padding: 4px 10px;
        border-radius: 6px;
        margin-bottom: 12px;
        display: inline-block;
    }

    .paper-title {
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 1.2rem;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.4;
        margin-bottom: 12px;
    }

    .ai-summary-box {
        background: #f1f5f9;
        border-left: 4px solid var(--primary);
        padding: 12px;
        border-radius: 8px;
        font-size: 13px;
        color: #475569;
        margin: 15px 0;
    }

    /* 状态栏 */
    .meta-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 20px;
        font-size: 12px;
        color: #94a3b8;
    }
    
    /* 隐藏 Streamlit 原生元素 */
    div[data-testid="stToolbar"] { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 深度数据引擎 ---
@st.cache_data(ttl=3600)
def get_intel_data(keywords, journal_ids, limit=25):
    """
    采用双重检索：关键词精确匹配 + 核心期刊追踪
    """
    # 关键词部分
    query = f"(abstract.search:\"{keywords}\" OR title.search:\"{keywords}\")"
    
    # 期刊过滤部分
    if journal_ids:
        journal_filter = "primary_location.schema_id:" + "|".join(journal_ids)
        full_filter = f"{query},{journal_filter}"
    else:
        full_filter = query

    url = f"https://api.openalex.org/works?filter={full_filter}&sort=publication_date:desc&per_page={limit}"
    
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json().get('results', [])
        return []
    except Exception as e:
        return []

def decode_abstract(inverted):
    if not inverted: return "Abstract not provided by publisher."
    idx = []
    for word, positions in inverted.items():
        for p in positions: idx.append((p, word))
    idx.sort()
    full_text = " ".join([x[1] for x in idx])
    return full_text[:400] + "..."

# --- 3. AI 智能总结逻辑 ---
def get_ai_insight(text, api_key):
    """
    调用 AI 接口进行论文洞察
    """
    if not api_key: return "请在侧边栏配置 API Key 以开启 AI 洞察。"
    
    # 这里以 DeepSeek 为例，您可以根据需要切换
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位老龄环境学专家，请用中文一句话总结以下摘要的核心研究贡献："},
            {"role": "user", "content": text}
        ]
    }
    try:
        # 模拟调用或实际调用 (此处为占位，实际使用时取消注释)
        # res = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers)
        # return res.json()['choices'][0]['message']['content']
        return "✨ 模拟洞察：该研究通过实证分析探讨了城市绿地对失智老人生活质量的正向影响，提出了环境弹性补偿模型。"
    except:
        return "AI 服务暂时忙碌..."

# --- 4. 主程序界面 ---
def main():
    apply_premium_style()
    
    # --- Sidebar: 专家控制面板 ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=60)
        st.title("智库控制台")
        st.markdown("---")
        
        journals = {
            "The Gerontologist": "S4306399625",
            "Health & Place": "S108842106",
            "Landscape & Urban Planning": "S162319083",
            "Age and Ageing": "S169624507",
            "J. of Env Psychology": "S156885347"
        }
        
        st.subheader("📡 频道订阅")
        selected_journals = st.multiselect("核心刊物", list(journals.keys()), default=list(journals.keys())[:3])
        ids = [journals[k] for k in selected_journals]
        
        st.subheader("🔍 精准画像")
        keywords = st.text_input("学术关键词", value="environmental gerontology")
        
        st.subheader("🤖 AI 神经元")
        ai_on = st.toggle("开启 AI 深度解析", value=True)
        key = st.sidebar.text_input("API Key", type="password", help="支持 DeepSeek/OpenAI 格式")
        
        st.markdown("---")
        st.caption("Gerontology Intel v3.0 Pro\nPowered by OpenAlex & DeepSeek")

    # --- Main Canvas ---
    st.markdown(f"### 🌐 全球老龄环境研究·实时情报")
    st.caption(f"检索到来自 {len(selected_journals)} 个顶刊的最新数据 | 当前时间: {datetime.now().strftime('%H:%M:%S')}")

    # 数据加载状态
    with st.spinner("正在穿透学术壁垒..."):
        papers = get_intel_data(keywords, ids)

    if not papers:
        st.error("❌ 未能在当前频道下发现论文。尝试扩大搜索关键词或增加订阅期刊。")
        return

    # 内容展示 (Pinterest 风格栅格)
    col1, col2 = st.columns(2, gap="large")
    
    for i, paper in enumerate(papers):
        target_col = col1 if i % 2 == 0 else col2
        
        title = paper.get('display_name', 'Untitled')
        journal = paper.get('host_venue', {}).get('display_name', 'Unknown Source')
        date = paper.get('publication_date', 'N/A')
        citations = paper.get('cited_by_count', 0)
        abstract = decode_abstract(paper.get('abstract_inverted_index'))
        doi = paper.get('doi', '#')

        with target_col:
            st.markdown(f"""
            <div class="paper-card">
                <div class="journal-tag">{journal}</div>
                <div class="paper-title">{title}</div>
                <div class="abstract-preview">{abstract[:180]}...</div>
                <div class="meta-footer">
                    <span>📅 {date}</span>
                    <span>🔥 引用: {citations}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 卡片交互区
            exp = st.expander("展开深度情报")
            with exp:
                if ai_on:
                    st.markdown(f"**🤖 AI 核心洞察:**")
                    st.info(get_ai_insight(abstract, key))
                
                st.markdown(f"**摘要全文:**\n\n{abstract}")
                st.link_button("🚀 查看原刊论文", doi, use_container_width=True)
            
            st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
