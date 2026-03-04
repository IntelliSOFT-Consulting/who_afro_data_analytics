#!/usr/bin/env python3
"""
Nigeria SCH Supply Chain Analytics & Forecasting
Data Integration, Transformation, and ARIMA Forecasting
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import json
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ARIMA and forecasting
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Paths
RAW_DIR = Path('raw-data/uploads')
OUTPUT_DIR = Path('data')
SHAPEFILE_DIR = Path('raw-data/shapefiles')

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("NIGERIA SCH SUPPLY CHAIN ANALYTICS & FORECASTING")
print("=" * 80)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Dosing parameters (tablets per person)
DOSING_FACTORS = {
    'SAC': 2.5,
    'PreSAC': 1.5,
    'Adults': 4.0,
    'Total': 2.5
}

# Treatment frequency by endemicity
FREQUENCY_MAP = {
    'High prevalence (50% and above)': 1.0,
    'Moderate prevalence (10%-49%)': 1.0,
    'Low prevalence (less than 10%)': 0.5,
    'Non-endemic': 0.0
}

BUFFER_FACTOR = 1.15  # 15% wastage buffer

# =============================================================================
# DEMAND SIDE: ESPEN DATA PROCESSING
# =============================================================================

def process_demand_data():
    """Process ESPEN SCH data to calculate demand"""
    print("\n📊 PROCESSING DEMAND DATA (ESPEN)...")
    
    df = pd.read_csv(RAW_DIR / 'data-NG-SCH-iu-2020-2024-20260303_115420.csv')
    print(f"   Loaded {len(df):,} records")
    
    # Calculate tablet needs
    def calc_tablets(row):
        pop = row['popReq']
        dosing = DOSING_FACTORS.get(row['targetPop'], 2.5)
        freq = FREQUENCY_MAP.get(row['endemicity'], 0)
        return int(pop * dosing * freq * BUFFER_FACTOR)
    
    df['tabletsNeeded'] = df.apply(calc_tablets, axis=1)
    df['coverageGap'] = df['popReq'] - df['popTreat']
    df['coverageGapPct'] = (df['coverageGap'] / df['popReq'] * 100).round(2)
    
    # Calculate priority scores
    def calc_priority(row):
        endem_weights = {
            'High prevalence (50% and above)': 1.0,
            'Moderate prevalence (10%-49%)': 0.7,
            'Low prevalence (less than 10%)': 0.4,
            'Non-endemic': 0.0
        }
        
        endem_score = endem_weights.get(row['endemicity'], 0) * 30
        coverage_gap_score = (1 - row['cov'] / 100) * 25
        pop_score = min(row['popReq'] / 500000, 1.0) * 15
        historical_score = (1 - row['pcN'] / 5) * 10
        
        return round(endem_score + coverage_gap_score + pop_score + historical_score, 2)
    
    df['priorityScore'] = df.apply(calc_priority, axis=1)
    
    # Save processed data
    output_file = OUTPUT_DIR / 'demand_data.json'
    df.to_json(output_file, orient='records', indent=2)
    print(f"   ✓ Saved to {output_file}")
    
    return df

# =============================================================================
# SUPPLY SIDE: PROCUREMENT DATA PROCESSING
# =============================================================================

def process_supply_data():
    """Process NTDeliver procurement orders"""
    print("\n📦 PROCESSING SUPPLY DATA (NTDeliver PO)...")
    
    df = pd.read_csv(RAW_DIR / 'Nigeria_PO_list_1772539064.csv')
    print(f"   Loaded {len(df)} procurement orders")
    
    # Clean quantity
    df['Quantity'] = df['Quantity'].str.replace(',', '').astype(int)
    
    # Parse dates
    date_cols = ['Actual Shipment Date', 'Actual Arrival Date', 'Actual Delivery Date', 'MDA Date']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format='%d-%b-%Y', errors='coerce')
    
    # Calculate lead times
    df['shipToArrival'] = (df['Actual Arrival Date'] - df['Actual Shipment Date']).dt.days
    df['arrivalToDelivery'] = (df['Actual Delivery Date'] - df['Actual Arrival Date']).dt.days
    df['totalLeadTime'] = (df['Actual Delivery Date'] - df['Actual Shipment Date']).dt.days
    
    # Save processed data
    output_file = OUTPUT_DIR / 'supply_data.json'
    df.to_json(output_file, orient='records', indent=2, date_format='iso')
    print(f"   ✓ Saved to {output_file}")
    
    return df

# =============================================================================
# SUPPLY-DEMAND INTEGRATION
# =============================================================================

def integrate_supply_demand(demand_df, supply_df):
    """Match supply to demand by year"""
    print("\n🔗 INTEGRATING SUPPLY & DEMAND...")
    
    # Aggregate annual demand (SAC only - primary target)
    demand_annual = demand_df[demand_df['targetPop'] == 'SAC'].groupby('year').agg({
        'tabletsNeeded': 'sum',
        'popReq': 'sum',
        'popTreat': 'sum',
        'cov': 'mean'
    }).reset_index()
    
    demand_annual.columns = ['year', 'demandTablets', 'popReq', 'popTreated', 'avgCoverage']
    
    # Aggregate annual supply
    supply_annual = supply_df.groupby('Year').agg({
        'Quantity': 'sum',
        'totalLeadTime': 'mean'
    }).reset_index()
    
    supply_annual.columns = ['year', 'supplyTablets', 'avgLeadTime']
    
    # Merge
    integrated = demand_annual.merge(supply_annual, on='year', how='outer')
    integrated = integrated.sort_values('year')
    integrated['supplyTablets'] = integrated['supplyTablets'].fillna(0).astype(int)
    
    # Calculate metrics
    integrated['supplyGap'] = integrated['demandTablets'] - integrated['supplyTablets']
    integrated['supplyAdequacy'] = (integrated['supplyTablets'] / integrated['demandTablets'] * 100).round(2)
    integrated['coverageGap'] = integrated['popReq'] - integrated['popTreated']
    
    # Save
    output_file = OUTPUT_DIR / 'supply_demand_integrated.json'
    integrated.to_json(output_file, orient='records', indent=2)
    print(f"   ✓ Saved to {output_file}")
    
    print("\n📈 SUPPLY-DEMAND SUMMARY (2020-2024):")
    print(integrated[['year', 'demandTablets', 'supplyTablets', 'supplyGap', 'supplyAdequacy']])
    
    return integrated

# =============================================================================
# ARIMA FORECASTING
# =============================================================================

def test_stationarity(timeseries):
    """Test if time series is stationary"""
    result = adfuller(timeseries.dropna())
    return {
        'adf_statistic': result[0],
        'p_value': result[1],
        'is_stationary': result[1] < 0.05
    }

def forecast_supply_arima(supply_df, forecast_years=3):
    """
    Forecast future supply using ARIMA model
    """
    print("\n🔮 ARIMA FORECASTING FOR SUPPLY CHAIN...")
    
    # Prepare time series (2010-2024)
    ts_data = supply_df.groupby('Year')['Quantity'].sum().reset_index()
    ts_data.columns = ['year', 'quantity']
    ts_data = ts_data.sort_values('year')
    
    print(f"   Historical data: {ts_data['year'].min()}-{ts_data['year'].max()}")
    
    # Test stationarity
    stat_test = test_stationarity(ts_data['quantity'])
    print(f"   Stationarity test: ADF={stat_test['adf_statistic']:.4f}, "
          f"p-value={stat_test['p_value']:.4f}")
    
    # Fit ARIMA model
    # Using (1,1,1) as a good starting point for supply chain data
    try:
        model = ARIMA(ts_data['quantity'], order=(1, 1, 1))
        fitted_model = model.fit()
        
        print(f"   ARIMA(1,1,1) fitted successfully")
        print(f"   AIC: {fitted_model.aic:.2f}, BIC: {fitted_model.bic:.2f}")
        
        # Forecast
        forecast = fitted_model.forecast(steps=forecast_years)
        
        # Create forecast dataframe
        last_year = ts_data['year'].max()
        forecast_years_list = [last_year + i + 1 for i in range(forecast_years)]
        
        forecast_df = pd.DataFrame({
            'year': forecast_years_list,
            'forecastSupply': forecast.values.astype(int),
            'lowerBound': (forecast.values * 0.85).astype(int),  # 85% confidence
            'upperBound': (forecast.values * 1.15).astype(int),  # 115% confidence
            'method': 'ARIMA(1,1,1)'
        })
        
        # Save forecast
        output_file = OUTPUT_DIR / 'supply_forecast.json'
        forecast_df.to_json(output_file, orient='records', indent=2)
        print(f"   ✓ Forecast saved to {output_file}")
        
        print("\n   📊 SUPPLY FORECAST:")
        print(forecast_df)
        
        return forecast_df, fitted_model
        
    except Exception as e:
        print(f"   ⚠️ ARIMA fitting failed: {str(e)}")
        print("   Using simple moving average instead...")
        
        # Fallback: Simple moving average
        avg_supply = ts_data['quantity'].tail(3).mean()
        forecast_df = pd.DataFrame({
            'year': [last_year + i + 1 for i in range(forecast_years)],
            'forecastSupply': [int(avg_supply)] * forecast_years,
            'lowerBound': [int(avg_supply * 0.85)] * forecast_years,
            'upperBound': [int(avg_supply * 1.15)] * forecast_years,
            'method': 'Moving Average'
        })
        
        output_file = OUTPUT_DIR / 'supply_forecast.json'
        forecast_df.to_json(output_file, orient='records', indent=2)
        print(f"   ✓ Forecast saved to {output_file}")
        
        return forecast_df, None

def forecast_demand_trend(demand_df, forecast_years=3):
    """Forecast demand using linear trend"""
    print("\n📈 DEMAND TREND FORECASTING...")
    
    # Annual demand for SAC
    demand_ts = demand_df[demand_df['targetPop'] == 'SAC'].groupby('year').agg({
        'tabletsNeeded': 'sum'
    }).reset_index()
    
    # Fit linear trend
    from sklearn.linear_model import LinearRegression
    
    X = demand_ts['year'].values.reshape(-1, 1)
    y = demand_ts['tabletsNeeded'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Forecast
    last_year = demand_ts['year'].max()
    future_years = np.array([last_year + i + 1 for i in range(forecast_years)]).reshape(-1, 1)
    forecast = model.predict(future_years)
    
    forecast_df = pd.DataFrame({
        'year': future_years.flatten(),
        'forecastDemand': forecast.astype(int),
        'lowerBound': (forecast * 0.90).astype(int),
        'upperBound': (forecast * 1.10).astype(int),
        'method': 'Linear Trend'
    })
    
    # Save
    output_file = OUTPUT_DIR / 'demand_forecast.json'
    forecast_df.to_json(output_file, orient='records', indent=2)
    print(f"   ✓ Forecast saved to {output_file}")
    print(forecast_df)
    
    return forecast_df

# =============================================================================
# GEOSPATIAL DATA PROCESSING
# =============================================================================

def process_geospatial_data(demand_df):
    """Convert shapefile to GeoJSON and merge with data"""
    print("\n🗺️  PROCESSING GEOSPATIAL DATA...")
    
    try:
        # Load shapefile
        shapefile = SHAPEFILE_DIR / 'ESPEN_IU_2024.shp'
        gdf = gpd.read_file(shapefile)
        
        print(f"   Loaded {len(gdf)} features from shapefile")
        print(f"   CRS: {gdf.crs}")
        
        # Filter for Nigeria
        nigeria_gdf = gdf[gdf['ADMIN0'] == 'Nigeria'].copy()
        print(f"   Nigeria features: {len(nigeria_gdf)}")
        
        # Get latest year data for SAC
        latest_year = demand_df['year'].max()
        latest_data = demand_df[
            (demand_df['year'] == latest_year) & 
            (demand_df['targetPop'] == 'SAC')
        ].copy()
        
        # Merge data with geometries
        # Match on IU_ID
        merged = nigeria_gdf.merge(
            latest_data[['iuId', 'endemicity', 'cov', 'popReq', 
                        'tabletsNeeded', 'priorityScore']],
            left_on='IU_ID',
            right_on='iuId',
            how='left'
        )
        
        # Fill missing values
        merged['cov'] = merged['cov'].fillna(0)
        merged['priorityScore'] = merged['priorityScore'].fillna(0)
        
        # Convert to WGS84 for web mapping
        merged = merged.to_crs('EPSG:4326')
        
        # Simplify geometries to reduce file size
        merged['geometry'] = merged['geometry'].simplify(0.01)
        
        # Save as GeoJSON
        output_file = OUTPUT_DIR / 'nigeria_iu_geojson.json'
        merged.to_file(output_file, driver='GeoJSON')
        print(f"   ✓ GeoJSON saved to {output_file}")
        
        # Create state-level aggregation
        state_agg = merged.dissolve(by='ADMIN1', aggfunc={
            'popReq': 'sum',
            'cov': 'mean',
            'priorityScore': 'mean'
        })
        
        state_output = OUTPUT_DIR / 'nigeria_states_geojson.json'
        state_agg.to_file(state_output, driver='GeoJSON')
        print(f"   ✓ State-level GeoJSON saved to {state_output}")
        
        return merged
        
    except Exception as e:
        print(f"   ⚠️ Geospatial processing failed: {str(e)}")
        return None

# =============================================================================
# ANALYTICS & INSIGHTS
# =============================================================================

def generate_supply_chain_metrics(supply_df, integrated_df):
    """Generate KPIs and metrics for supply chain"""
    print("\n📊 GENERATING SUPPLY CHAIN METRICS...")
    
    metrics = {
        'totalPOsDelivered': len(supply_df[supply_df['Stage'] == 'delivered']),
        'totalTabletsSupplied': int(supply_df['Quantity'].sum()),
        'avgLeadTime': int(supply_df['totalLeadTime'].mean()) if 'totalLeadTime' in supply_df else 0,
        'minLeadTime': int(supply_df['totalLeadTime'].min()) if 'totalLeadTime' in supply_df else 0,
        'maxLeadTime': int(supply_df['totalLeadTime'].max()) if 'totalLeadTime' in supply_df else 0,
        
        # Recent performance (last 3 years)
        'recent3YearsSupply': int(supply_df[supply_df['Year'].isin([2022, 2023, 2024])]['Quantity'].sum()),
        'recent3YearsDemand': int(integrated_df[integrated_df['year'].isin([2022, 2023, 2024])]['demandTablets'].sum()),
        
        # Current status
        'ordersInTransit': len(supply_df[supply_df['Stage'] == 'shipping']),
        
        # Supply adequacy trends
        'years2020_2024': integrated_df[integrated_df['year'].between(2020, 2024)].to_dict('records')
    }
    
    output_file = OUTPUT_DIR / 'supply_chain_metrics.json'
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"   ✓ Metrics saved to {output_file}")
    
    return metrics

def generate_priority_analysis(demand_df):
    """Generate priority LGAs and states"""
    print("\n🎯 GENERATING PRIORITY ANALYSIS...")
    
    latest_year = demand_df['year'].max()
    sac_latest = demand_df[
        (demand_df['targetPop'] == 'SAC') & 
        (demand_df['year'] == latest_year)
    ].copy()
    
    # Top 100 priority LGAs
    priority_lgas = sac_latest.nlargest(100, 'priorityScore')[
        ['admin2', 'admin1', 'endemicity', 'popReq', 
         'cov', 'tabletsNeeded', 'priorityScore', 'iuId']
    ].to_dict('records')
    
    # State-level aggregation
    state_priority = sac_latest.groupby('admin1').agg({
        'popReq': 'sum',
        'popTreat': 'sum',
        'tabletsNeeded': 'sum',
        'priorityScore': 'mean',
        'admin2': 'count'
    }).reset_index()
    
    state_priority.columns = ['state', 'popReq', 'popTreated', 
                              'tabletsNeeded', 'avgPriority', 'lgaCount']
    state_priority['coverage'] = (state_priority['popTreated'] / state_priority['popReq'] * 100).round(2)
    state_priority = state_priority.sort_values('avgPriority', ascending=False)
    
    # Save
    output_file = OUTPUT_DIR / 'priority_lgas.json'
    with open(output_file, 'w') as f:
        json.dump(priority_lgas, f, indent=2)
    print(f"   ✓ Priority LGAs saved to {output_file}")
    
    output_file = OUTPUT_DIR / 'state_summary.json'
    state_priority.to_json(output_file, orient='records', indent=2)
    print(f"   ✓ State summary saved to {output_file}")
    
    return priority_lgas, state_priority

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution pipeline"""
    
    # Process data
    demand_df = process_demand_data()
    supply_df = process_supply_data()
    
    # Integration
    integrated_df = integrate_supply_demand(demand_df, supply_df)
    
    # Forecasting
    supply_forecast, arima_model = forecast_supply_arima(supply_df, forecast_years=3)
    demand_forecast = forecast_demand_trend(demand_df, forecast_years=3)
    
    # Geospatial
    geo_data = process_geospatial_data(demand_df)
    
    # Analytics
    metrics = generate_supply_chain_metrics(supply_df, integrated_df)
    priority_lgas, state_summary = generate_priority_analysis(demand_df)
    
    print("\n" + "=" * 80)
    print("✅ DATA PROCESSING COMPLETE")
    print("=" * 80)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nGenerated files:")
    print("  1. demand_data.json - Processed ESPEN data with calculated metrics")
    print("  2. supply_data.json - Processed procurement orders")
    print("  3. supply_demand_integrated.json - Annual supply-demand matching")
    print("  4. supply_forecast.json - ARIMA supply forecast (2025-2027)")
    print("  5. demand_forecast.json - Demand trend forecast (2025-2027)")
    print("  6. nigeria_iu_geojson.json - IU-level GeoJSON with data")
    print("  7. nigeria_states_geojson.json - State-level aggregated GeoJSON")
    print("  8. supply_chain_metrics.json - KPIs and performance metrics")
    print("  9. priority_lgas.json - Top 100 priority LGAs")
    print(" 10. state_summary.json - State-level summary statistics")
    
    print("\n🚀 Ready to start Node.js server!")
    print("   Next: npm install && npm start")

if __name__ == '__main__':
    main()
