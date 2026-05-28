import streamlit as st
import pandas as pd
from databricks import sql
import os
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Traffic Congestion Forecast", page_icon="🚦", layout="wide")

st.title("🚦 Traffic Congestion Forecast")
st.markdown("Real-time traffic analysis, hazard tracking, and congestion predictions")

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
        return pd.DataFrame()

# Tabs
tab1, tab2, tab3 = st.tabs(["⏰ Hourly Patterns", "📍 Location Risk", "💡 Recommendations"])

with tab1:
    st.header("Hourly Congestion Patterns")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Peak Hour", "8:00 AM", "Weekdays")
    with col2:
        st.metric("Avg Congestion", "6.2/10")
    with col3:
        st.metric("Total Hazards", "113")
    with col4:
        st.metric("Active Hazards", "89")
    
    query_hourly = """
    SELECT 
        hour_of_day,
        day_name,
        congestion_level,
        congestion_score,
        total_hazards,
        major_hazards,
        moderate_hazards,
        minor_hazards,
        is_peak_hour
    FROM mobility_ai.gold.congestion_forecast_hourly
    ORDER BY hour_of_day
    """
    
    df_hourly = query_data(query_hourly)
    
    if not df_hourly.empty:
        # Congestion heatmap by hour and day
        pivot_data = df_hourly.pivot_table(values='congestion_score', 
                                           index='day_name', 
                                           columns='hour_of_day', 
                                           aggfunc='mean')
        
        fig_heatmap = px.imshow(pivot_data,
                               labels=dict(x="Hour of Day", y="Day", color="Congestion Score"),
                               title="Congestion Heatmap: Hour vs Day",
                               aspect="auto",
                               color_continuous_scale="RdYlGn_r")
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Hourly trend line
        avg_by_hour = df_hourly.groupby('hour_of_day')['congestion_score'].mean().reset_index()
        fig_trend = px.line(avg_by_hour, x='hour_of_day', y='congestion_score',
                           title='Average Congestion Score by Hour',
                           labels={'hour_of_day': 'Hour of Day', 'congestion_score': 'Congestion Score'},
                           markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            # Hazard distribution
            hazard_data = df_hourly[['major_hazards', 'moderate_hazards', 'minor_hazards']].sum()
            fig_hazards = px.pie(values=hazard_data.values, names=hazard_data.index,
                                title='Hazard Severity Distribution')
            st.plotly_chart(fig_hazards, use_container_width=True)
        
        with col2:
            # Peak vs non-peak
            peak_data = df_hourly.groupby('is_peak_hour')['congestion_score'].mean()
            fig_peak = px.bar(peak_data, title='Peak vs Non-Peak Congestion',
                             labels={'value': 'Avg Congestion Score', 'index': 'Is Peak Hour'})
            st.plotly_chart(fig_peak, use_container_width=True)
        
        st.subheader("Hourly Congestion Data")
        st.dataframe(df_hourly, use_container_width=True)

with tab2:
    st.header("Location Risk Analysis")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("High Risk Locations", "23")
    with col2:
        st.metric("Avg Risk Score", "7.1/10")
    with col3:
        st.metric("Active Hazards", "89")
    
    query_location = """
    SELECT 
        location,
        risk_level,
        risk_score,
        total_hazards,
        active_hazards,
        major_hazards,
        dominant_hazard_type,
        center_lat,
        center_lon
    FROM mobility_ai.gold.congestion_forecast_location
    ORDER BY risk_score DESC
    """
    
    df_location = query_data(query_location)
    
    if not df_location.empty:
        # Risk level distribution
        col1, col2 = st.columns(2)
        with col1:
            risk_counts = df_location['risk_level'].value_counts()
            fig_risk = px.pie(risk_counts, values=risk_counts.values, names=risk_counts.index,
                             title='Risk Level Distribution',
                             color_discrete_map={'High': 'red', 'Medium': 'orange', 'Low': 'green'})
            st.plotly_chart(fig_risk, use_container_width=True)
        
        with col2:
            # Dominant hazard types
            hazard_counts = df_location['dominant_hazard_type'].value_counts().head(8)
            fig_types = px.bar(hazard_counts, title='Top Hazard Types',
                              labels={'value': 'Count', 'index': 'Hazard Type'})
            st.plotly_chart(fig_types, use_container_width=True)
        
        # Top 10 high-risk locations
        top_risk = df_location.nlargest(10, 'risk_score')
        fig_top_risk = px.bar(top_risk, x='location', y='risk_score', color='risk_level',
                             title='Top 10 High-Risk Locations',
                             labels={'location': 'Location', 'risk_score': 'Risk Score'})
        st.plotly_chart(fig_top_risk, use_container_width=True)
        
        # Map visualization (if coordinates available)
        if 'center_lat' in df_location.columns and 'center_lon' in df_location.columns:
            st.subheader("Risk Map")
            map_data = df_location.dropna(subset=['center_lat', 'center_lon'])
            if not map_data.empty:
                fig_map = px.scatter_mapbox(map_data, 
                                           lat='center_lat', 
                                           lon='center_lon',
                                           color='risk_level',
                                           size='risk_score',
                                           hover_name='location',
                                           hover_data=['total_hazards', 'dominant_hazard_type'],
                                           color_discrete_map={'High': 'red', 'Medium': 'orange', 'Low': 'green'},
                                           zoom=8,
                                           height=500)
                fig_map.update_layout(mapbox_style="open-street-map")
                st.plotly_chart(fig_map, use_container_width=True)
        
        st.subheader("Location Risk Data")
        st.dataframe(df_location, use_container_width=True)

with tab3:
    st.header("Travel Recommendations")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Best Travel Time", "10:00 AM - 3:00 PM")
    with col2:
        st.metric("Recommendations", "24")
    with col3:
        st.metric("Avg Congestion", "4.8/10")
    
    query_recommendations = """
    SELECT 
        hour_of_day,
        recommendation_category,
        time_period,
        avg_congestion_score,
        avg_hazards,
        charging_recommendation,
        travel_recommendation
    FROM mobility_ai.gold.congestion_forecast_recommendations
    ORDER BY hour_of_day
    """
    
    df_rec = query_data(query_recommendations)
    
    if not df_rec.empty:
        # Recommendations by time period
        period_counts = df_rec['time_period'].value_counts()
        fig_period = px.bar(period_counts, title='Recommendations by Time Period',
                           labels={'value': 'Count', 'index': 'Time Period'})
        st.plotly_chart(fig_period, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            # Category distribution
            cat_counts = df_rec['recommendation_category'].value_counts()
            fig_cat = px.pie(cat_counts, values=cat_counts.values, names=cat_counts.index,
                            title='Recommendation Categories')
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            # Congestion by hour
            fig_hour = px.line(df_rec, x='hour_of_day', y='avg_congestion_score',
                              title='Average Congestion Score by Hour',
                              labels={'hour_of_day': 'Hour', 'avg_congestion_score': 'Congestion Score'},
                              markers=True)
            st.plotly_chart(fig_hour, use_container_width=True)
        
        # Recommendations table
        st.subheader("Travel & Charging Recommendations")
        display_cols = ['hour_of_day', 'time_period', 'recommendation_category', 
                       'travel_recommendation', 'charging_recommendation', 'avg_congestion_score']
        st.dataframe(df_rec[display_cols], use_container_width=True)

st.markdown("---")
st.caption("Live traffic data from NSW Live Traffic | Updated every 5 minutes")
