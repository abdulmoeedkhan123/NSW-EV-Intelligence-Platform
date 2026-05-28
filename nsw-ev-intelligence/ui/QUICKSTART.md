# 🚀 Quick Start Guide

## Fastest Way to See Your UI (5 minutes)

### Step 1: Test Locally (No Setup Required)

```bash
# From the ui directory
cd /Workspace/Users/moeedk1@gmail.com/NSW-EV-Intelligence-Platform/nsw-ev-intelligence/ui

# Install dependencies (one-time)
pip install streamlit databricks-sql-connector pandas plotly

# Run the app
streamlit run home.py
```

Your app will open in your browser at `http://localhost:8501`

### Step 2: Deploy to Databricks Apps

```bash
# Make sure Databricks CLI is configured
databricks configure --token

# Deploy the app
./deploy.sh
```

## 📸 What You'll See

### Home Page
- **4 Key Metrics Cards**: EV Chargers, Regions, Hazards, Routes
- **Feature Grid**: Overview of all 4 modules
- **Data Sources**: NSW EV, Traffic, Fuel data

### Page 1: EV Charger Recommendations 🔌
- **Tab 1 - Nearest Chargers**: 
  - Distance distribution histogram
  - Top 10 operators bar chart
  - Charging speed pie chart
  - Full data table with 720 stations

- **Tab 2 - Infrastructure Gaps**:
  - Gap severity by region
  - Charger type distribution
  - Top 10 regions by capacity
  - Regional gap analysis table

- **Tab 3 - Smart Recommendations**:
  - Recommendation score distribution
  - Tier distribution pie chart
  - Top operators by score
  - Ranked recommendations table

### Page 2: Traffic Congestion Forecast 🚦
- **Tab 1 - Hourly Patterns**:
  - Congestion heatmap (hour × day)
  - Average congestion by hour line chart
  - Hazard severity pie chart
  - Peak vs non-peak comparison

- **Tab 2 - Location Risk**:
  - Risk level distribution
  - Top hazard types
  - High-risk locations bar chart
  - Interactive map with risk markers

- **Tab 3 - Recommendations**:
  - Recommendations by time period
  - Category distribution
  - Congestion by hour trends
  - Travel & charging advice table

### Page 3: Trip Intelligence & Planning 🗺️
- **Tab 1 - Optimal Routes**:
  - Safety rating pie chart
  - Risk score distribution
  - Top 10 hazardous routes
  - Hazard type breakdown
  - Delay analysis by safety rating

- **Tab 2 - Charging Requirements**:
  - Charging stops vs distance scatter plot
  - Recommended charger types
  - Trip feasibility distribution
  - Time breakdown (driving vs charging)
  - Requirements by distance range

- **Tab 3 - Trip Recommendations**:
  - Recommendation categories
  - Confidence score distribution
  - Time savings by category
  - Detailed recommendations table

### Page 4: Regional Infrastructure Metrics 📊
- **EV Readiness Scores**: Bar chart for all 9 NSW regions
- **Charger Distribution**: Stacked bar chart by region
- **Capacity Analysis**: Total and average capacity charts
- **EV vs Fuel**: Side-by-side comparison
- **Comparison Table**: Color-coded readiness scores
- **CSV Export**: Download full dataset

## 🎨 UI Design Features

- **Color Scheme**: Professional blue/purple gradients
- **Responsive Layout**: Works on desktop, tablet, mobile
- **Interactive Charts**: Hover for details, zoom, pan
- **Live Data**: 5-minute cache refresh
- **Custom Styling**: Gradient metric cards

## 🔧 Customization

### Change Colors
Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1E88E5"  # Change this
backgroundColor = "#FFFFFF"
```

### Add New Visualizations
Edit any page file in `pages/`:
```python
# Add new chart
fig = px.bar(df, x='column', y='value')
st.plotly_chart(fig, use_container_width=True)
```

### Modify Data Queries
Update SQL queries in page files:
```python
query = """
    SELECT * FROM your_table
    WHERE condition = 'value'
"""
df = query_data(query)
```

## 🐛 Common Issues

**"Connection Error"**
- Check environment variables are set
- Verify SQL Warehouse is running
- Test with: `databricks sql execute "SELECT 1"`

**"Empty Charts"**
- Verify gold tables exist
- Check data pipeline ran successfully
- Test query: `SELECT COUNT(*) FROM mobility_ai.gold.charger_recommendations_nearest`

**"Module Not Found"**
- Install requirements: `pip install -r requirements.txt`
- Verify Python 3.8+: `python --version`

## 📊 Sample Data Counts

Your application visualizes:
- **2,160 charger records** (720 × 3 recommendation types)
- **113 congestion forecast records**
- **102 trip planning records**
- **9 regional metric records**

Total: **2,384 analyzed data points** across 10 gold tables

## 🎯 Next Steps

1. ✅ Test locally with `streamlit run home.py`
2. ✅ Explore all 4 pages and tabs
3. ✅ Deploy to Databricks Apps with `./deploy.sh`
4. ✅ Share with stakeholders
5. ✅ Add custom analysis based on feedback

## 📞 Need Help?

Check these resources:
- `README.md` - Full documentation
- Streamlit docs: https://docs.streamlit.io
- Databricks Apps: https://docs.databricks.com/apps

---
**Built with ❤️ for NSW EV Intelligence Platform**
