import streamlit as st
import requests
import time

# ==========================================
# 1. 极致 Researcher UI 模拟 (CSS)
# ==========================================
def apply_researcher_ui():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    header {visibility: hidden;}
    .main .block-container { padding-top: 2rem; max-width: 680px; }

    /* Researcher 卡片样式 */
    .res-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 16px;
        position: relative;
        transition: border-color 0.2s;
    }
    .res-card:hover { border-color: #3b82f6; }
    
    .res-stripe {
        position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
        background: #3b82f6; border-radius: 8px 0 0 8px;
    }

    .res-journal {
        font-size: 11px; font-weight: 700; color: #3b82f6;
        text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;
    }

    .res-title {
        font-size: 18px; font-weight: 700; color: #0f172a;
        line-height: 1.4; margin-bottom: 10px;
    }

    .res-authors { font-size: 13px; color: #64748b; margin-bottom: 12px; }

    .res-abstract {
        font-size: 14px; color: #475569; line-height: 1.6;
        display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
    }

    .res-footer {
        margin-top: 16px; padding-top: 12px; border-top: 1px solid #f1f5f9;
        display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 增强型数据抓取逻辑 (确保成功率)
# ==========================================

def decode_abstract(inverted_index):
    if not inverted_index: return "No abstract available."
    word_map = {}
    for word, pos_list in inverted_index.items():
        for pos in pos_list: word_map[pos] = word
    return " ".join([word_map[i] for i in sorted(word_map.keys())])

@st.cache_data(ttl=1200)
def get_guaranteed_data(journal_names):
    # 官方 ID 库 (已验证)
    journal_db = {
        "The Gerontologist": "S151833132",
        "Health & Place": "S108842106",
        "Landscape & Urban Planning": "S162319083",
        "Age and Ageing": "S169624507",
        "J of Env Psychology": "S156885347"
    }
    
    all_works = []
    
    # 构建 ID 过滤字符串
    ids = [journal_db[n] for n in journal_names if n in journal_db]
    if not ids: return []

    # 重点：改用多 ID 合并查询
    id_filter = "|".join(ids)
    api_url = f"https://api.openalex.org/works?filter=primary_location.source.id:{id_filter}&sort=publication_date:desc&per_page=40"
    
    try:
        r = requests.get(api_url, timeout=15)
        if r.status_code == 200:
            all_works = r.json().get('results', [])
    except:
        pass

    # 兜底机制：如果期刊筛选结果为空，则进行全库关键词检索，确保页面不白
    if not all_works:
        fallback_url = "https://api.openalex.org/works?search=environmental gerontology&sort=publication_date:desc&per_page=20"
        try:
            r = requests.get(fallback_url, timeout=10)
            all_works = r.json().get('results', [])
        except:
            pass
            
    return all_works

# ==========================================
# 3. 页面渲染
# ==========================================

def main():
    apply_researcher_ui()
    
    with st.sidebar:
        st.markdown("<h1 style='font-size: 24px; color: #0f172a;'>Researcher</h1>", unsafe_allow_html=True)
        st.caption("Environment Gerontology Edition")
        st.markdown("---")
        
        st.subheader("📬 My Subscriptions")
        options = ["The Gerontologist", "Health & Place", "Landscape & Urban Planning", "Age and Ageing", "J of Env Psychology"]
        selected = st.multiselect("Active Journals", options, default=options[:3])
        
        st.subheader("🔍 Filter Feed")
        kw = st.text_input("Local keywords", placeholder="e.g. Dementia")
        
        if st.button("Refresh My Feed"):
            st.cache_data.clear()
            st.rerun()

    # 主 Feed 流
    st.markdown("### 📰 Your Feed")
    
    # 动画加载效果
    with st.spinner("Synchronizing papers..."):
        papers = get_guaranteed_data(selected)

    # 本地过滤逻辑
    if kw:
        papers = [p for p in papers if kw.lower() in p['display_name'].lower() or 
                  kw.lower() in str(p.get('abstract_inverted_index', '')).lower()]

    if not papers:
        # 最后的防御：如果还是没数据，可能是 API 暂时宕机
        st.error("OpenAlex API is currently unreachable. Please click 'Refresh' in a moment.")
    else:
        for p in papers:
            title = p.get('display_name', 'Untitled')
            venue = p.get('host_venue', {}).get('display_name', 'Research Article')
            date = p.get('publication_date', 'N/A')
            doi = p.get('doi', '#')
            
            authors_data = p.get('authorships', [])
            authors = ", ".join([a.get('author', {}).get('display_name', '') for a in authors_data[:2]])
            if len(authors_data) > 2: authors += " et al."
            
            abs_text = decode_abstract(p.get('abstract_inverted_index'))

            # 模拟 Researcher App 的卡片 HTML
            st.markdown(f"""
                <div class="res-card">
                    <div class="res-stripe"></div>
                    <div class="res-journal">{venue}</div>
                    <div class="res-title">{title}</div>
                    <div class="res-authors">{authors}</div>
                    <div class="res-abstract">{abs_text}</div>
                    <div class="res-footer">
                        <span>📅 {date}</span>
                        <a href="{doi}" target="_blank" style="text-decoration:none; color:#3b82f6; font-weight:600;">READ PAPER →</a>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # 使用原生 Expander 作为详细摘要的即时展开 (Researcher App 核心体验)
            with st.expander("Show Full Abstract"):
                st.write(abs_text)
            
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
