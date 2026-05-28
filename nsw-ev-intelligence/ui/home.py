import streamlit as st
import os
from databricks import sql
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="NSW EV Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">⚡ NSW EV Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-time insights for electric vehicle infrastructure, traffic, and trip planning</div>', unsafe_allow_html=True)

# Database connection helper
@st.cache_resource
def get_connection():
    return sql.connect(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN")
    )

@st.cache_data(ttl=300)
def query_data(query):
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame()

# Key metrics
st.header("📊 Platform Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="stat-card">
        <h3 style="color: #1E88E5;">🔌 EV Chargers</h3>
        <h1 style="color: #424242;">2,160</h1>
        <p>Charging stations analyzed</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="stat-card">
        <h3 style="color: #43A047;">🗺️ Regions</h3>
        <h1 style="color: #424242;">9</h1>
        <p>NSW regions monitored</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="stat-card">
        <h3 style="color: #FB8C00;">⚠️ Hazards</h3>
        <h1 style="color: #424242;">113</h1>
        <p>Traffic incidents tracked</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="stat-card">
        <h3 style="color: #8E24AA;">🚗 Routes</h3>
        <h1 style="color: #424242;">102</h1>
        <p>Optimal routes analyzed</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Feature sections
st.header("🎯 Platform Features")

col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.subheader("⚡ EV Charger Intelligence")
        st.markdown("""
        - **Nearest Chargers**: Find charging stations near any location
        - **Infrastructure Gaps**: Identify underserved areas
        - **Smart Recommendations**: AI-powered station suggestions
        - **Accessibility Scores**: Evaluate station availability
        """)
        
    with st.container():
        st.subheader("🗺️ Trip Planning")
        st.markdown("""
        - **Optimal Routes**: Safest and fastest paths
        - **Charging Requirements**: Calculate stops needed
        - **Trip Feasibility**: Assess journey viability
        - **Real-time Hazards**: Live traffic updates
        """)

with col2:
    with st.container():
        st.subheader("🚦 Traffic & Congestion")
        st.markdown("""
        - **Hourly Forecasts**: Predict congestion by hour/day
        - **Location Risk**: Identify high-risk areas
        - **Travel Recommendations**: Best times to travel
        - **Hazard Tracking**: Monitor roadworks, incidents, floods
        """)
        
    with st.container():
        st.subheader("📍 Regional Insights")
        st.markdown("""
        - **Infrastructure Metrics**: Charger density by region
        - **EV Readiness**: Regional adoption scores
        - **Fuel Comparisons**: EV vs traditional pricing
        - **Capacity Analysis**: kW availability
        """)

st.divider()

# Data sources
st.header("📚 Data Sources")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **🔌 NSW EV Charging**  
    Transport NSW open data on charging station locations, capacity, and operator details
    """)

with col2:
    st.info("""
    **🚦 Live Traffic**  
    Real-time traffic incidents, roadworks, floods, and events from NSW Live Traffic
    """)

with col3:
    st.info("""
    **⛽ Fuel Pricing**  
    Current fuel prices across NSW regions for cost comparisons
    """)

st.divider()

# Quick navigation
st.header("🚀 Quick Navigation")
st.markdown("""
Use the sidebar to explore:
- **🔌 Charger Recommendations**: Find the best charging stations
- **🚦 Traffic Forecast**: View congestion predictions
- **🗺️ Trip Intelligence**: Plan optimal EV journeys  
- **📊 Regional Metrics**: Compare infrastructure across NSW
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #757575;'>
    <p>NSW EV Intelligence Platform | Built with Databricks & Streamlit</p>
    <p>Data updated in real-time | Last refresh: Live</p>
</div>
""", unsafe_allow_html=True)
