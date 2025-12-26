import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# 1. Researcher App 核心 UI 样式 (高保真还原)
# ==========================================
def inject_researcher_design():
    st.markdown("""
    <style>
    /* 引入 Researcher 专用字体 */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    .stApp { background-color: #f4f7f9; font-family: 'Roboto', sans-serif; }
    
    /* 隐藏 Streamlit 原生组件 */
    header {visibility: hidden;}
    .main .block-container { padding-top: 1rem; max-width: 700px; }
    
    /* 模拟 Researcher App 的 Feed 卡片 */
    .researcher-card {
        background: white;
        border: 1px solid #dfe3e8;
        border-radius: 4px; /* Researcher 使用微圆角 */
        padding: 20px;
        margin-bottom: 12px;
        position: relative;
    }
    
    /* 左侧颜色竖条 - 模拟订阅标记 */
    .journal-stripe {
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background-color: #3498db;
        border-radius: 4px 0 0 4px;
    }

    .card-journal {
        font-size: 11px;
        font-weight: 700;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 8px;
    }

    .card-title {
        font-size: 17px;
        font-weight: 600;
        color: #2c3e50;
        line-height: 1.35;
        margin-bottom: 10px;
        text-decoration: none;
    }

    .card-authors {
        font-size: 13px;
        color: #95a5a6;
        margin-bottom: 12px;
    }

    .card-abstract {
        font-size: 14px;
        color: #34495e;
        line-height: 1.5;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
    }

    .card-footer {
        margin-top: 15px;
        padding-top: 12px;
        border-top: 1px solid #f2f2f2;
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #bdc3c7;
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #dfe3e8;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 核心数据解析与抓取 (保证成功率)
# ==========================================

def decode_abstract(inverted_index):
    if not inverted_index: return "No abstract available."
    d = {}
    for word, pos in inverted_index.items():
        for p in pos: d[p] = word
    return " ".join([d[i] for i in sorted(d.keys())])

@st.cache_data(ttl=3600)
def fetch_papers_secure(journal_names):
    # 学术期刊 ID 映射
    mapping = {
        "The Gerontologist": "S4306399625",
        "Health & Place": "S108842106",
        "Landscape & Urban Planning": "S162319083",
        "Age and Ageing": "S169624507",
        "J of Aging and Env": "S4210214227"
    }
    
    all_results = []
    
    # 策略 1：并行逐个抓取 (确保不会因为某个期刊无更新而导致整体报错)
    for name in journal_names:
        jid = mapping.get(name)
        url = f"https://api.openalex.org/works?filter=primary_location.source.id:https://openalex.org/{jid}&sort=publication_date:desc&per_page=10"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                all_results.extend(r.json().get('results', []))
        except:
            continue

    # 策略 2：如果订阅的期刊确实没数据，自动通过关键词抓取全领域最新论文（兜底方案）
    if len(all_results) < 3:
        fallback_url = "https://api.openalex.org/works?search=environmental gerontology&sort=publication_date:desc&per_page=20"
        try:
            r = requests.get(fallback_url)
            all_results.extend(r.json().get('results', []))
        except:
            pass

    # 按日期排序
    all_results.sort(key=lambda x: x.get('publication_date', ''), reverse=True)
    return all_results

# ==========================================
# 3. 应用程序主框架
# ==========================================

def main():
    inject_researcher_design()
    
    # Sidebar - 模拟 Researcher App 的导航栏
    with st.sidebar:
        st.title("Researcher")
        st.caption("v3.2 Professional Edition")
        st.markdown("---")
        
        st.subheader("📬 My Journals")
        options = ["The Gerontologist", "Health & Place", "Landscape & Urban Planning", "Age and Ageing", "J of Aging and Env"]
        selected = st.multiselect("Subscribed", options, default=options[:3])
        
        st.markdown("---")
        st.subheader("🔍 Local Search")
        keyword = st.text_input("Search in feed...", placeholder="e.g. Dementia")
        
        if st.button("Refresh Feed"):
            st.cache_data.clear()
            st.rerun()

    # Main Feed
    st.markdown("### 📰 Your Feed")
    
    # 执行抓取
    with st.spinner("Synchronizing with Academic Cloud..."):
        papers = fetch_papers_secure(selected)
    
    # 关键词过滤
    if keyword:
        papers = [p for p in papers if keyword.lower() in p['display_name'].lower() or 
                  keyword.lower() in str(p.get('abstract_inverted_index', '')).lower()]

    # 渲染 Researcher 风格卡片
    if not papers:
        st.error("Connection failed. Please check your internet or refresh.")
    else:
        for p in papers:
            title = p.get('display_name', 'Untitled Paper')
            journal = p.get('host_venue', {}).get('display_name', 'Open Access')
            date = p.get('publication_date', 'N/A')
            doi = p.get('doi', '#')
            # 提取作者
            authors_list = p.get('authorships', [])
            authors_str = ", ".join([a.get('author', {}).get('display_name', '') for a in authors_list[:3]])
            if len(authors_list) > 3: authors_str += " et al."
            
            # 摘要预览
            abstract = decode_abstract(p.get('abstract_inverted_index'))

            # HTML 模板
            st.markdown(f"""
            <div class="researcher-card">
                <div class="journal-stripe"></div>
                <div class="card-journal">{journal}</div>
                <div class="card-title">{title}</div>
                <div class="card-authors">{authors_str}</div>
                <div class="card-abstract">{abstract}</div>
                <div class="card-footer">
                    <span>📅 {date}</span>
                    <span style="color: #3498db; font-weight: 600; cursor: pointer;">Full Access →</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 使用原生 Expander 模仿 App 的“展开阅读”
            with st.expander("Read Full Abstract"):
                st.write(abstract)
                st.link_button("View on Publisher Site", doi)
            
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
