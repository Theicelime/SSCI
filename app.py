import streamlit as st
import requests
import duckdb
import pandas as pd
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
import torch
import json
import os

# ==========================================
# 1. 系统配置与数据库初始化
# ==========================================
DB_FILE = 'egis_academic.db'
con = duckdb.connect(DB_FILE)

# 初始化表结构：增加阅读标记和向量列
con.execute("""
CREATE TABLE IF NOT EXISTS papers (
    doi VARCHAR PRIMARY KEY,
    title TEXT,
    journal VARCHAR,
    pub_date DATE,
    authors TEXT,
    abstract TEXT,
    oa_url TEXT,
    citations INTEGER,
    tags TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    fetch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 加载轻量级向量模型（首次运行需联网下载，之后本地运行）
@st.cache_resource
def load_embedder():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_embedder()

# ==========================================
# 2. 高保真 Researcher UI (CSS)
# ==========================================
def apply_researcher_v5_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    header {visibility: hidden;}
    .main .block-container { padding-top: 1rem; max-width: 720px; }
    
    /* 时间线 Feed 卡片 */
    .res-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 4px;
        padding: 24px; margin-bottom: 12px; position: relative;
    }
    .res-card.unread { border-left: 4px solid #3b82f6; }
    .res-card.read { border-left: 4px solid #e2e8f0; opacity: 0.8; }
    
    .res-journal { font-size: 11px; font-weight: 700; color: #3b82f6; text-transform: uppercase; margin-bottom: 8px; }
    .res-title { font-size: 18px; font-weight: 700; color: #0f172a; line-height: 1.4; margin-bottom: 8px; }
    .res-authors { font-size: 13px; color: #64748b; margin-bottom: 12px; }
    
    /* 自动生成的语义标签 */
    .tag-pill {
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 10px; font-weight: 600; margin-right: 5px;
        background: #f1f5f9; color: #475569;
    }
    
    .res-footer {
        margin-top: 16px; padding-top: 12px; border-top: 1px solid #f1f5f9;
        display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. 后端引擎：增量抓取与语义解析
# ==========================================

def decode_abstract(inverted_index):
    if not inverted_index: return ""
    d = {i: w for w, p in inverted_index.items() for i in p}
    return " ".join([d[i] for i in sorted(d.keys())])

def fetch_and_sync(journal_ids):
    """增量同步：仅存入数据库中不存在的 DOI"""
    id_filter = "|".join(journal_ids)
    url = f"https://api.openalex.org/works?filter=primary_location.source.id:{id_filter}&sort=publication_date:desc&per_page=50"
    
    try:
        r = requests.get(url, timeout=15).json().get('results', [])
        for p in r:
            doi = p.get('doi')
            if not doi: continue
            
            # 检查去重
            exists = con.execute("SELECT 1 FROM papers WHERE doi = ?", [doi]).fetchone()
            if not exists:
                title = p.get('display_name')
                abstract = decode_abstract(p.get('abstract_inverted_index'))
                # 解析 OA 链接：Publisher -> Best OA
                oa_url = p.get('best_oa_location', {}).get('pdf_url') or p.get('doi')
                authors = ", ".join([a['author']['display_name'] for a in p.get('authorships', [])[:3]])
                
                con.execute("""
                INSERT INTO papers (doi, title, journal, pub_date, authors, abstract, oa_url, citations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, [doi, title, p['host_venue']['display_name'], p['publication_date'], authors, abstract, oa_url, p['cited_by_count']])
        return True
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return False

# ==========================================
# 4. 前端交互与语义过滤
# ==========================================

def main():
    apply_researcher_v5_style()
    
    # --- Sidebar: 控制中心 ---
    with st.sidebar:
        st.title("EGIS Pro")
        st.caption("Environmental Gerontology Intel")
        
        journals = {
            "The Gerontologist": "S151833132",
            "Health & Place": "S108842106",
            "Landscape & Urban Planning": "S162319083",
            "Ageing & Society": "S4210170428"
        }
        
        selected_journals = st.multiselect("订阅列表", list(journals.keys()), default=list(journals.keys()))
        
        st.markdown("---")
        # 语义过滤滑块
        semantic_query = st.text_input("🎯 语义焦点筛选", placeholder="如：建成环境与跌倒风险...")
        similarity_threshold = st.slider("匹配相关度", 0.0, 1.0, 0.3)
        
        st.markdown("---")
        if st.button("🔄 同步云端数据"):
            ids = [journals[n] for n in selected_journals]
            if fetch_and_sync(ids):
                st.success("同步完成")
                st.rerun()

    # --- 主 Feed 流逻辑 ---
    st.markdown("### 📥 智能订阅流")
    
    # 从 DuckDB 读取数据
    df = con.execute("SELECT * FROM papers ORDER BY pub_date DESC").df()
    
    if df.empty:
        st.info("库内暂无数据，请点击左侧同步按钮。")
        return

    # 语义过滤逻辑
    if semantic_query and not df.empty:
        query_embedding = model.encode(semantic_query, convert_to_tensor=True)
        # 对标题+摘要进行编码（实际应用中应预存 embedding 以加速）
        df['content'] = df['title'] + " " + df['abstract']
        content_embeddings = model.encode(df['content'].tolist(), convert_to_tensor=True)
        cosine_scores = util.cos_sim(query_embedding, content_embeddings)[0]
        df['score'] = cosine_scores.tolist()
        df = df[df['score'] >= similarity_threshold].sort_values(by='score', ascending=False)

    # 渲染 Researcher 列表
    for _, row in df.iterrows():
        card_class = "read" if row['is_read'] else "unread"
        
        st.markdown(f"""
        <div class="res-card {card_class}">
            <div class="res-stripe"></div>
            <div class="res-journal">{row['journal']}</div>
            <div class="res-title">{row['title']}</div>
            <div class="res-authors">{row['authors']}</div>
            <div class="res-abstract">{row['abstract'][:250]}...</div>
            <div class="res-footer">
                <span>📅 {row['pub_date']} | 🔥 被引: {row['citations']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 交互区：沉浸式摘要与跳转
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("📖 摘要", key=f"abs_{row['doi']}"):
                st.info(row['abstract'])
        with col2:
            st.link_button("🚀 全文", row['oa_url'])
        with col3:
            if not row['is_read']:
                if st.button("✔️ 标记已读", key=f"read_{row['doi']}"):
                    con.execute("UPDATE papers SET is_read = True WHERE doi = ?", [row['doi']])
                    st.rerun()

if __name__ == "__main__":
    main()
