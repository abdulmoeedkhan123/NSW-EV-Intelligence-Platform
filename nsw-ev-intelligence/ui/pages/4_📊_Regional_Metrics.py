import streamlit as st
import pandas as pd
from databricks import sql
import os
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Regional Infrastructure Metrics", page_icon="📊", layout="wide")

st.title("📊 Regional Infrastructure Metrics")
st.markdown("Compare EV infrastructure and readiness across NSW regions")

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

query_regional = """
SELECT 
    region,
    ev_station_count,
    valid_locations,
    total_capacity_kw,
    avg_capacity_kw,
    max_capacity_kw,
    slow_chargers,
    fast_chargers,
    rapid_chargers,
    ultra_rapid_chargers,
    fuel_station_count_nsw,
    avg_regular_unleaded_price,
    avg_diesel_price,
    avg_lpg_price,
    ev_readiness_score
FROM mobility_ai.gold.regional_infrastructure_metrics
ORDER BY ev_readiness_score DESC
"""

df_regional = query_data(query_regional)

if not df_regional.empty:
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total EV Stations", f"{df_regional['ev_station_count'].sum():,}")
    with col2:
        st.metric("Total Capacity", f"{df_regional['total_capacity_kw'].sum():,.0f} kW")
    with col3:
        st.metric("Avg Readiness Score", f"{df_regional['ev_readiness_score'].mean():.1f}")
    with col4:
        st.metric("Regions Analyzed", len(df_regional))
    
    st.divider()
    
    # EV Readiness by Region
    st.header("EV Readiness Scores")
    fig_readiness = px.bar(df_regional.sort_values('ev_readiness_score', ascending=False),
                          x='region', y='ev_readiness_score',
                          title='EV Readiness Score by Region',
                          labels={'region': 'Region', 'ev_readiness_score': 'Readiness Score'},
                          color='ev_readiness_score',
                          color_continuous_scale='viridis')
    st.plotly_chart(fig_readiness, use_container_width=True)
    
    # Charger distribution
    st.header("Charger Type Distribution")
    col1, col2 = st.columns(2)
    
    with col1:
        # Stacked bar chart
        charger_cols = ['slow_chargers', 'fast_chargers', 'rapid_chargers', 'ultra_rapid_chargers']
        fig_stack = go.Figure()
        for col in charger_cols:
            fig_stack.add_trace(go.Bar(
                name=col.replace('_', ' ').title(),
                x=df_regional['region'],
                y=df_regional[col]
            ))
        fig_stack.update_layout(barmode='stack', title='Charger Types by Region')
        st.plotly_chart(fig_stack, use_container_width=True)
    
    with col2:
        # Total charger pie chart
        total_chargers = df_regional[charger_cols].sum()
        fig_pie = px.pie(values=total_chargers.values, names=total_chargers.index,
                        title='Overall Charger Type Distribution')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Capacity analysis
    st.header("Capacity Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_total_cap = px.bar(df_regional.sort_values('total_capacity_kw', ascending=False),
                              x='region', y='total_capacity_kw',
                              title='Total Capacity by Region (kW)',
                              labels={'total_capacity_kw': 'Total Capacity (kW)'})
        st.plotly_chart(fig_total_cap, use_container_width=True)
    
    with col2:
        fig_avg_cap = px.bar(df_regional.sort_values('avg_capacity_kw', ascending=False),
                            x='region', y='avg_capacity_kw',
                            title='Average Capacity per Station (kW)',
                            labels={'avg_capacity_kw': 'Avg Capacity (kW)'})
        st.plotly_chart(fig_avg_cap, use_container_width=True)
    
    # EV vs Fuel stations
    st.header("EV vs Traditional Fuel Infrastructure")
    col1, col2 = st.columns(2)
    
    with col1:
        comparison_data = pd.DataFrame({
            'Region': df_regional['region'],
            'EV Stations': df_regional['ev_station_count'],
            'Fuel Stations': df_regional['fuel_station_count_nsw']
        })
        
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Bar(name='EV Stations', x=comparison_data['Region'], 
                                    y=comparison_data['EV Stations']))
        fig_compare.add_trace(go.Bar(name='Fuel Stations', x=comparison_data['Region'], 
                                    y=comparison_data['Fuel Stations']))
        fig_compare.update_layout(barmode='group', title='EV vs Fuel Stations by Region')
        st.plotly_chart(fig_compare, use_container_width=True)
    
    with col2:
        # Fuel price comparison
        fuel_prices = df_regional[['avg_regular_unleaded_price', 'avg_diesel_price', 'avg_lpg_price']].mean()
        fig_fuel = px.bar(fuel_prices, title='Average Fuel Prices Across NSW',
                         labels={'value': 'Price ($)', 'index': 'Fuel Type'})
        st.plotly_chart(fig_fuel, use_container_width=True)
    
    # Regional comparison table
    st.header("Regional Comparison Table")
    
    # Calculate additional metrics
    df_regional['charger_density'] = (df_regional['ev_station_count'] / 
                                      df_regional['valid_locations']).round(2)
    df_regional['ultra_rapid_ratio'] = (df_regional['ultra_rapid_chargers'] / 
                                        df_regional['ev_station_count'] * 100).round(1)
    
    display_cols = ['region', 'ev_station_count', 'total_capacity_kw', 'avg_capacity_kw',
                   'slow_chargers', 'fast_chargers', 'rapid_chargers', 'ultra_rapid_chargers',
                   'charger_density', 'ultra_rapid_ratio', 'ev_readiness_score']
    
    st.dataframe(df_regional[display_cols].style.background_gradient(
        subset=['ev_readiness_score'], cmap='RdYlGn'
    ), use_container_width=True)
    
    # Insights
    st.header("🔍 Key Insights")
    
    best_region = df_regional.loc[df_regional['ev_readiness_score'].idxmax(), 'region']
    most_stations = df_regional.loc[df_regional['ev_station_count'].idxmax(), 'region']
    highest_capacity = df_regional.loc[df_regional['total_capacity_kw'].idxmax(), 'region']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success(f"**Most EV-Ready Region**  
{best_region}")
    with col2:
        st.info(f"**Most EV Stations**  
{most_stations}")
    with col3:
        st.warning(f"**Highest Capacity**  
{highest_capacity}")
    
    # Full data download
    st.header("📥 Export Data")
    csv = df_regional.to_csv(index=False)
    st.download_button(
        label="Download Regional Metrics CSV",
        data=csv,
        file_name="nsw_regional_infrastructure_metrics.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption("Regional data aggregated from multiple sources | Updated daily")
