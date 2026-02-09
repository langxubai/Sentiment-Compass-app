import streamlit as st
from textblob import TextBlob
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
import praw  # 新增: Reddit API 库

# --- 页面配置 ---
st.set_page_config(
    page_title="Sentiment Compass: 舆论信念罗盘",
    page_icon="🧭",
    layout="wide"
)

# --- 核心逻辑函数 (NLP) ---
def analyze_sentiment(text):
    """
    使用 TextBlob 进行基础情绪分析。
    Return: polarity (-1 to 1), subjectivity (0 to 1)
    """
    if not text:
        return 0, 0
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity

def get_sentiment_label(score):
    if score > 0.1:
        return "积极 (Positive) 🟢"
    elif score < -0.1:
        return "消极 (Negative) 🔴"
    else:
        return "中性 (Neutral) ⚪"

# --- 数据源 A: NewsAPI (机构/官方口径) ---
def fetch_news_data(topic, api_key):
    if not api_key:
        return pd.DataFrame()
    
    url = f"https://newsapi.org/v2/everything?q={topic}&language=en&sortBy=publishedAt&pageSize=50&apiKey={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") != "ok":
            st.error(f"NewsAPI Error: {data.get('message')}")
            return pd.DataFrame()
        
        articles = data.get("articles", [])
        processed_data = []
        for article in articles:
            title = article.get("title", "")
            desc = article.get("description", "") or ""
            date_str = article.get("publishedAt", "")[:10] # YYYY-MM-DD
            full_text = f"{title}. {desc}"
            
            pol, subj = analyze_sentiment(full_text)
            processed_data.append({
                "Date": date_str,
                "Text": title,
                "Sentiment": pol,
                "Subjectivity": subj,
                "Source": "News (Institutional)"
            })
        return pd.DataFrame(processed_data)
    except Exception as e:
        st.error(f"NewsAPI 请求失败: {e}")
        return pd.DataFrame()

# --- 数据源 B: Reddit (大众/散户口径) ---
def fetch_reddit_data(topic, client_id, client_secret, user_agent="sentiment_compass_v1"):
    if not client_id or not client_secret:
        return pd.DataFrame()
    
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        # 搜索 r/all，按 'new' 排序以捕捉最新信号
        # limit=50 保证样本量与新闻对等
        submissions = reddit.subreddit("all").search(topic, sort="new", limit=50)
        
        processed_data = []
        for sub in submissions:
            # 结合标题和正文，更真实反映用户想法
            full_text = f"{sub.title} . {sub.selftext}"
            pol, subj = analyze_sentiment(full_text)
            
            # Reddit 使用 UTC 时间戳
            date_str = datetime.fromtimestamp(sub.created_utc).strftime('%Y-%m-%d')
            
            processed_data.append({
                "Date": date_str,
                "Text": sub.title,
                "Sentiment": pol,
                "Subjectivity": subj,
                "Source": "Reddit (Public/Retail)"
            })
        return pd.DataFrame(processed_data)
    except Exception as e:
        st.error(f"Reddit API 连接失败: {e}")
        return pd.DataFrame()

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 数据源配置")
    st.info("💡 **原理**：比较“官方报道”与“民间讨论”的情绪差值，寻找共振或背离信号。")
    
    st.subheader("1. 机构信号 (NewsAPI)")
    news_api_key = st.text_input("NewsAPI Key", type="password", help="必填，用于获取新闻")
    
    st.subheader("2. 微弱信号 (Reddit)")
    reddit_cid = st.text_input("Reddit Client ID", type="password")
    reddit_secret = st.text_input("Reddit Secret", type="password")
    
    st.markdown("---")
    st.caption("没有 Key? 仅使用单点分析功能不受影响。")

# --- 主页面 ---
st.title("🧭 舆论信念罗盘 (Sentiment Compass)")
st.markdown("> *\"The market is a voting machine in the short run, but a weighing machine in the long run.\"* — Benjamin Graham")

tab1, tab2 = st.tabs(["🔍 单点嗅探 (Sniffer)", "📈 趋势共振 (Resonance)"])

# --- Tab 1: 单点分析 (保持原样，略微优化展示) ---
with tab1:
    st.subheader("即时文本情绪探测")
    user_input = st.text_area("输入一条传言、评论或新闻标题：", height=100)
    
    if st.button("分析"):
        if user_input:
            pol, subj = analyze_sentiment(user_input)
            label = get_sentiment_label(pol)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("情绪极性 (Polarity)", f"{pol:.2f}")
            c2.metric("主观噪音 (Subjectivity)", f"{subj:.2f}", help="越接近 1 代表越主观/情绪化")
            c3.subheader(label)
            
            # 仪表盘
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", value = pol,
                title = {'text': "信念强度"},
                gauge = {'axis': {'range': [-1, 1]}, 'bar': {'color': "black"},
                         'steps': [{'range': [-1, -0.2], 'color': "#ff4b4b"},
                                   {'range': [-0.2, 0.2], 'color': "#f0f2f6"},
                                   {'range': [0.2, 1], 'color': "#2bd27f"}]}
            ))
            st.plotly_chart(fig, use_container_width=True)

# --- Tab 2: 趋势分析 (核心修改) ---
with tab2:
    st.subheader("🌐 宏观舆论场：机构 vs 散户")
    
    col_in, col_btn = st.columns([3, 1])
    with col_in:
        topic = st.text_input("输入资产或话题 (例如: Quantum Computing, Inflation)", value="Gold")
    with col_btn:
        start_btn = st.button("开始全网扫描", type="primary")

    if start_btn:
        if not news_api_key and not (reddit_cid and reddit_secret):
            st.error("请至少在侧边栏配置一个 API Key (NewsAPI 或 Reddit)！")
        else:
            with st.spinner(f"正在扫描 '{topic}' 的多维舆论信号..."):
                # 1. 获取数据
                df_news = fetch_news_data(topic, news_api_key)
                df_reddit = fetch_reddit_data(topic, reddit_cid, reddit_secret)
                
                # 2. 合并数据
                df_all = pd.concat([df_news, df_reddit], ignore_index=True)
                
                if not df_all.empty:
                    # 3. 数据聚合：按日期和来源计算平均情绪
                    df_all['Date'] = pd.to_datetime(df_all['Date'])
                    df_trend = df_all.groupby(['Date', 'Source'])['Sentiment'].mean().reset_index()
                    
                    st.success(f"扫描完成！共分析 {len(df_all)} 条数据 (News: {len(df_news)}, Reddit: {len(df_reddit)})")
                    
                    # 4. 绘制对比图
                    fig_trend = go.Figure()
                    
                    # 只有新闻数据时
                    if not df_news.empty:
                        news_trend = df_trend[df_trend['Source'] == 'News (Institutional)']
                        fig_trend.add_trace(go.Scatter(
                            x=news_trend['Date'], y=news_trend['Sentiment'],
                            mode='lines+markers', name='新闻 (机构/滞后)',
                            line=dict(color='#1f77b4', width=3)
                        ))
                    
                    # 只有 Reddit 数据时
                    if not df_reddit.empty:
                        reddit_trend = df_trend[df_trend['Source'] == 'Reddit (Public/Retail)']
                        fig_trend.add_trace(go.Scatter(
                            x=reddit_trend['Date'], y=reddit_trend['Sentiment'],
                            mode='lines+markers', name='讨论 (散户/先行)',
                            line=dict(color='#ff7f0e', width=3, dash='dot') # 虚线表示不稳定性
                        ))

                    fig_trend.update_layout(
                        title=f"'{topic}' 舆论分歧图 (Sentiment Divergence)",
                        yaxis=dict(title='情绪极性 (-1 悲观, 1 乐观)', range=[-1, 1]),
                        xaxis=dict(title='日期'),
                        hovermode="x unified",
                        legend=dict(orientation="h", y=1.1)
                    )
                    
                    # 添加参考线 (0轴)
                    fig_trend.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="中性基准")
                    
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
                    # 5. 详细数据展示 (增加主观度过滤)
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("#### 📰 机构新闻 (Top News)")
                        if not df_news.empty:
                            st.dataframe(df_news[['Date', 'Text', 'Sentiment']].head(10), use_container_width=True)
                    
                    with c2:
                        st.markdown("#### 🗣️ 散户高噪点 (High Subjectivity)")
                        st.caption("筛选主观度 > 0.5 的言论，通常包含强烈暗示。")
                        if not df_reddit.empty:
                            # 筛选高主观度言论
                            high_subj = df_reddit[df_reddit['Subjectivity'] > 0.5].sort_values('Sentiment')
                            st.dataframe(high_subj[['Date', 'Text', 'Sentiment']].head(10), use_container_width=True)
                            
                else:
                    st.warning("未找到数据，请检查 API Key 或尝试更换关键词。")