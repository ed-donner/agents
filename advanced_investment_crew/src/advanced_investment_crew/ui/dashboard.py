"""
Streamlit Dashboard for ETF Portfolio Analysis
Main user interface for the application
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
import sys
from typing import Dict

# Add parent directory to path for relative imports
sys.path.append(str(Path(__file__).parent.parent))

from advanced_investment_crew.data.market_data import MarketDataFetcher
from advanced_investment_crew.analysis.portfolio_optimizer import PortfolioOptimizer


def format_percentage(value: float) -> str:
    """Format decimal as percentage"""
    return f"{value*100:.2f}%"


def format_currency(value: float, currency: str) -> str:
    """Format value as currency"""
    return f"{value:.2f} {currency}"


def create_price_chart(prices: pd.DataFrame, title: str = "Price History") -> go.Figure:
    """Create normalized price chart"""
    normalized = prices / prices.iloc[0] * 100
    
    fig = go.Figure()
    
    for ticker in normalized.columns:
        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized[ticker],
            name=ticker,
            mode='lines',
            hovertemplate='%{y:.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Normalized Price (Base=100)",
        hovermode='x unified',
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_returns_distribution(returns: pd.DataFrame) -> go.Figure:
    """Create returns distribution chart"""
    fig = go.Figure()
    
    for ticker in returns.columns:
        fig.add_trace(go.Histogram(
            x=returns[ticker] * 100,
            name=ticker,
            opacity=0.7,
            nbinsx=50
        ))
    
    fig.update_layout(
        title="Returns Distribution",
        xaxis_title="Daily Return (%)",
        yaxis_title="Frequency",
        barmode='overlay',
        height=400
    )
    
    return fig


def create_correlation_heatmap(correlation: pd.DataFrame) -> go.Figure:
    """Create correlation heatmap"""
    fig = go.Figure(data=go.Heatmap(
        z=correlation.values,
        x=correlation.columns,
        y=correlation.columns,
        colorscale='RdBu',
        zmid=0,
        text=correlation.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title="Correlation Matrix",
        height=500,
        xaxis={'side': 'bottom'}
    )
    
    return fig


def create_weights_chart(weights: Dict, title: str) -> go.Figure:
    """Create portfolio weights bar chart"""
    df = pd.DataFrame({
        'Ticker': list(weights.keys()),
        'Weight': list(weights.values())
    })
    
    # Filter out very small weights
    df = df[df['Weight'] > 0.001].sort_values('Weight', ascending=True)
    
    fig = go.Figure(data=[
        go.Bar(
            x=df['Weight'],
            y=df['Ticker'],
            orientation='h',
            text=[f"{w*100:.1f}%" for w in df['Weight']],
            textposition='auto',
            marker_color='steelblue'
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Weight",
        yaxis_title="Ticker",
        height=max(300, len(df) * 40),
        xaxis_tickformat='.0%',
        showlegend=False
    )
    
    return fig


def create_efficient_frontier(frontier: pd.DataFrame, 
                              max_sharpe: Dict, 
                              min_vol: Dict) -> go.Figure:
    """Create efficient frontier chart"""
    fig = go.Figure()
    
    # Efficient frontier line
    fig.add_trace(go.Scatter(
        x=frontier['Volatility'] * 100,
        y=frontier['Return'] * 100,
        mode='lines',
        name='Efficient Frontier',
        line=dict(color='blue', width=3),
        hovertemplate='Vol: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>'
    ))
    
    # Max Sharpe point
    fig.add_trace(go.Scatter(
        x=[max_sharpe['volatility'] * 100],
        y=[max_sharpe['return'] * 100],
        mode='markers+text',
        name='Max Sharpe',
        marker=dict(color='green', size=15, symbol='star'),
        text=['Max Sharpe'],
        textposition='top center',
        hovertemplate='Max Sharpe<br>Vol: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>'
    ))
    
    # Min Volatility point
    fig.add_trace(go.Scatter(
        x=[min_vol['volatility'] * 100],
        y=[min_vol['return'] * 100],
        mode='markers+text',
        name='Min Volatility',
        marker=dict(color='red', size=15, symbol='diamond'),
        text=['Min Vol'],
        textposition='bottom center',
        hovertemplate='Min Volatility<br>Vol: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title="Efficient Frontier",
        xaxis_title="Volatility (%)",
        yaxis_title="Expected Return (%)",
        height=550,
        hovermode='closest',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig


def run_dashboard():
    """Main dashboard application"""
    
    # Page configuration
    st.set_page_config(
        page_title="ETF Portfolio Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main > div {
            padding-top: 2rem;
        }
        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Title
    st.title("📊 ETF Portfolio Analyzer")
    st.markdown("*Modern Portfolio Theory-based analysis and optimization*")
    st.markdown("---")
    
    # ==================== SIDEBAR ====================
    st.sidebar.header("⚙️ Configuration")
    
    # Market selection
    market_type = st.sidebar.selectbox(
        "Select Market",
        options=['global', 'turkey'],
        format_func=lambda x: {
            'global': '🌍 Global Markets',
            'turkey': '🇹🇷 Türkiye Piyasası'
        }[x],
        key='market_selector'
    )
    
    # Initialize data fetcher
    try:
        fetcher = MarketDataFetcher(market_type=market_type)
        tickers = fetcher.get_tickers()
        currency = fetcher.get_currency()
        risk_free_rate = fetcher.get_risk_free_rate()
        market_name = fetcher.get_market_name()
        
        st.sidebar.success(f"✅ {market_name}")
        st.sidebar.info(f"💱 Currency: **{currency}**")
        st.sidebar.info(f"📈 Risk-Free Rate: **{risk_free_rate*100:.1f}%**")
        
    except Exception as e:
        st.error(f"❌ Error loading configuration: {str(e)}")
        st.stop()
    
    # Display ticker information
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Available Tickers")
    
    for ticker in tickers:
        info = fetcher.get_ticker_info(ticker)
        with st.sidebar.expander(f"**{ticker}**"):
            st.markdown(f"**{info['name']}**")
            st.caption(f"*{info['sector']}*")
            st.caption(info['description'])
    
    # Data period selection
    st.sidebar.markdown("---")
    period = st.sidebar.selectbox(
        "📅 Time Period",
        options=['1y', '2y', '5y', 'max'],
        index=1,
        help="Historical data period to analyze"
    )
    
    # ==================== MAIN CONTENT ====================
    
    # Fetch data
    with st.spinner(f"🔄 Fetching data for {len(tickers)} tickers..."):
        try:
            data = fetcher.fetch_data(period=period)
            prices = fetcher.get_close_prices(data)
            returns = fetcher.calculate_returns(prices)
            
            # Validate data
            is_valid, message = fetcher.validate_data(prices)
            if not is_valid:
                st.error(f"❌ Data validation failed: {message}")
                st.stop()
            
            st.success(f"✅ Data loaded: **{len(prices)}** days, **{len(tickers)}** tickers")
            
        except Exception as e:
            st.error(f"❌ Error fetching data: {str(e)}")
            st.info("💡 Tip: Check your internet connection and try again")
            st.stop()
    
    # ==================== PRICE ANALYSIS ====================
    st.header("📈 Price Analysis")
    
    # Price chart
    fig_prices = create_price_chart(prices, f"{market_name} - Normalized Prices")
    st.plotly_chart(fig_prices, use_container_width=True)
    
    # Statistics table
    st.subheader("📊 Performance Statistics")
    stats_df = fetcher.get_summary_statistics(prices, returns)
    st.dataframe(stats_df, use_container_width=True, hide_index=True)
    
    # ==================== RETURNS ANALYSIS ====================
    st.markdown("---")
    st.header("📉 Returns Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_dist = create_returns_distribution(returns)
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        correlation = returns.corr()
        fig_corr = create_correlation_heatmap(correlation)
        st.plotly_chart(fig_corr, use_container_width=True)
    
    # ==================== PORTFOLIO OPTIMIZATION ====================
    st.markdown("---")
    st.header("🎯 Portfolio Optimization")
    
    # Initialize optimizer
    optimizer = PortfolioOptimizer(risk_free_rate=risk_free_rate)
    
    # Optimization tabs
    tab1, tab2, tab3 = st.tabs(["📈 Max Sharpe", "🛡️ Min Volatility", "📊 Efficient Frontier"])
    
    with tab1:
        st.subheader("Maximum Sharpe Ratio Portfolio")
        
        with st.spinner("Optimizing for maximum Sharpe ratio..."):
            max_sharpe = optimizer.optimize_sharpe(returns)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Expected Return",
                format_percentage(max_sharpe['return']),
                help="Annualized expected return"
            )
        
        with col2:
            st.metric(
                "Volatility",
                format_percentage(max_sharpe['volatility']),
                help="Annualized standard deviation"
            )
        
        with col3:
            st.metric(
                "Sharpe Ratio",
                f"{max_sharpe['sharpe_ratio']:.3f}",
                help="Risk-adjusted return measure"
            )
        
        # Weights chart
        fig_weights = create_weights_chart(max_sharpe['weights'], "Optimal Portfolio Weights")
        st.plotly_chart(fig_weights, use_container_width=True)
        
        # Weights table
        weights_df = pd.DataFrame({
            'Ticker': list(max_sharpe['weights'].keys()),
            'Weight': [format_percentage(w) for w in max_sharpe['weights'].values()],
            'Name': [fetcher.get_ticker_info(t)['name'] for t in max_sharpe['weights'].keys()]
        })
        weights_df = weights_df[weights_df['Weight'] != '0.00%'].sort_values(
            by='Weight', 
            key=lambda x: x.str.rstrip('%').astype(float),
            ascending=False
        )
        st.dataframe(weights_df, use_container_width=True, hide_index=True)
    
    with tab2:
        st.subheader("Minimum Volatility Portfolio")
        
        with st.spinner("Optimizing for minimum volatility..."):
            min_vol = optimizer.optimize_min_volatility(returns)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Expected Return",
                format_percentage(min_vol['return']),
                help="Annualized expected return"
            )
        
        with col2:
            st.metric(
                "Volatility",
                format_percentage(min_vol['volatility']),
                help="Annualized standard deviation"
            )
        
        with col3:
            st.metric(
                "Sharpe Ratio",
                f"{min_vol['sharpe_ratio']:.3f}",
                help="Risk-adjusted return measure"
            )
        
        # Weights chart
        fig_weights = create_weights_chart(min_vol['weights'], "Optimal Portfolio Weights")
        st.plotly_chart(fig_weights, use_container_width=True)
        
        # Weights table
        weights_df = pd.DataFrame({
            'Ticker': list(min_vol['weights'].keys()),
            'Weight': [format_percentage(w) for w in min_vol['weights'].values()],
            'Name': [fetcher.get_ticker_info(t)['name'] for t in min_vol['weights'].keys()]
        })
        weights_df = weights_df[weights_df['Weight'] != '0.00%'].sort_values(
            by='Weight',
            key=lambda x: x.str.rstrip('%').astype(float),
            ascending=False
        )
        st.dataframe(weights_df, use_container_width=True, hide_index=True)
    
    with tab3:
        st.subheader("Efficient Frontier")
        
        with st.spinner("Calculating efficient frontier..."):
            frontier = optimizer.calculate_efficient_frontier(returns, n_points=40)
        
        fig_frontier = create_efficient_frontier(frontier, max_sharpe, min_vol)
        st.plotly_chart(fig_frontier, use_container_width=True)
        
        st.info("""
        **📚 Understanding the Efficient Frontier:**
        - The blue line represents all optimal portfolios (best return for given risk)
        - **Green star**: Maximum Sharpe ratio (best risk-adjusted return)
        - **Red diamond**: Minimum volatility (lowest risk)
        - Portfolios below the line are sub-optimal
        """)
    
    # ==================== FOOTER ====================
    st.markdown("---")
    st.caption(f"""
    💡 **Data Source:** Yahoo Finance | 
    **Market:** {market_name} | 
    **Currency:** {currency} | 
    **Period:** {period} | 
    **Last Updated:** {prices.index[-1].strftime('%Y-%m-%d')}
    """)
    
    st.caption("⚠️ *This tool is for educational purposes only. Not financial advice.*")


if __name__ == "__main__":
    run_dashboard()
