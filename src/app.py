import streamlit as st
from textblob import TextBlob
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import requests

# --- 页面配置 ---
st.set_page_config(
    page_title="舆论信念罗盘 (Sentiment Compass)",
    page_icon="🧭",
    layout="wide"
)

# --- 核心逻辑函数 (NLP) ---
def analyze_sentiment(text):
    """
    使用 TextBlob 进行基础情绪分析。
    Return: polarity (区间 -1 到 1, <0 为负面, >0 为正面)
    注意：后续可在此处替换为 BERT/RoBERTa 模型以提高金融语境准确度。
    """
    if not text:
        return 0, 0
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity

# --- 数据获取函数 ---
def fetch_news_data(topic, api_key):
    """
    从 NewsAPI 获取指定话题的新闻，并进行情绪分析。
    """
    url = f"https://newsapi.org/v2/everything?q={topic}&language=en&sortBy=publishedAt&pageSize=50&apiKey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") != "ok":
            st.error(f"API Error: {data.get('message')}")
            return pd.DataFrame()
        
        articles = data.get("articles", [])
        processed_data = []
        
        for article in articles:
            # 获取标题和发布时间
            title = article.get("title", "")
            description = article.get("description", "") or ""
            published_at = article.get("publishedAt", "")[:10] # 截取日期部分 YYYY-MM-DD
            
            # 合并标题和描述进行更准确的情绪分析
            full_text = f"{title}. {description}"
            
            # 调用你原有的分析函数
            polarity, subjectivity = analyze_sentiment(full_text)
            
            processed_data.append({
                "Date": published_at,
                "Title": title,
                "Sentiment": polarity,
                "Subjectivity": subjectivity
            })
            
        return pd.DataFrame(processed_data)
        
    except Exception as e:
        st.error(f"网络请求失败: {e}")
        return pd.DataFrame()

def get_sentiment_label(score):
    if score > 0.1:
        return "积极 (Positive) 🟢"
    elif score < -0.1:
        return "消极 (Negative) 🔴"
    else:
        return "中性 (Neutral) ⚪"

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 参数设置")
    st.info("💡 提示：商品价格是信念的投影。当大众情绪极端化时，往往是反转的信号。")
    model_choice = st.selectbox("选择NLP模型", ["TextBlob (通用/快速)", "FinBERT (金融专用/需显存)"])
    if model_choice == "FinBERT (金融专用/需显存)":
        st.warning("演示模式暂仅支持 TextBlob，部署 FinBERT 需要 PyTorch 环境。")

# --- 主页面 ---
st.title("🧭 舆论信念罗盘")
st.markdown("> *\"Market prices are always wrong in the sense that they present a biased view of the future.\"* — George Soros")

# 创建两个选项卡：单点分析 vs 趋势分析
tab1, tab2 = st.tabs(["🔍 单点舆情分析", "📈 市场情绪趋势"])

# --- Tab 1: 单点分析 ---
with tab1:
    st.subheader("即时新闻/评论分析")
    user_input = st.text_area("输入你看到的市场传言、新闻标题或评论：", height=150, placeholder="例如：The Federal Reserve decided to cut interest rates, which is great for gold prices.")
    
    if st.button("分析情绪信念"):
        if user_input:
            polarity, subjectivity = analyze_sentiment(user_input)
            label = get_sentiment_label(polarity)
            
            # 结果展示列
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("情绪极性 (Polarity)", f"{polarity:.2f}", delta_color="normal")
            with col2:
                st.metric("主观程度 (Subjectivity)", f"{subjectivity:.2f}")
            with col3:
                st.subheader(label)
            
            # 仪表盘可视化
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = polarity,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "市场信念强度"},
                gauge = {
                    'axis': {'range': [-1, 1]},
                    'bar': {'color': "black"},
                    'steps': [
                        {'range': [-1, -0.3], 'color': "#ff4b4b"},  # Red
                        {'range': [-0.3, 0.3], 'color': "#f0f2f6"}, # Grey
                        {'range': [0.3, 1], 'color': "#2bd27f"}     # Green
                    ],
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
            
            # 物理/AI 背景的解释
            st.caption(f"**分析逻辑：** 基于 NLP 语义向量分析。Polarity 为 -1 (极度悲观) 到 1 (极度乐观)。如果主观程度高且情绪极端，通常代表非理性的“噪音”。")

# --- Tab 2: 真实趋势分析 ---
with tab2:
    st.subheader("🌐 实时舆论趋势 (Live Sentiment Trend)")
    
    # 1. 获取用户输入
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        topic = st.text_input("输入关注的资产/话题 (例如: Gold, Bitcoin, AI)", value="Quantum Computing")
    with col_btn:
        # 实际开发中建议将 API Key 放入 st.secrets，这里为了演示通过输入框获取或硬编码
        api_key = st.text_input("NewsAPI Key", type="password", help="去 newsapi.org 免费申请")
        start_btn = st.button("抓取并分析")

    if start_btn and topic and api_key:
        with st.spinner(f"正在全网搜索关于 '{topic}' 的舆论信号..."):
            # A. 获取真实数据
            df_raw = fetch_news_data(topic, api_key)
            
            if not df_raw.empty:
                # B. 数据聚合 (按日期计算平均情绪)
                # 将日期转换为 datetime 对象以便排序
                df_raw['Date'] = pd.to_datetime(df_raw['Date'])
                df_trend = df_raw.groupby('Date')[['Sentiment']].mean().reset_index()
                df_trend = df_trend.sort_values('Date')
                
                # C. 统计数据展示
                st.success(f"成功分析了 {len(df_raw)} 条相关新闻！")
                
                avg_sentiment = df_raw['Sentiment'].mean()
                sentiment_str = "乐观 🟢" if avg_sentiment > 0.05 else ("悲观 🔴" if avg_sentiment < -0.05 else "中性 ⚪")
                
                m1, m2, m3 = st.columns(3)
                m1.metric("当前综合情绪", f"{avg_sentiment:.3f}", sentiment_str)
                m2.metric("最大波动 (Max Polarity)", f"{df_raw['Sentiment'].max():.2f}")
                m3.metric("新闻样本量", len(df_raw))

                # D. 绘图 (和原来类似的双轴图，但这里我们先只画情绪趋势)
                fig_trend = go.Figure()

                # 情绪柱状图
                fig_trend.add_trace(go.Bar(
                    x=df_trend['Date'], 
                    y=df_trend['Sentiment'],
                    name='平均舆论情绪',
                    marker_color=df_trend['Sentiment'].apply(lambda x: '#2bd27f' if x>0 else '#ff4b4b')
                ))
                
                # 添加趋势线
                fig_trend.add_trace(go.Scatter(
                    x=df_trend['Date'],
                    y=df_trend['Sentiment'],
                    mode='lines',
                    name='情绪平滑曲线',
                    line=dict(color='blue', width=2, shape='spline')
                ))

                fig_trend.update_layout(
                    title=f"'{topic}' 过去30天舆论情绪走势",
                    yaxis=dict(title='情绪极性 (Polarity)', range=[-1, 1]),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # E. 展示具体新闻列表 (增加可信度)
                with st.expander("查看底层新闻源 (Source Data)"):
                    st.dataframe(df_raw[['Date', 'Title', 'Sentiment']].sort_values(by='Date', ascending=False), use_container_width=True)
            
            else:
                st.warning("未找到相关数据，请检查 API Key 或更换关键词。")