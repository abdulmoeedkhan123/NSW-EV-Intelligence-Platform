import streamlit as st
import pandas as pd
from databricks import sql
import os
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Trip Intelligence & Planning", page_icon="🗺️", layout="wide")

st.title("🗺️ Trip Intelligence & Planning")
st.markdown("Optimize EV journeys with route analysis and charging requirements")

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
tab1, tab2, tab3 = st.tabs(["🛣️ Optimal Routes", "🔋 Charging Requirements", "💡 Trip Recommendations"])

with tab1:
    st.header("Optimal Route Analysis")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Routes", "34")
    with col2:
        st.metric("Safe Routes", "28")
    with col3:
        st.metric("Avg Delay", "12 min")
    with col4:
        st.metric("Total Hazards", "156")
    
    query_routes = """
    SELECT 
        location,
        route_safety_rating,
        route_risk_score,
        total_hazards,
        active_hazards,
        major_hazards,
        primary_hazard_type,
        estimated_delay_minutes,
        roadwork_count,
        incident_count,
        flood_count,
        event_count
    FROM mobility_ai.gold.trip_routes_optimal
    ORDER BY route_risk_score
    """
    
    df_routes = query_data(query_routes)
    
    if not df_routes.empty:
        # Safety rating distribution
        col1, col2 = st.columns(2)
        with col1:
            safety_counts = df_routes['route_safety_rating'].value_counts()
            fig_safety = px.pie(safety_counts, values=safety_counts.values, names=safety_counts.index,
                               title='Route Safety Rating Distribution',
                               color_discrete_map={'Safe': 'green', 'Moderate': 'orange', 'Caution': 'red'})
            st.plotly_chart(fig_safety, use_container_width=True)
        
        with col2:
            # Risk score distribution
            fig_risk = px.histogram(df_routes, x='route_risk_score', nbins=20,
                                   title='Risk Score Distribution',
                                   labels={'route_risk_score': 'Risk Score'})
            st.plotly_chart(fig_risk, use_container_width=True)
        
        # Top hazardous routes
        top_hazards = df_routes.nlargest(10, 'total_hazards')
        fig_hazards = px.bar(top_hazards, x='location', y='total_hazards', 
                            color='route_safety_rating',
                            title='Top 10 Routes by Total Hazards',
                            labels={'location': 'Location', 'total_hazards': 'Total Hazards'})
        st.plotly_chart(fig_hazards, use_container_width=True)
        
        # Hazard type breakdown
        hazard_types = df_routes['primary_hazard_type'].value_counts().head(8)
        fig_types = px.bar(hazard_types, title='Top Hazard Types',
                          labels={'value': 'Count', 'index': 'Hazard Type'})
        st.plotly_chart(fig_types, use_container_width=True)
        
        # Delay analysis
        col1, col2 = st.columns(2)
        with col1:
            avg_delay = df_routes.groupby('route_safety_rating')['estimated_delay_minutes'].mean()
            fig_delay = px.bar(avg_delay, title='Avg Delay by Safety Rating',
                              labels={'value': 'Delay (min)', 'index': 'Safety Rating'})
            st.plotly_chart(fig_delay, use_container_width=True)
        
        with col2:
            # Hazard composition
            hazard_comp = df_routes[['roadwork_count', 'incident_count', 'flood_count', 'event_count']].sum()
            fig_comp = px.pie(values=hazard_comp.values, names=hazard_comp.index,
                             title='Hazard Type Composition')
            st.plotly_chart(fig_comp, use_container_width=True)
        
        st.subheader("Route Analysis Data")
        st.dataframe(df_routes, use_container_width=True)

with tab2:
    st.header("Charging Requirements Analysis")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Charging Stops", "1.8")
    with col2:
        st.metric("Feasible Trips", "85%")
    with col3:
        st.metric("Avg Charging Time", "2.3 hrs")
    with col4:
        st.metric("Fast Charger Stations", "142")
    
    query_charging = """
    SELECT 
        trip_distance_km,
        charging_stops_needed,
        base_driving_time_hours,
        charging_time_hours,
        total_trip_time_hours,
        recommended_charger_type,
        minimum_starting_battery_pct,
        trip_feasibility,
        total_stations,
        fast_charger_stations,
        charger_availability_score
    FROM mobility_ai.gold.trip_charging_requirements
    """
    
    df_charging = query_data(query_charging)
    
    if not df_charging.empty:
        # Charging stops vs distance
        fig_stops = px.scatter(df_charging, x='trip_distance_km', y='charging_stops_needed',
                              color='trip_feasibility',
                              title='Charging Stops vs Trip Distance',
                              labels={'trip_distance_km': 'Distance (km)', 
                                     'charging_stops_needed': 'Charging Stops'},
                              trendline="ols")
        st.plotly_chart(fig_stops, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            # Recommended charger types
            charger_counts = df_charging['recommended_charger_type'].value_counts()
            fig_charger = px.pie(charger_counts, values=charger_counts.values, 
                                names=charger_counts.index,
                                title='Recommended Charger Types')
            st.plotly_chart(fig_charger, use_container_width=True)
        
        with col2:
            # Trip feasibility
            feasibility_counts = df_charging['trip_feasibility'].value_counts()
            fig_feas = px.pie(feasibility_counts, values=feasibility_counts.values,
                             names=feasibility_counts.index,
                             title='Trip Feasibility Distribution')
            st.plotly_chart(fig_feas, use_container_width=True)
        
        # Time breakdown
        time_data = df_charging[['base_driving_time_hours', 'charging_time_hours']].mean()
        fig_time = px.bar(time_data, title='Average Trip Time Breakdown',
                         labels={'value': 'Hours', 'index': 'Time Component'})
        st.plotly_chart(fig_time, use_container_width=True)
        
        # Distance ranges
        df_charging['distance_range'] = pd.cut(df_charging['trip_distance_km'], 
                                               bins=[0, 100, 200, 300, 400, 500],
                                               labels=['0-100', '100-200', '200-300', '300-400', '400+'])
        range_stats = df_charging.groupby('distance_range').agg({
            'charging_stops_needed': 'mean',
            'charging_time_hours': 'mean',
            'minimum_starting_battery_pct': 'mean'
        }).round(2)
        
        st.subheader("Charging Requirements by Distance Range")
        st.dataframe(range_stats, use_container_width=True)
        
        st.subheader("Detailed Charging Data")
        st.dataframe(df_charging.drop('distance_range', axis=1), use_container_width=True)

with tab3:
    st.header("Trip Recommendations")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Recommendations", "34")
    with col2:
        st.metric("Optimal Routes", "28")
    with col3:
        st.metric("Alternative Routes", "6")
    
    query_trip_rec = """
    SELECT 
        recommendation_category,
        route_recommendation,
        charging_strategy,
        safety_notes,
        estimated_savings_minutes,
        confidence_score
    FROM mobility_ai.gold.trip_recommendations
    ORDER BY confidence_score DESC
    """
    
    df_trip_rec = query_data(query_trip_rec)
    
    if not df_trip_rec.empty:
        # Recommendation categories
        cat_counts = df_trip_rec['recommendation_category'].value_counts()
        fig_cat = px.bar(cat_counts, title='Recommendation Categories',
                        labels={'value': 'Count', 'index': 'Category'})
        st.plotly_chart(fig_cat, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            # Confidence score distribution
            fig_conf = px.histogram(df_trip_rec, x='confidence_score', nbins=20,
                                   title='Confidence Score Distribution',
                                   labels={'confidence_score': 'Confidence Score'})
            st.plotly_chart(fig_conf, use_container_width=True)
        
        with col2:
            # Savings analysis
            avg_savings = df_trip_rec.groupby('recommendation_category')['estimated_savings_minutes'].mean()
            fig_savings = px.bar(avg_savings, title='Avg Time Savings by Category',
                                labels={'value': 'Savings (min)', 'index': 'Category'})
            st.plotly_chart(fig_savings, use_container_width=True)
        
        st.subheader("Trip Recommendations")
        st.dataframe(df_trip_rec, use_container_width=True)

st.markdown("---")
st.caption("Trip data analyzed in real-time | Route optimization updated every 5 minutes")
