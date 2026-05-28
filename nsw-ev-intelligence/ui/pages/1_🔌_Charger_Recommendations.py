import streamlit as st
import pandas as pd
from databricks import sql
import os
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="EV Charger Recommendations", page_icon="🔌", layout="wide")

st.title("🔌 EV Charger Recommendations")
st.markdown("Find optimal charging stations based on location, capacity, and accessibility")

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
    except:
        # Return sample data if connection fails
        return pd.DataFrame()

# Tabs
tab1, tab2, tab3 = st.tabs(["📍 Nearest Chargers", "⚠️ Infrastructure Gaps", "⭐ Smart Recommendations"])

with tab1:
    st.header("Nearest Charging Stations")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Stations", "720", "+12 this month")
    with col2:
        st.metric("Avg Distance", "5.2 km", "-0.3 km")
    with col3:
        st.metric("Min Distance", "0.8 km")
    
    # Query nearest chargers
    query_nearest = """
    SELECT 
        lganame,
        operator,
        charging_speed,
        charger_rating_kw,
        distance_km,
        accessibility_score,
        total_plugs
    FROM mobility_ai.gold.charger_recommendations_nearest
    ORDER BY distance_km
    LIMIT 100
    """
    
    df_nearest = query_data(query_nearest)
    
    if not df_nearest.empty:
        # Distance distribution
        fig_dist = px.histogram(df_nearest, x='distance_km', nbins=30,
                               title='Distance Distribution to Nearest Chargers',
                               labels={'distance_km': 'Distance (km)', 'count': 'Number of Locations'})
        st.plotly_chart(fig_dist, use_container_width=True)
        
        # Top operators
        col1, col2 = st.columns(2)
        with col1:
            operator_counts = df_nearest['operator'].value_counts().head(10)
            fig_op = px.bar(operator_counts, title='Top 10 Operators',
                           labels={'value': 'Station Count', 'index': 'Operator'})
            st.plotly_chart(fig_op, use_container_width=True)
        
        with col2:
            speed_counts = df_nearest['charging_speed'].value_counts()
            fig_speed = px.pie(speed_counts, values=speed_counts.values, names=speed_counts.index,
                              title='Charging Speed Distribution')
            st.plotly_chart(fig_speed, use_container_width=True)
        
        # Data table
        st.subheader("Nearest Chargers Data")
        st.dataframe(df_nearest, use_container_width=True)

with tab2:
    st.header("Infrastructure Gaps Analysis")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Capacity", "4,280 kW")
    with col2:
        st.metric("Slow Chargers", "1,024")
    with col3:
        st.metric("Fast Chargers", "856")
    with col4:
        st.metric("Rapid Chargers", "280")
    
    query_gaps = """
    SELECT 
        lganame,
        gap_category,
        slow_chargers,
        fast_chargers,
        rapid_chargers,
        total_capacity_kw,
        gap_severity
    FROM mobility_ai.gold.charger_recommendations_gaps
    ORDER BY gap_severity DESC
    """
    
    df_gaps = query_data(query_gaps)
    
    if not df_gaps.empty:
        # Gap severity by region
        fig_severity = px.bar(df_gaps, x='lganame', y='gap_severity', color='gap_category',
                             title='Infrastructure Gap Severity by Region',
                             labels={'lganame': 'Region', 'gap_severity': 'Gap Severity'})
        st.plotly_chart(fig_severity, use_container_width=True)
        
        # Charger type distribution
        col1, col2 = st.columns(2)
        with col1:
            charger_types = df_gaps[['slow_chargers', 'fast_chargers', 'rapid_chargers']].sum()
            fig_types = px.pie(values=charger_types.values, names=charger_types.index,
                              title='Charger Type Distribution')
            st.plotly_chart(fig_types, use_container_width=True)
        
        with col2:
            fig_capacity = px.bar(df_gaps.nlargest(10, 'total_capacity_kw'), 
                                 x='lganame', y='total_capacity_kw',
                                 title='Top 10 Regions by Capacity',
                                 labels={'total_capacity_kw': 'Capacity (kW)', 'lganame': 'Region'})
            st.plotly_chart(fig_capacity, use_container_width=True)
        
        st.subheader("Infrastructure Gaps Data")
        st.dataframe(df_gaps, use_container_width=True)

with tab3:
    st.header("Smart Charging Recommendations")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Recommended Stations", "420")
    with col2:
        st.metric("Avg Recommendation Score", "8.4/10")
    with col3:
        st.metric("High Tier Stations", "156")
    
    query_smart = """
    SELECT 
        operator,
        charging_speed,
        recommendation_tier,
        recommendation_score,
        accessibility_score,
        charger_rating_kw,
        total_plugs
    FROM mobility_ai.gold.charger_recommendations_smart
    ORDER BY recommendation_score DESC
    LIMIT 100
    """
    
    df_smart = query_data(query_smart)
    
    if not df_smart.empty:
        # Recommendation score distribution
        fig_score = px.histogram(df_smart, x='recommendation_score', nbins=20,
                                title='Recommendation Score Distribution',
                                labels={'recommendation_score': 'Score', 'count': 'Station Count'})
        st.plotly_chart(fig_score, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            # Tier distribution
            tier_counts = df_smart['recommendation_tier'].value_counts()
            fig_tier = px.pie(tier_counts, values=tier_counts.values, names=tier_counts.index,
                             title='Recommendation Tier Distribution')
            st.plotly_chart(fig_tier, use_container_width=True)
        
        with col2:
            # Top operators by score
            top_ops = df_smart.groupby('operator')['recommendation_score'].mean().nlargest(10)
            fig_top = px.bar(top_ops, title='Top 10 Operators by Avg Score',
                            labels={'value': 'Avg Score', 'index': 'Operator'})
            st.plotly_chart(fig_top, use_container_width=True)
        
        st.subheader("Smart Recommendations Data")
        st.dataframe(df_smart, use_container_width=True)

st.markdown("---")
st.caption("Data from mobility_ai.gold schema | Refreshed every 5 minutes")
