import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import pytz

# ==========================================
# 页面配置 (手机端适配)
# ==========================================
st.set_page_config(
    page_title="Nano Sniper V4",
    page_icon="🎯",
    layout="centered" # 手机端居中显示更好看
)

# ==========================================
# 核心逻辑 (Judge Logic)
# ==========================================
def analyze_ticker(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # 抓取盘前盘后
        df = ticker.history(period="1d", interval="1m", prepost=True)
        
        if df.empty:
            # 尝试抓取5天
            df = ticker.history(period="5d", interval="1m", prepost=True)
            if not df.empty:
                last_date = df.index[-1].date()
                df = df[df.index.date == last_date]
        
        if df.empty:
            return None, "No Data"

        # 计算 VWAP
        v = df['Volume'].values
        p = df['Close'].values
        df = df.assign(vwap=(p * v).cumsum() / v.cumsum())
        
        return df, None
    except Exception as e:
        return None, str(e)

# ==========================================
# UI 界面渲染
# ==========================================
st.title("🎯 Nano-Judge V4")
st.caption("VWAP 机构成本审判系统 | 手机便携版")

# 输入框
symbol = st.text_input("输入股票代码 (如 DXF, UAVS):", "").upper().strip()

if symbol:
    with st.spinner(f"正在审判 ${symbol}..."):
        df, error = analyze_ticker(symbol)
        
        if error:
            st.error(f"❌ 获取数据失败: {error}")
        elif df is not None:
            # 提取最新数据
            latest = df.iloc[-1]
            current_price = float(latest['Close'])
            vwap_price = float(latest['vwap'])
            day_high = df['High'].max()
            day_low = df['Low'].min()
            last_time = latest.name.strftime('%H:%M:%S')
            
            # 计算乖离率
            deviation = (current_price - vwap_price) / vwap_price * 100
            
            # --- 判决逻辑 ---
            verdict = ""
            verdict_color = ""
            reason = ""
            
            if current_price < vwap_price:
                verdict = "❌ 绝对别买 (NO TOUCH)"
                verdict_color = "red"
                reason = "价格在水下 (Below VWAP)，空头控盘。"
            elif deviation > 5.0:
                verdict = "⚠️ 别追高 (DONT CHASE)"
                verdict_color = "orange"
                reason = f"乖离率过大 ({deviation:.2f}%)，等待回调。"
            else:
                verdict = "✅ 买入 (BUY)"
                verdict_color = "green"
                reason = "站稳成本线，多头控盘，位置安全。"

            # --- 显示结果 ---
            
            # 1. 醒目的判决横幅
            if verdict_color == "green":
                st.success(f"## {verdict}")
            elif verdict_color == "red":
                st.error(f"## {verdict}")
            else:
                st.warning(f"## {verdict}")
            
            st.info(f"💡 {reason}")
            
            # 2. 核心指标卡片
            col1, col2, col3 = st.columns(3)
            col1.metric("实时价格", f"${current_price:.3f}", f"{deviation:.2f}% vs VWAP")
            col2.metric("机构成本 (VWAP)", f"${vwap_price:.3f}")
            col3.metric("止损红线", f"${max(day_low, vwap_price * 0.98):.3f}")

            # 3. 交互式图表 (Plotly) - 手机上能缩放
            st.markdown("### 📊 分时博弈图")
            fig = go.Figure()
            
            # 价格线
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Close'], 
                mode='lines', name='Price',
                line=dict(color='white', width=2)
            ))
            
            # VWAP 线
            fig.add_trace(go.Scatter(
                x=df.index, y=df['vwap'], 
                mode='lines', name='VWAP',
                line=dict(color='orange', width=2, dash='dash')
            ))
            
            fig.update_layout(
                template="plotly_dark",
                margin=dict(l=0, r=0, t=0, b=0),
                height=350,
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.caption(f"数据更新时间: {last_time} (美东)")

        else:
            st.error("数据为空，可能是停牌或代码错误。")
