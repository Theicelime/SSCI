import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="老龄环境学论文看板", page_icon="📚", layout="wide")

# --- 自定义样式 (让它更“好看”) ---
st.markdown("""
    <style>
    .paper-card {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        height: 350px;
        display: flex;
        flex-direction: column;
        transition: transform 0.2s;
    }
    .paper-card:hover {
        transform: translateY(-5px);
        border-color: #4A90E2;
    }
    .journal-tag {
        font-size: 0.7rem;
        text-transform: uppercase;
        color: #4A90E2;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1A1A1A;
        margin-bottom: 10px;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .abstract {
        font-size: 0.85rem;
        color: #666;
        line-height: 1.4;
        flex-grow: 1;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
    }
    .footer {
        margin-top: 15px;
        font-size: 0.8rem;
        color: #999;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    a { text-decoration: none; color: inherit; }
    </style>
    """, unsafe_allow_html=True)

# --- 目标期刊数据 ---
JOURNALS = {
    "The Gerontologist": "S4306399625",
    "Journal of Environmental Psychology": "S156885347",
    "Health & Place": "S108842106",
    "Landscape and Urban Planning": "S162319083",
    "Age and Ageing": "S169624507"
}

# --- 数据获取函数 ---
@st.cache_data(ttl=3600)  # 缓存1小时
def fetch_papers(selected_journals):
    ids = "|".join([JOURNALS[name] for name in selected_journals])
    url = f"https://api.openalex.org/works?filter=primary_location.schema_id:{ids}&sort=publication_date:desc&per_page=20"
    
    try:
        res = requests.get(url)
        data = res.json()
        return data.get('results', [])
    except:
        return []

# --- 侧边栏 ---
st.sidebar.title("🔍 控制面板")
st.sidebar.info("自动追踪老龄环境学前沿论文")
selected = st.sidebar.multiselect("订阅期刊", list(JOURNALS.keys()), default=list(JOURNALS.keys()))
search_query = st.sidebar.text_input("关键词过滤", "")

# --- 主界面 ---
st.title("📑 环境老年学·科研卡片")
st.caption(f"更新于: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if not selected:
    st.warning("请在侧边栏至少选择一个期刊。")
else:
    papers = fetch_papers(selected)
    
    # 过滤关键词
    if search_query:
        papers = [p for p in papers if search_query.lower() in p['display_name'].lower()]

    # 布局：一行4列
    cols = st.columns(4)
    
    for idx, paper in enumerate(papers):
        col = cols[idx % 4]
        
        # 提取信息
        title = paper.get('display_name', 'No Title')
        journal = paper.get('host_venue', {}).get('display_name', 'Unknown Journal')
        date = paper.get('publication_date', '')
        doi = paper.get('doi', '#')
        author = paper.get('authorships', [{}])[0].get('author', {}).get('display_name', 'Unknown')
        
        # 渲染卡片
        with col:
            st.markdown(f"""
                <a href="{doi}" target="_blank">
                    <div class="paper-card">
                        <div class="journal-tag">{journal}</div>
                        <div class="title">{title}</div>
                        <div class="abstract">作者: {author} 等人。点击跳转DOI查看完整摘要和全文内容。</div>
                        <div class="footer">
                            <span>📅 {date}</span>
                            <span style="color: #4A90E2; font-weight:bold;">阅读原文 →</span>
                        </div>
                    </div>
                </a>
            """, unsafe_allow_html=True)

if not papers:
    st.write("未能抓取到相关论文，请尝试调整筛选条件。")
