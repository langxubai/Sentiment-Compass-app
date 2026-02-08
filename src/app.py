import streamlit as st
from textblob import TextBlob
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

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

# --- Tab 2: 趋势分析 (模拟数据) ---
with tab2:
    st.subheader("时间序列情绪流 (Sentiment Flow)")
    st.markdown("模拟过去 30 天的市场舆论变化与商品价格的关联。")
    
    if st.button("生成模拟数据流"):
        # 模拟数据生成
        dates = [datetime.today() - timedelta(days=x) for x in range(30)]
        dates.reverse()
        
        data = []
        price = 100
        sentiment_accum = 0
        
        for date in dates:
            # 随机生成情绪波动 (模拟布朗运动 + 情绪动量)
            daily_sentiment = random.uniform(-0.5, 0.5)
            sentiment_accum += daily_sentiment
            
            # 价格受情绪驱动 (简化模型：Price ~ Integral of Sentiment)
            price = price * (1 + daily_sentiment * 0.1) 
            
            data.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Sentiment": daily_sentiment,
                "Simulated_Price": price
            })
            
        df = pd.DataFrame(data)
        
        # 绘制双轴图表
        # 创建图形
        fig_trend = go.Figure()

        # 添加价格线 (左轴)
        fig_trend.add_trace(go.Scatter(
            x=df['Date'], y=df['Simulated_Price'],
            name='商品价格 (信念结果)',
            line=dict(color='#636EFA', width=3)
        ))

        # 添加情绪柱状图 (右轴)
        fig_trend.add_trace(go.Bar(
            x=df['Date'], y=df['Sentiment'],
            name='单日舆论情绪',
            marker_color=df['Sentiment'].apply(lambda x: '#2bd27f' if x>0 else '#ff4b4b'),
            yaxis='y2',
            opacity=0.6
        ))

        # 设置双轴
        fig_trend.update_layout(
            title='舆论情绪与价格相关性模型',
            yaxis=dict(title='价格 ($)', side='left'),
            yaxis2=dict(title='情绪指数', side='right', overlaying='y', range=[-1, 1]),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
        
        st.info("观察结论：在很多时刻，情绪的剧烈波动（柱状图）往往先于价格（曲线）的剧烈变化，或者是价格变化的放大器。")