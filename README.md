# Nigeria Schistosomiasis Supply Chain Analytics Platform

**An integrated Node.js web application for preventive chemotherapy quantification**

---

## 🎯 Overview

This platform provides supply chain analytics for Nigeria's schistosomiasis control programme, featuring:

<!-- - **ARIMA Forecasting**: Predictive modeling of future supply needs (2025-2027) -->
- **Supply-Demand Matching**: Real-time integration of procurement and treatment data
- **Interactive Geospatial Visualization**: Choropleth maps showing endemicity and coverage
- **Data-Driven Insights**: KPIs, trends, and strategic recommendations

## 📊 Key Features

<!-- ### 1. **Supply Chain Snapshot**
- ARIMA(1,1,1) supply forecasting model
- Lead time analysis and procurement tracking
- Supply adequacy metrics and gap analysis
- Real-time procurement order monitoring -->

### 1. **National Dashboard**
- Treatment coverage trends (2020-2024)
- Endemicity distribution across 774 LGAs
- Population-level metrics and KPIs
- State-level priority analysis

### 2. **Interactive Map View**
- Leaflet-based choropleth mapping
- Multi-layer visualization (endemicity, coverage, priority)
- Click-through LGA details
- Real-time data tooltips

<!-- ### 3. **Forecast Analysis**
- 3-year supply and demand projections
- Confidence intervals and scenario planning
- Strategic recommendations based on forecasts
- Detailed forecast breakdowns -->

## 🔧 Technical Stack

**Backend:**
- Node.js with Express.js
- RESTful API architecture

**Data Processing:**
- Python 3.12 with pandas, numpy
- GeoPandas for geospatial processing
<!-- - Statsmodels for ARIMA forecasting
- Scikit-learn for trend analysis -->

**Frontend:**
- HTML5, CSS3 (ESPEN-themed)
- Chart.js for data visualization
- Leaflet.js for interactive maps
- Vanilla JavaScript (no framework overhead)

**Data Formats:**
- JSON for API responses
- GeoJSON for spatial data
- CSV for raw data input

## 📁 Project Structure

```
nigeria-sch-supply-chain/
│
├── data/
│   ├── demand_data.json              # Processed ESPEN data
│   ├── supply_data.json              # Procurement orders
│   ├── supply_demand_integrated.json # Annual projection
│   ├── nigeria_iu_geojson.json       # IU-level boundaries + data
│   ├── nigeria_states_geojson.json   # State-level aggregation
│   ├── supply_chain_metrics.json     # KPIs
│   ├── priority_lgas.json            # Top 100 priority LGAs
│   └── state_summary.json            # State statistics
│
├── public/
│   └── css/
│       └── espen-theme.css           # ESPEN styling
│
├── server/
│   └── app.js                        # Express server
│
├── views/
│   ├── index.html                    # National dashboard
│   ├── supply-chain.html             # Supply chain snapshot
│   ├── map.html                      # Interactive map
│   └── forecast.html                 # Forecast analysis
│
├── process_supply_chain_data.py      # Data processing script
├── package.json
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Node.js 14+ and npm
- Python 3.8+ with pip

### Installation

1. **Install Python Dependencies**
```bash
pip3 install pandas openpyxl numpy geopandas shapely statsmodels scikit-learn
```

2. **Process the Data**
```bash
python3 process_supply_chain_data.py
```

This will:
- Load ESPEN SCH data (demand side)
- Load NTDeliver procurement orders (supply side)
- Integrate supply and demand by year
<!-- - Run ARIMA forecasting for supply (2025-2027)
- Generate demand forecasts using trend analysis -->
- Convert shapefiles to GeoJSON
- Calculate all metrics and indicators

3. **Install Node.js Dependencies**
```bash
cd webapp
npm install
```

4. **Start the Server**
```bash
npm start
```

5. **Open Browser**
```
http://localhost:3000
```

## 📊 Data Flow

```
Raw Data Sources
      ↓
  [Python ETL]
  - Data cleaning
  <!-- - ARIMA forecasting -->
  - Geospatial conversion
  - Metric calculation
      ↓
  [JSON Files]
      ↓
  [Node.js API]
      ↓
  [Web Interface]
  - Dashboards
  - Charts
  - Maps
  - Forecasts
```

<!-- ## 🔍 ARIMA Forecasting Methodology

**Model:** ARIMA(1,1,1)

**Training Data:** 
- Historical procurement orders (2010-2025)
- 16 years of supply data

**Forecast Period:** 2025-2027 (3 years)

**Key Parameters:**
- p=1 (autoregressive order)
- d=1 (degree of differencing)
- q=1 (moving average order)

**Confidence Intervals:** ±15% based on historical variance

**Model Validation:**
- ADF test for stationarity
- AIC and BIC for model selection
- Visual inspection of residuals -->

## 📈 Key Metrics

### Supply Chain KPIs
- **Total Procurement Orders:** 23 (2010-2025)
- **Total Tablets Supplied:** 346M
- **Average Lead Time:** Calculated from shipment to delivery
- **Supply Adequacy:** (Supply / Demand) × 100

### Treatment Coverage
- **Target:** 75% effective coverage
- **Population Groups:** SAC, PreSAC, Adults
- **Endemicity Levels:** High (≥50%), Moderate (10-49%), Low (<10%)

### Forecast Accuracy
- **Supply Forecast 2025:** ~30M tablets
- **Supply Forecast 2026:** ~30M tablets
- **Supply Forecast 2027:** ~30M tablets

## 🗺️ Geospatial Features

**Data Source:** ESPEN IU 2024 Shapefile

**Processing:**
- Filtered for Nigeria (774 LGAs)
- Converted to WGS84 (EPSG:4326) for web mapping
- Simplified geometries for performance
- Merged with latest treatment data (2024)

**Map Layers:**
1. **Endemicity:** Prevalence classification
2. **Coverage:** Treatment coverage percentage
3. **Priority:** Multi-criteria priority score

## 🔗 API Endpoints

### Supply Chain
- `GET /api/supply-chain/metrics` - Overall KPIs
<!-- - `GET /api/supply/forecast` - ARIMA forecast -->
- `GET /api/procurement/orders?year=2024` - PO details
- `GET /api/supply-chain/lead-times` - Lead time analysis

### Demand & Coverage
- `GET /api/dashboard/national?year=2024` - National summary
- `GET /api/coverage/trend` - 5-year trend
- `GET /api/supply-demand/historical` - Annual integration

### Forecasting
- `GET /api/forecast/combined` - Supply + demand forecast
- `GET /api/demand/forecast` - Demand projection

### Geographic
- `GET /api/geo/nigeria-iu` - IU-level GeoJSON
- `GET /api/geo/nigeria-states` - State-level GeoJSON
- `GET /api/priority/lgas?limit=50` - Priority ranking

## 🎨 ESPEN Styling

**Color Palette:**
- Primary Blue: `#0056A4`
- Dark Blue: `#003D7A`
- Success Green: `#28A745`
- Warning Yellow: `#FFC107`
- Danger Red: `#DC3545`

**Design Principles:**
- Clean, professional interface
- Consistent with ESPEN Portal branding
- Responsive design for mobile/tablet
- Accessibility-focused

## 📝 Data Sources

1. **ESPEN Portal**
   - Nigeria SCH IU data (2020-2024)
   - Implementation unit boundaries
   - Treatment coverage data

2. **NTDeliver**
   - Procurement order list
   - Delivery timelines
   - PZQ quantities

3. **ESPEN Geospatial**
   - Nigeria shapefile (774 LGAs)
   - Administrative boundaries

## 🔐 Data Privacy

- All data is aggregated at LGA level (no individual records)
- Compliant with WHO data sharing policies
- No personally identifiable information (PII)

## 🛠️ Customization

### Adding New Years
Update `process_supply_chain_data.py` to include new data years and re-run:
```bash
python3 process_supply_chain_data.py
```

<!-- ### Modifying Forecasts
Adjust ARIMA parameters in the script:
```python
model = ARIMA(ts_data['quantity'], order=(p, d, q))
``` -->

### Changing Map Layers
Edit `map.html` layer definitions:
```javascript
const layerSelector = document.getElementById('layerSelector');
// Add new options
```

## 📊 Sample Outputs

### Supply Chain Metrics
```json
{
  "totalPOsDelivered": 22,
  "totalTabletsSupplied": 346000000,
  "avgLeadTime": 156,
  "recent3YearsSupply": 77616000
}
```
<!-- 
### ARIMA Forecast
```json
[
  {
    "year": 2025,
    "forecastSupply": 30087442,
    "lowerBound": 25574325,
    "upperBound": 34600558,
    "method": "ARIMA(1,1,1)"
  }
]
``` -->

## 🐛 Troubleshooting

**Issue:** Data files not found
```bash
# Solution: Run data processing script
python3 process_supply_chain_data.py
```

**Issue:** Port 3000 already in use
```bash
# Solution: Change port in server/app.js
const PORT = process.env.PORT || 8080;
```

**Issue:** GeoJSON not loading
```bash
# Check file size and browser console for errors
# Ensure shapefile was properly converted
```

## 📚 References

- WHO Schistosomiasis Treatment Guidelines
- ESPEN Data Portal: https://espen.afro.who.int/
- NTDeliver: https://www.ntdeliver.com/
<!-- - ARIMA Forecasting: Box-Jenkins methodology -->

## 👥 Contributors

**Developer:** Fred Ochieng
**Organization:** ESPEN/WHO AFRO
**Purpose:** Preventive Chemotherapy Quantification

## 📄 License

This project is intended for public health research and programme implementation. Data usage should comply with WHO and ESPEN data sharing policies.

---

## 🚀 Deployment

### Option 1: Heroku
```bash
heroku create nigeria-sch-supply-chain
git push heroku main
```

### Option 2: DigitalOcean
```bash
# Upload files via SFTP
ssh user@server
cd /var/www/nigeria-sch
npm install
pm2 start server/app.js
```

### Option 3: Vercel (Serverless)
```bash
npm install -g vercel
vercel --prod
```

---

**Built with ❤️ for Global Health**
