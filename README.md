# 🧭 Sentiment Compass: 舆论信念罗盘

> **"Price is the monetization of collective belief."** > 价格本质上是一种信念。当舆论情绪形成共振（Resonance）时，市场价格往往会出现非线性的相变。

## 📖 项目简介 (Introduction)
这是一个基于 Streamlit 的 Web 应用程序，旨在量化和可视化市场舆论情绪。
作为物理学背景的研究者，我们将市场视为一个受“情绪场”影响的复杂系统。本项目利用 NLP 技术捕捉文本中的情绪极性（Polarity）和主观度（Subjectivity），帮助识别市场噪音与有效信号。

## ✨ 核心功能 (Features)
1.  **Micro Analysis (单点分析)**: 
    - 快速评估单条新闻、推文或评论的情绪倾向。
    - 可视化情绪仪表盘，识别极端的非理性情绪。
2.  **Macro Trend (趋势模拟)**: 
    - 模拟时间序列下的情绪累积效应。
    - 展示“舆论先行，价格随后”的滞后相关性。

## 🛠️ 技术栈 (Tech Stack)
- **Frontend**: Streamlit (快速构建交互式 Web UI)
- **NLP Engine**: TextBlob (当前版本), 预留 FinBERT 接口
- **Visualization**: Plotly (交互式金融图表)
- **Containerization**: Docker (标准化运行环境)

## 🚀 快速开始 (Quick Start)

### 方法 A: 直接运行 (Local)
确保已安装 Python 3.10+
```bash
pip install -r requirements.txt
python -m textblob.download_corpora
streamlit run app.py

```

### 方法 B: Docker 容器化 (推荐)

避免环境依赖问题，一次构建，到处运行。

```bash
# 1. 构建镜像
docker build -t sentiment-compass .

# 2. 启动容器 (访问 http://localhost:8501)
docker run -p 8501:8501 sentiment-compass

```

## 📝 待办事项 (Roadmap)

* [ ] 接入真实新闻源 API (NewsAPI / Twitter API)
* [ ] 引入 **Ising Model** (伊辛模型) 模拟舆论在社交网络中的自旋传播
* [ ] 升级 NLP 模型至 HuggingFace FinBERT