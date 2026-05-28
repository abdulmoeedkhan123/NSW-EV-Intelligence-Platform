# NSW EV Intelligence Platform - Streamlit UI

A comprehensive web application for NSW electric vehicle infrastructure analysis, traffic forecasting, and trip planning.

## 🚀 Features

### 🔌 EV Charger Recommendations
- **Nearest Chargers**: Discover charging stations by location with distance and accessibility metrics
- **Infrastructure Gaps**: Identify underserved areas and capacity shortfalls
- **Smart Recommendations**: AI-powered station suggestions based on multiple factors

### 🚦 Traffic Congestion Forecast
- **Hourly Patterns**: Congestion heatmaps by hour and day of week
- **Location Risk Analysis**: High-risk areas with hazard tracking (roadworks, incidents, floods)
- **Travel Recommendations**: Optimal travel times and charging strategies

### 🗺️ Trip Intelligence & Planning
- **Optimal Routes**: Safe route analysis with hazard awareness
- **Charging Requirements**: Calculate stops needed based on trip distance
- **Trip Feasibility**: Assess journey viability for EV travel

### 📊 Regional Infrastructure Metrics
- **Regional Comparison**: EV readiness scores across 9 NSW regions
- **Charger Distribution**: Slow, fast, rapid, and ultra-rapid charger analysis
- **Capacity Analysis**: Total and average capacity metrics
- **EV vs Fuel**: Infrastructure comparison with traditional fuel stations

## 📊 Data Sources

The platform analyzes 10 gold-layer tables from the mobility_ai catalog:

**EV Charger Data (3 tables, 2,160 records)**
- `charger_recommendations_nearest`: Distance-based station recommendations
- `charger_recommendations_gaps`: Infrastructure gap analysis
- `charger_recommendations_smart`: AI-scored station recommendations

**Traffic & Congestion (3 tables, 113 records)**
- `congestion_forecast_hourly`: Hour/day congestion predictions
- `congestion_forecast_location`: Location-based risk scoring
- `congestion_forecast_recommendations`: Travel timing suggestions

**Trip Planning (3 tables, 102 records)**
- `trip_routes_optimal`: Route safety and hazard analysis
- `trip_charging_requirements`: Charging stop calculations
- `trip_recommendations`: Journey optimization suggestions

**Regional Metrics (1 table, 9 records)**
- `regional_infrastructure_metrics`: Regional EV readiness metrics

## 🛠️ Setup & Deployment

### Option 1: Databricks Apps (Recommended)

1. **Navigate to the UI directory**
   ```bash
   cd /Workspace/Users/<your-email>/NSW-EV-Intelligence-Platform/nsw-ev-intelligence/ui
   ```

2. **Deploy as Databricks App**
   - The `app.yml` is already configured
   - Deploy using Databricks CLI or UI
   ```bash
   databricks apps create nsw-ev-platform
   databricks apps deploy nsw-ev-platform ./
   ```

3. **Set Environment Variables**
   - `DATABRICKS_WORKSPACE_URL`: Your workspace URL
   - `DATABRICKS_WAREHOUSE_ID`: SQL Warehouse ID (or use 'auto')
   - `DATABRICKS_TOKEN`: Access token (automatically provided in Databricks Apps)

### Option 2: Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
   export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
   export DATABRICKS_TOKEN="your-access-token"
   ```

3. **Run the app**
   ```bash
   streamlit run home.py --server.port 8080
   ```

4. **Access the UI**
   - Open browser to `http://localhost:8080`

## 📁 Project Structure

```
ui/
├── app.yml                          # Databricks App configuration
├── requirements.txt                 # Python dependencies
├── home.py                         # Main landing page
└── pages/
    ├── 1_🔌_Charger_Recommendations.py
    ├── 2_🚦_Traffic_Forecast.py
    ├── 3_🗺️_Trip_Intelligence.py
    └── 4_📊_Regional_Metrics.py
```

## 🎨 UI Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Interactive Visualizations**: Plotly charts with hover details
- **Real-time Data**: 5-minute cache refresh for live updates
- **Data Export**: Download CSV for offline analysis
- **Custom Styling**: Professional gradient cards and color schemes

## 🔒 Security

- All database connections use secure Databricks SQL connectors
- Token-based authentication
- No sensitive data cached in browser
- Environment variables for credentials

## 📈 Performance

- Query caching with 5-minute TTL
- Connection pooling for database efficiency
- Lazy loading of visualizations
- Optimized data aggregations

## 🐛 Troubleshooting

**Connection Errors**
- Verify environment variables are set correctly
- Check SQL Warehouse is running
- Confirm access token has proper permissions

**Empty Data**
- Ensure gold layer tables exist in `mobility_ai.gold` schema
- Verify data pipeline has completed successfully
- Check table permissions

**Slow Performance**
- Increase SQL Warehouse size
- Adjust cache TTL in `@st.cache_data` decorator
- Consider materializing complex aggregations

## 📚 Documentation

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Databricks Apps Guide](https://docs.databricks.com/en/apps/index.html)
- [Plotly Python Documentation](https://plotly.com/python/)

## 🤝 Contributing

This is a demonstration platform. For production use:
1. Add user authentication
2. Implement role-based access control
3. Add monitoring and logging
4. Create automated tests
5. Set up CI/CD pipeline

## 📄 License

This project is part of the NSW EV Intelligence Platform.

## 🙋 Support

For issues or questions:
- Check the troubleshooting section
- Review Databricks documentation
- Contact your platform administrator
