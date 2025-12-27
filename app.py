import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 极致学术级 UI 样式
# ==========================================
def apply_pro_researcher_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #fcfcfd; font-family: 'Inter', sans-serif; }
    header {visibility: hidden;}
    .main .block-container { padding-top: 1rem; max-width: 720px; }

    /* 高级卡片 */
    .res-card {
        background: white;
        border: 1px solid #edf2f7;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: all 0.3s ease;
    }
    .res-card:hover { 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); 
        border-color: #3182ce;
    }
    
    /* 侧边期刊识别条 */
    .res-stripe {
        position: absolute; left: 0; top: 0; bottom: 0; width: 5px;
        background: #3182ce; border-radius: 12px 0 0 12px;
    }

    /* 标签系统 */
    .tag-container { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
    .tag {
        font-size: 10px; font-weight: 700; padding: 2px 8px; 
        border-radius: 4px; text-transform: uppercase;
    }
    .tag-journal { background: #ebf8ff; color: #2b6cb0; }
    .tag-topic { background: #f0fff4; color: #276749; }
    .tag-oa { background: #fff5f5; color: #c53030; }

    .res-title {
        font-size: 19px; font-weight: 700; color: #1a202c;
        line-height: 1.4; margin-bottom: 10px; cursor: pointer;
    }
    .res-title:hover { color: #3182ce; }

    .res-authors { font-size: 13px; color: #718096; margin-bottom: 15px; }

    .res-abstract {
        font-size: 14.5px; color: #4a5568; line-height: 1.7;
        margin-bottom: 15px;
    }

    /* 底部操作栏 */
    .res-footer {
        display: flex; justify-content: space-between; align-items: center;
        padding-top: 15px; border-top: 1px solid #f7fafc;
        font-size: 12px; color: #a0aec0;
    }
    
    .action-btn {
        color: #3182ce; font-weight: 600; text-decoration: none;
        padding: 5px 10px; border-radius: 6px; transition: background 0.2s;
    }
    .action-btn:hover { background: #ebf8ff; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 增强型数据处理器
# ==========================================

def get_paper_url(p):
    """【修正：URL错误问题】优先获取标准DOI链接，其次是OA链接"""
    doi = p.get('doi')
    if doi:
        return doi if doi.startswith('http') else f"https://doi.org/{doi}"
    
    # 备选：寻找 Open Access 的直接 PDF 链接
    oa_info = p.get('open_access', {})
    if oa_info.get('is_oa'):
        oa_url = oa_info.get('oa_url')
        if oa_url: return oa_url
        
    # 最后兜底：落地页
    return p.get('primary_location', {}).get('landing_page_url', '#')

def get_topic_tags(title, abstract):
    """【新增：智能语义标签】"""
    text = (title + " " + abstract).lower()
    tags = []
    if "dementia" in text or "alzheimer" in text: tags.append("🧠 失智症")
    if "urban" in text or "city" in text or "built" in text: tags.append("🏙️ 城市规划")
    if "technology" in text or "digital" in text or "smart" in text: tags.append("💻 智能技术")
    if "policy" in text or "government" in text: tags.append("⚖️ 政策研究")
    if "mobility" in text or "walkability" in text: tags.append("🚶 移动性")
    return tags[:2]

def decode_abstract(inverted_index):
    if not inverted_index: return "No abstract text provided for this entry."
    word_map = {}
    for word, pos_list in inverted_index.items():
        for pos in pos_list: word_map[pos] = word
    return " ".join([word_map[i] for i in sorted(word_map.keys())])

@st.cache_data(ttl=1200)
def fetch_guaranteed_data_v4(journal_names):
    journal_db = {
        "The Gerontologist": "S151833132",
        "Health & Place": "S108842106",
        "Landscape & Urban Planning": "S162319083",
        "Age and Ageing": "S169624507",
        "J of Aging and Env": "S4210214227"
    }
    
    selected_ids = [journal_db[n] for n in journal_names if n in journal_db]
    if not selected_ids: return []

    id_filter = "|".join(selected_ids)
    # 增加被引频次排序，获取更高质量的内容
    api_url = f"https://api.openalex.org/works?filter=primary_location.source.id:{id_filter}&sort=publication_date:desc&per_page=50"
    
    try:
        r = requests.get(api_url, timeout=15)
        if r.status_code == 200:
            return r.json().get('results', [])
    except:
        pass
    
    # 万能兜底
    fallback = "https://api.openalex.org/works?search=environmental gerontology&sort=publication_date:desc&per_page=20"
    return requests.get(fallback).json().get('results', [])

# ==========================================
# 3. 应用程序主框架
# ==========================================

def main():
    apply_pro_researcher_theme()
    
    with st.sidebar:
        st.markdown("<h1 style='font-size: 26px; font-weight: 800;'>Researcher <span style='color:#3182ce'>Pro</span></h1>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.subheader("📬 订阅频道")
        options = ["The Gerontologist", "Health & Place", "Landscape & Urban Planning", "Age and Ageing", "J of Aging and Env"]
        selected = st.multiselect("Active Subscriptions", options, default=options[:3])
        
        st.subheader("🔍 流内搜索")
        kw = st.text_input("关键词过滤", placeholder="搜索标题或摘要...")

        st.markdown("---")
        if st.sidebar.button("🚀 强制同步最新数据"):
            st.cache_data.clear()
            st.rerun()
            
        st.caption("Environment Gerontology Edition v4.0")

    # 主 Feed 流界面
    st.markdown("### 📰 我的科研订阅流")
    
    with st.spinner("正在链接全球学术数据库..."):
        all_papers = fetch_guaranteed_data_v4(selected)

    # 过滤
    papers = [p for p in all_papers if kw.lower() in p['display_name'].lower() or kw.lower() in str(p.get('abstract_inverted_index','')).lower()] if kw else all_papers

    if not papers:
        st.info("当前筛选条件下暂无新文献。")
    else:
        for p in papers:
            # 数据处理
            title = p.get('display_name', 'Untitled Article')
            venue = p.get('host_venue', {}).get('display_name', 'Top Tier Journal')
            date = p.get('publication_date', 'N/A')
            correct_url = get_paper_url(p)
            cites = p.get('cited_by_count', 0)
            is_oa = p.get('open_access', {}).get('is_oa', False)
            
            authors_data = p.get('authorships', [])
            authors_full = ", ".join([a.get('author', {}).get('display_name', '') for a in authors_data])
            authors_short = ", ".join([a.get('author', {}).get('display_name', '') for a in authors_data[:2]]) + (" et al." if len(authors_data)>2 else "")
            
            abs_text = decode_abstract(p.get('abstract_inverted_index'))
            topics = get_topic_tags(title, abs_text)

            # --- 渲染卡片 ---
            st.markdown(f"""
            <div class="res-card">
                <div class="res-stripe"></div>
                <div class="tag-container">
                    <span class="tag tag-journal">{venue}</span>
                    {" ".join([f'<span class="tag tag-topic">{t}</span>' for t in topics])}
                    {"<span class='tag tag-oa'>🔓 OPEN ACCESS</span>" if is_oa else ""}
                </div>
                <a class="res-title" href="{correct_url}" target="_blank">{title}</a>
                <div class="res-authors">{authors_short}</div>
                <div class="res-abstract">{abs_text[:350]}...</div>
                <div class="res-footer">
                    <span>📅 {date}  |  🔥 被引: {cites}</span>
                    <a class="action-btn" href="{correct_url}" target="_blank">阅读全文 →</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # --- 辅助操作区 (Streamlit 原生) ---
            with st.expander("📝 引用 & 详细摘要"):
                st.markdown("**APA 格式引文 (点击下方可复制):**")
                year = date.split('-')[0] if '-' in date else 'n.d.'
                st.code(f"{authors_full} ({year}). {title}. {venue}. {correct_url}")
                st.markdown("---")
                st.markdown("**完整摘要:**")
                st.write(abs_text)

if __name__ == "__main__":
    main()
