import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. Researcher App 视觉风格定义 ---
def inject_researcher_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* 基础背景与字体 */
    .stApp { background-color: #f9fafb; font-family: 'Inter', sans-serif; }
    
    /* 隐藏顶部白条和菜单 */
    header {visibility: hidden;}
    .main .block-container { padding-top: 2rem; max-width: 800px; }

    /* Researcher 风格卡片 */
    .feed-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .feed-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }

    /* 期刊标题标签 */
    .journal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .journal-name {
        font-size: 12px;
        font-weight: 700;
        color: #3b82f6;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .pub-date {
        font-size: 12px;
        color: #9ca3af;
    }

    /* 论文标题 */
    .paper-title {
        font-size: 18px;
        font-weight: 700;
        color: #111827;
        line-height: 1.4;
        margin-bottom: 12px;
    }

    /* 作者信息 */
    .author-line {
        font-size: 14px;
        color: #4b5563;
        margin-bottom: 16px;
    }

    /* 摘要预览 */
    .abstract-preview {
        font-size: 14px;
        color: #6b7280;
        line-height: 1.6;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    /* 操作按钮 */
    .action-bar {
        display: flex;
        gap: 20px;
        margin-top: 20px;
        padding-top: 16px;
        border-top: 1px solid #f3f4f6;
    }
    
    .action-link {
        color: #3b82f6;
        font-size: 13px;
        font-weight: 600;
        text-decoration: none;
    }

    /* 侧边栏美化 */
    .css-1d391kg { background-color: white; border-right: 1px solid #e5e7eb; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 增强型数据抓取逻辑 ---
def decode_inverted_index(index):
    if not index: return "No abstract available."
    word_index = []
    for word, positions in index.items():
        for pos in positions: word_index.append((pos, word))
    word_index.sort()
    return " ".join([w for p, w in word_index])

@st.cache_data(ttl=1800)
def fetch_researcher_feed(journal_ids):
    """
    专门针对订阅流的逻辑：获取这些期刊最近的所有论文
    """
    if not journal_ids: return []
    
    # 构建过滤字符串：只筛选期刊ID
    journal_filter = "|".join(journal_ids)
    url = f"https://api.openalex.org/works?filter=primary_location.schema_id:{journal_filter}&sort=publication_date:desc&per_page=30"
    
    try:
        r = requests.get(url, timeout=15)
        return r.json().get('results', [])
    except:
        return []

# --- 3. 页面构建 ---
def main():
    inject_researcher_theme()
    
    # --- Sidebar (控制面板) ---
    with st.sidebar:
        st.markdown("<h1 style='font-size: 24px;'>Researcher</h1>", unsafe_allow_html=True)
        st.caption("Environment Gerontology Edition")
        st.markdown("---")
        
        journals_db = {
            "The Gerontologist": "S4306399625",
            "Journal of Env Psychology": "S156885347",
            "Health & Place": "S108842106",
            "Landscape & Urban Planning": "S162319083",
            "Ageing & Society": "S4210170428"
        }
        
        st.markdown("### 📢 My Subscriptions")
        selected_names = st.multiselect("Select Journals", 
                                        options=list(journals_db.keys()), 
                                        default=list(journals_db.keys())[:3])
        
        st.markdown("### 🔍 Filter Feed")
        keyword = st.text_input("Keywords (e.g. Dementia)", "")
        
        st.markdown("---")
        if st.button("Clear Cache & Refresh"):
            st.cache_data.clear()

    # --- Main Feed ---
    st.markdown(f"### 📬 Your Feed")
    st.caption(f"Showing latest research from {len(selected_names)} sources")

    journal_ids = [journals_db[name] for name in selected_names]
    
    with st.spinner("Fetching latest papers..."):
        all_papers = fetch_researcher_feed(journal_ids)
    
    # 本地关键词过滤 (比API过滤更可靠，不会导致“空结果”)
    if keyword:
        display_papers = [p for p in all_papers if keyword.lower() in p['display_name'].lower() or 
                          keyword.lower() in str(p.get('abstract_inverted_index', '')).lower()]
    else:
        display_papers = all_papers

    if not display_papers:
        st.markdown("""
            <div style='text-align: center; padding: 50px; color: #9ca3af;'>
                <p>No papers found in your feed.</p>
                <p style='font-size: 13px;'>Try following more journals or clearing filters.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        for paper in display_papers:
            # 数据解析
            title = paper.get('display_name', 'Untitled')
            journal = paper.get('host_venue', {}).get('display_name', 'Unknown')
            date = paper.get('publication_date', 'N/A')
            authors = ", ".join([a.get('author', {}).get('display_name', '') for a in paper.get('authorships', [])[:3]])
            doi = paper.get('doi', '#')
            abstract = decode_inverted_index(paper.get('abstract_inverted_index'))
            
            # 渲染卡片 (Researcher 风格)
            st.markdown(f"""
                <div class="feed-card">
                    <div class="journal-header">
                        <span class="journal-name">{journal}</span>
                        <span class="pub-date">{date}</span>
                    </div>
                    <div class="paper-title">{title}</div>
                    <div class="author-line">{authors} et al.</div>
                    <div class="abstract-preview">{abstract}</div>
                    <div class="action-bar">
                        <a href="{doi}" target="_blank" class="action-link">READ PAPER</a>
                        <span style="color:#e5e7eb">|</span>
                        <span class="action-link" style="color:#9ca3af; cursor:not-allowed;">SAVE TO LIBRARY</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # 使用 Streamlit 原生组件辅助摘要查看 (因为 HTML 里的点击事件较难处理)
            with st.expander("Full Abstract"):
                st.write(abstract)

if __name__ == "__main__":
    main()
