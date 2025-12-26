import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# ==========================================
# 1. 页面配置与极简美学 CSS
# ==========================================
st.set_page_config(page_title="Gerontology Intelligence", page_icon="🌐", layout="wide")

def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* 背景美化 */
    .main { background: #fdfdfd; }
    
    /* 智能卡片设计 */
    .paper-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        border: 1px solid #f0f0f0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        margin-bottom: 25px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    
    .paper-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.08);
        border-color: #3b82f6;
    }

    .journal-badge {
        display: inline-block;
        padding: 4px 12px;
        background: #eff6ff;
        color: #1d4ed8;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-bottom: 12px;
    }

    .paper-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #1e293b;
        line-height: 1.3;
        margin-bottom: 15px;
    }

    .meta-info {
        display: flex;
        align-items: center;
        gap: 15px;
        color: #64748b;
        font-size: 0.85rem;
        margin-top: auto;
        padding-top: 15px;
        border-top: 1px solid #f8fafc;
    }

    .stat-item { display: flex; align-items: center; gap: 4px; }
    
    /* 按钮样式优化 */
    .stButton>button {
        border-radius: 10px;
        background: #1e293b;
        color: white;
        border: none;
        width: 100%;
    }
    
    /* 隐藏默认组件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 核心逻辑：数据抓取与解析
# ==========================================

def decode_abstract(inverted_index):
    """解码 OpenAlex 特有的倒排索引摘要"""
    if not inverted_index: return "暂无摘要预览"
    word_index = []
    for word, pos_list in inverted_index.items():
        for pos in pos_list:
            word_index.append((pos, word))
    word_index.sort()
    abstract = " ".join([word for pos, word in word_index])
    return abstract[:300] + "..." if len(abstract) > 300 else abstract

@st.cache_data(ttl=3600, show_spinner=False)
def get_latest_papers(journal_ids, min_citations, days_back):
    # 构建 API URL
    ids_str = "|".join(journal_ids)
    url = f"https://api.openalex.org/works?filter=primary_location.schema_id:{ids_str},cited_by_count:>{min_citations}&sort=publication_date:desc&per_page=40"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get('results', [])
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return []

# ==========================================
# 3. 界面布局
# ==========================================
local_css()

# --- 侧边栏：智能化控制 ---
with st.sidebar:
    st.markdown("## ⚙️ 智能过滤")
    
    journals_map = {
        "The Gerontologist": "S4306399625",
        "Journal of Env Psychology": "S156885347",
        "Health & Place": "S108842106",
        "Landscape & Urban Planning": "S162319083",
        "Age and Ageing": "S169624507",
        "J of Aging and Env": "S4210214227"
    }
    
    selected_names = st.multiselect("追踪期刊", list(journals_map.keys()), default=list(journals_map.keys())[:3])
    selected_ids = [journals_map[name] for name in selected_names]
    
    min_cite = st.slider("最低引用量", 0, 100, 0)
    search_keyword = st.text_input("标题关键词搜索", "")
    
    st.divider()
    st.markdown("### 🤖 AI 设置")
    ai_enabled = st.toggle("开启 AI 核心观点提取", value=False)
    if ai_enabled:
        api_key = st.text_input("DeepSeek/OpenAI Key", type="password")

# --- 主内容区 ---
col_head_1, col_head_2 = st.columns([2, 1])
with col_head_1:
    st.markdown("# 🧠 环境老年学·前沿情报站")
    st.markdown(f"**{datetime.now().strftime('%Y年%m月%d日')}** · 聚合全球顶刊最新研究")

with col_head_2:
    if st.button("🔄 强制刷新数据库"):
        st.cache_data.clear()

if not selected_ids:
    st.warning("请在侧边栏至少订阅一个期刊以获取情报。")
else:
    with st.spinner("正在链接全球学术数据库..."):
        raw_papers = get_latest_papers(selected_ids, min_cite, 90)
    
    # 关键词过滤
    if search_keyword:
        papers = [p for p in raw_papers if search_keyword.lower() in p['display_name'].lower()]
    else:
        papers = raw_papers

    if not papers:
        st.info("当前筛选条件下未发现新论文。")
    else:
        # 网格布局
        n_cols = 3
        rows = [papers[i:i + n_cols] for i in range(0, len(papers), n_cols)]
        
        for row in rows:
            cols = st.columns(n_cols)
            for i, paper in enumerate(row):
                with cols[i]:
                    title = paper.get('display_name', 'Untitled')
                    venue = paper.get('host_venue', {}).get('display_name', 'Unknown Venue')
                    date = paper.get('publication_date', 'Unknown Date')
                    cites = paper.get('cited_by_count', 0)
                    doi = paper.get('doi', '#')
                    abstract = decode_abstract(paper.get('abstract_inverted_index'))
                    
                    # 渲染卡片
                    st.markdown(f"""
                    <div class="paper-card">
                        <div>
                            <div class="journal-badge">{venue}</div>
                            <div class="paper-title">{title}</div>
                            <div class="abstract">{abstract}</div>
                        </div>
                        <div class="meta-info">
                            <div class="stat-item">📅 {date}</div>
                            <div class="stat-item">🔥 引用: {cites}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 功能按钮组
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        st.link_button("📄 读原文", doi)
                    with btn_col2:
                        if st.button("✨ AI 总结", key=f"ai_{paper['id']}"):
                            if not ai_enabled:
                                st.error("请先在左侧开启AI功能")
                            else:
                                st.toast("AI 正在深度阅读...")
                                # 这里预留 AI 调用逻辑
                                st.info("AI 总结功能已就绪，接入 API Key 后即可展示研究贡献、方法论和结论。")

# --- 页脚 ---
st.markdown("---")
st.caption("数据来源: OpenAlex API | 设计: Environmental Gerontology Dashboard v2.0")
