import streamlit as st
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import requests
import praw

# --- 页面配置 ---
st.set_page_config(
    page_title="Sentiment Compass: Ising Model Edition",
    page_icon="🧭",
    layout="wide"
)

# --- 初始化 VADER 分析器 (比 TextBlob 更敏感) ---
@st.cache_resource
def get_vader_analyzer():
    return SentimentIntensityAnalyzer()

vader = get_vader_analyzer()

# --- 核心物理逻辑函数 (Physics Core) ---

def analyze_signal(text):
    """
    混合分析模型：
    1. VADER Compound: 捕捉微弱情绪信号 (-1 到 1)，作为自旋 (Spin)。
    2. TextBlob Subjectivity: 捕捉主观程度 (0 到 1)，作为噪声/温度 (Temperature)。
    """
    if not text:
        return 0.0, 0.0
    
    # VADER 处理社交文本/噪声能力更强
    vs = vader.polarity_scores(text)
    spin = vs['compound'] 
    
    # TextBlob 处理主观性
    blob = TextBlob(text)
    noise_level = blob.sentiment.subjectivity
    
    return spin, noise_level

def calculate_ising_metrics(df):
    """
    计算伊辛模型关键指标。
    输入 df 需包含 'Sentiment' 列 (即 Spin)。
    """
    if df.empty:
        return 0, 0
    
    spins = df['Sentiment'].values
    
    # 1. 磁化强度 (Magnetization, M): 舆论的一致性方向
    # M ~ <s_i>
    magnetization = np.mean(spins)
    
    # 2. 磁化率 (Susceptibility, χ): 舆论的“易感性”或“脆弱度”
    # 在物理上，χ = ( <M^2> - <M>^2 ) / T
    # 这里我们简化为自旋的方差 (Variance of Sentiment)
    # 物理意义：当 χ 变大时，系统处于临界态，微小的外部新闻(外场 H)就能引发崩塌(相变)。
    susceptibility = np.var(spins)
    
    return magnetization, susceptibility

# --- 数据获取函数 ---

def fetch_newsapi_data(topic, api_key):
    """从 NewsAPI 获取广播型数据 (Broadcasting)"""
    url = f"https://newsapi.org/v2/everything?q={topic}&language=en&sortBy=publishedAt&pageSize=100&apiKey={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") != "ok":
            st.error(f"NewsAPI Error: {data.get('message')}")
            return pd.DataFrame()
        
        articles = data.get("articles", [])
        processed_data = []
        for article in articles:
            text = f"{article.get('title', '')}. {article.get('description', '')}"
            spin, noise = analyze_signal(text)
            processed_data.append({
                "Date": article.get("publishedAt", "")[:19], # ISO format
                "Text": text,
                "Sentiment": spin,     # Spin
                "Subjectivity": noise, # Temperature
                "Source": "NewsAPI"
            })
        return pd.DataFrame(processed_data)
    except Exception as e:
        st.error(f"NewsAPI 请求失败: {e}")
        return pd.DataFrame()

def fetch_reddit_data(topic, client_id, client_secret, user_agent="sentiment_compass_v2"):
    """从 Reddit 获取噪声型数据 (Noise/Micro-states)"""
    try:
        reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
        subreddit = reddit.subreddit("all")
        # 搜索相关讨论，不局限于金融板块
        posts = subreddit.search(topic, sort='new', limit=100)
        
        processed_data = []
        for post in posts:
            # 结合标题和高赞评论可能更佳，这里先只取标题以保证速度
            text = f"{post.title} {post.selftext[:200]}" 
            spin, noise = analyze_signal(text)
            processed_data.append({
                "Date": datetime.fromtimestamp(post.created_utc).isoformat(),
                "Text": text,
                "Sentiment": spin,
                "Subjectivity": noise,
                "Source": "Reddit"
            })
        return pd.DataFrame(processed_data)
    except Exception as e:
        st.error(f"Reddit API 错误 (请检查 Credentials): {e}")
        return pd.DataFrame()

def generate_simulation_data():
    """
    生成模拟的相变数据 (Monte Carlo Simulation 伪造)。
    模拟一个系统从无序(Disordered) -> 临界态(Critical) -> 有序(Ordered) 的过程。
    """
    dates = pd.date_range(end=datetime.now(), periods=100, freq='H')
    data = []
    
    # 阶段 1: 随机噪声 (无序)
    for i in range(40):
        spin = np.random.normal(0, 0.2) # 均值0，方差小
        data.append({"Date": dates[i], "Sentiment": spin, "Subjectivity": np.random.random()})
        
    # 阶段 2: 临界涨落 (Critical Fluctuations) - 均值仍为0，但方差剧增
    for i in range(40, 70):
        # 模拟意见分歧巨大：有人极度看多，有人极度看空
        spin = np.random.choice([0.8, -0.8]) + np.random.normal(0, 0.1) 
        data.append({"Date": dates[i], "Sentiment": spin, "Subjectivity": 0.9})
        
    # 阶段 3: 相变/对称性破缺 (Symmetry Breaking) - 坍缩到一个方向
    for i in range(70, 100):
        spin = -0.9 + np.random.normal(0, 0.1) # 突然崩盘
        data.append({"Date": dates[i], "Sentiment": spin, "Subjectivity": 0.6})
        
    return pd.DataFrame(data)

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 探测器设置")
    st.markdown("### 1. 选择数据源")
    data_source = st.selectbox(
        "Data Source", 
        ["Simulation (物理演示)", "NewsAPI (广播信号)", "Reddit (微观噪声)"]
    )
    
    api_key = None
    reddit_cid = None
    reddit_sec = None
    
    if data_source == "NewsAPI (广播信号)":
        api_key = st.text_input("NewsAPI Key", type="password")
    elif data_source == "Reddit (微观噪声)":
        st.info("需要 Reddit App Credentials")
        reddit_cid = st.text_input("Client ID", type="password")
        reddit_sec = st.text_input("Client Secret", type="password")

    st.divider()
    st.markdown("### 2. 物理参数解释")
    st.markdown("**Magnetization ($M$):**\n平均舆论方向。$M \\approx 0$ 表示多空平衡。")
    st.markdown("**Susceptibility ($\chi$):**\n舆论易感性(方差)。\n⚠️ **高 $\chi$ + 低 $M$ = 暴风雨前的宁静。**")

# --- 主页面 ---
st.title("🧭 Sentiment Compass: Ising Model Edition")
st.caption("基于统计物理 (Statistical Physics) 的舆论相变探测器")

tab1, tab2 = st.tabs(["🔬 微观粒子分析 (Micro)", "📈 宏观相变监控 (Macro)"])

# --- Tab 1: 单文本分析 ---
with tab1:
    st.subheader("单条讯息自旋测定")
    txt = st.text_area("输入文本 (推文/评论/新闻):", value="I am worried about the inflation, but AI stocks seem unstoppable!")
    if st.button("计算自旋 (Calculate Spin)"):
        spin, noise = analyze_signal(txt)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("自旋方向 (Spin)", f"{spin:.2f}")
        c2.metric("热噪声 (Temp)", f"{noise:.2f}")
        
        state = "中性 (Paramagnetic)"
        if spin > 0.3: state = "上自旋 (Positive) 🟢"
        if spin < -0.3: state = "下自旋 (Negative) 🔴"
        c3.metric("当前状态", state)

# --- Tab 2: 宏观分析 ---
with tab2:
    st.subheader("舆论场相变监控 (Phase Transition Monitor)")
    
    topic = st.text_input("输入话题 (Topic):", value="Quantum Computing")
    start = st.button("启动探测 (Initialize Detector)")
    
    if start:
        df = pd.DataFrame()
        
        with st.spinner("正在采集场数据..."):
            if data_source == "Simulation (物理演示)":
                df = generate_simulation_data()
                st.warning("⚠️ 当前为模拟数据：展示了典型的从无序到相变的过程。")
            elif data_source == "NewsAPI (广播信号)":
                if api_key:
                    df = fetch_newsapi_data(topic, api_key)
                else:
                    st.error("请输入 NewsAPI Key")
            elif data_source == "Reddit (微观噪声)":
                if reddit_cid and reddit_sec:
                    df = fetch_reddit_data(topic, reddit_cid, reddit_sec)
                else:
                    st.error("请输入 Reddit Credentials")

        if not df.empty:
            # 数据预处理
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            
            # 滑动窗口计算物理指标 (模拟随时间的演化)
            # 我们使用 Expanding window 来模拟信息的累积，或者 Rolling window 模拟瞬时状态
            window_size = len(df) // 10 if len(df) > 20 else 5
            
            df['Magnetization'] = df['Sentiment'].rolling(window=window_size).mean()
            df['Susceptibility'] = df['Sentiment'].rolling(window=window_size).var()
            
            # 布局：上图为原始自旋分布，下图为物理指标
            
            # 图1: 自旋分布散点图
            fig_scatter = px.scatter(
                df, x='Date', y='Sentiment', color='Subjectivity',
                title=f"微观自旋分布 (Micro-States Scatters) - {topic}",
                color_continuous_scale='Bluered',
                range_y=[-1.1, 1.1]
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # 图2: 序参量 (M) 与 响应函数 (χ)
            st.markdown("### 📊 序参量与临界指标")
            
            # 双轴图
            fig_macro = go.Figure()
            
            # 左轴：磁化强度 M
            fig_macro.add_trace(go.Scatter(
                x=df['Date'], y=df['Magnetization'],
                name='磁化强度 (Avg Sentiment)',
                line=dict(color='blue', width=2)
            ))
            
            # 右轴：磁化率 χ
            fig_macro.add_trace(go.Scatter(
                x=df['Date'], y=df['Susceptibility'],
                name='磁化率/易感性 (Variance)',
                line=dict(color='red', width=2, dash='dot'),
                yaxis='y2'
            ))
            
            fig_macro.update_layout(
                title="相变前兆监控 (Order Parameter vs Susceptibility)",
                yaxis=dict(title="Magnetization (M)", range=[-1, 1]),
                yaxis2=dict(
                    title="Susceptibility (χ)", 
                    overlaying='y', 
                    side='right',
                    range=[0, df['Susceptibility'].max() * 1.2]
                ),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig_macro, use_container_width=True)
            
            # 物理洞察解释
            curr_sus = df['Susceptibility'].iloc[-1]
            st.info(f"""
            **物理诊断报告:**
            - 当前磁化率 ($\chi$): **{curr_sus:.4f}**
            - **解读**: 
                - 如果 $\chi$ 较低且 $M$ 接近 0：系统处于**无序相 (Disordered Phase)**，噪声为主。
                - 如果 $\chi$ 急剧升高：系统处于**临界点 (Critical Point)**。即使 $M$ 看起来正常，市场也极其脆弱，随时可能发生对称性破缺。
                - 如果 $M$ 很大且 $\chi$ 回落：系统已完成**相变 (Phase Transition)**，进入有序相（单边行情）。
            """)
            
            with st.expander("查看原始数据 (Raw Lattice Data)"):
                st.dataframe(df.sort_values(by='Date', ascending=False))