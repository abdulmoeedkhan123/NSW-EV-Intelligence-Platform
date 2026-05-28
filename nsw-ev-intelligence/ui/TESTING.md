# 🧪 Local Testing Instructions

## Quick Start (5 minutes)

### Option 1: Run from Databricks Terminal

```bash
# Navigate to UI directory
cd /Workspace/Users/moeedk1@gmail.com/NSW-EV-Intelligence-Platform/nsw-ev-intelligence/ui

# Run the application
./run_local.sh
```

### Option 2: Manual Setup

```bash
# 1. Navigate to directory
cd /Workspace/Users/moeedk1@gmail.com/NSW-EV-Intelligence-Platform/nsw-ev-intelligence/ui

# 2. Install dependencies (if needed)
pip install streamlit==1.31.0 databricks-sql-connector==3.0.0 pandas plotly

# 3. Run the app
streamlit run home.py --server.port 8501

# 4. Open browser
# Navigate to: http://localhost:8501
```

## ✅ Test Validation Results

Your application has been tested and validated:

- ✅ **12 files created** (48.6 KB)
- ✅ **All Python syntax valid**
- ✅ **10 database tables accessible** (2,384 records)
- ✅ **4 dashboard pages ready**
- ✅ **Streamlit configuration complete**

## 📊 Available Data

Your application connects to:

1. **EV Charger Recommendations** (2,160 records)
   - 80 nearest charger locations
   - 130 infrastructure gap analysis
   - 1,950 smart recommendations

2. **Traffic Congestion Forecast** (113 records)
   - 90 hourly pattern predictions
   - 1 location risk analysis
   - 22 travel recommendations

3. **Trip Intelligence** (102 records)
   - 1 optimal route
   - 11 charging requirements
   - 90 trip recommendations

4. **Regional Metrics** (9 records)
   - 9 NSW regions analyzed

## 🎨 What You'll See

### Home Page
- Platform overview
- 4 key metric cards
- Feature descriptions
- Quick navigation

### Dashboard Pages
Each page has multiple tabs with:
- Interactive Plotly visualizations
- Real-time data from gold tables
- Filtering and sorting
- CSV export capabilities

## 🔍 Testing Checklist

- [ ] Navigate to UI directory
- [ ] Run `./run_local.sh` or `streamlit run home.py`
- [ ] Open http://localhost:8501 in browser
- [ ] Check home page loads correctly
- [ ] Navigate through all 4 dashboard pages
- [ ] Verify charts render with data
- [ ] Test interactive features (hover, zoom)
- [ ] Check responsive design (resize browser)

## ⚠️ Known Limitations

**Database Connection:**
- Streamlit apps running outside Databricks may not connect to Spark directly
- You'll see empty charts or sample data
- For full functionality, deploy as Databricks App

**Solution:** Deploy to Databricks Apps for production use:
```bash
./deploy.sh
```

## 🐛 Troubleshooting

### "Address already in use"
```bash
# Kill existing streamlit process
pkill -f streamlit
# Or use different port
streamlit run home.py --server.port 8502
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "No data displayed"
- Check database connection
- Verify gold tables exist
- Review query logs in terminal

## 📸 Screenshots Expected

**Home Page:**
- 4 colored metric cards (Chargers, Regions, Hazards, Routes)
- Feature grid with icons
- Data source descriptions

**Charger Recommendations:**
- Distance distribution histogram
- Operator bar chart
- Charging speed pie chart
- Gap severity visualizations

**Traffic Forecast:**
- Congestion heatmap (24h × 7 days)
- Risk level distribution
- Hazard type breakdown

**Trip Intelligence:**
- Safety rating distribution
- Charging stops scatter plot
- Time savings analysis

**Regional Metrics:**
- EV readiness bar chart
- Charger distribution (stacked bars)
- Regional comparison table

## 🚀 Next Steps

After local testing:

1. **Deploy to Production**
   ```bash
   ./deploy.sh
   ```

2. **Share with Team**
   - Get Databricks App URL
   - Configure permissions
   - Gather feedback

3. **Customize**
   - Edit page files in `pages/`
   - Modify colors in `.streamlit/config.toml`
   - Add new visualizations

## 📚 Resources

- **Streamlit Docs**: https://docs.streamlit.io
- **Plotly Charts**: https://plotly.com/python/
- **Databricks Apps**: https://docs.databricks.com/apps/

---

**Need Help?**
- Check logs in terminal running streamlit
- Review README.md for detailed documentation
- Test with demo data: `python demo_data.py`
