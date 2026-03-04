const express = require('express');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Helper function to load JSON data
const loadJSON = (filename) => {
    const filepath = path.join(__dirname, '../data', filename);
    try {
        return JSON.parse(fs.readFileSync(filepath, 'utf8'));
    } catch (error) {
        console.error(`Error loading ${filename}:`, error.message);
        return null;
    }
};

// Load all data files
let demandData, supplyData, integrated, supplyForecast, demandForecast;
let supplyChainMetrics, priorityLGAs, stateSummary;

try {
    demandData = loadJSON('demand_data.json');
    supplyData = loadJSON('supply_data.json');
    integrated = loadJSON('supply_demand_integrated.json');
    supplyForecast = loadJSON('supply_forecast.json');
    demandForecast = loadJSON('demand_forecast.json');
    supplyChainMetrics = loadJSON('supply_chain_metrics.json');
    priorityLGAs = loadJSON('priority_lgas.json');
    stateSummary = loadJSON('state_summary.json');
    
    console.log('✓ All data files loaded successfully');
} catch (error) {
    console.error('Error loading data files:', error.message);
    console.log('Please run: python3 process_supply_chain_data.py');
    process.exit(1);
}

// =============================================================================
// API ROUTES
// =============================================================================

// Supply Chain Metrics & KPIs
app.get('/api/supply-chain/metrics', (req, res) => {
    res.json(supplyChainMetrics);
});

// Supply-Demand Integration (Historical)
app.get('/api/supply-demand/historical', (req, res) => {
    const startYear = parseInt(req.query.startYear) || 2020;
    const endYear = parseInt(req.query.endYear) || 2024;
    
    const filtered = integrated.filter(d => 
        d.year >= startYear && d.year <= endYear
    );
    
    res.json(filtered);
});

// Supply Forecast (ARIMA)
app.get('/api/supply/forecast', (req, res) => {
    res.json(supplyForecast);
});

// Demand Forecast
app.get('/api/demand/forecast', (req, res) => {
    res.json(demandForecast);
});

// Combined Forecast (Supply + Demand)
app.get('/api/forecast/combined', (req, res) => {
    const historical = integrated.filter(d => d.year >= 2020 && d.year <= 2024);
    
    const combined = {
        historical: historical.map(d => ({
            year: d.year,
            demand: d.demandTablets,
            supply: d.supplyTablets,
            gap: d.supplyGap,
            adequacy: d.supplyAdequacy
        })),
        forecast: supplyForecast.map((s, idx) => ({
            year: s.year,
            demandForecast: demandForecast[idx].forecastDemand,
            supplyForecast: s.forecastSupply,
            projectedGap: demandForecast[idx].forecastDemand - s.forecastSupply,
            projectedAdequacy: (s.forecastSupply / demandForecast[idx].forecastDemand * 100).toFixed(2)
        }))
    };
    
    res.json(combined);
});

// Procurement Orders (Supply Timeline)
app.get('/api/procurement/orders', (req, res) => {
    const year = req.query.year;
    
    if (year) {
        const filtered = supplyData.filter(d => d.Year == year);
        res.json(filtered);
    } else {
        res.json(supplyData);
    }
});

// Lead Time Analysis
app.get('/api/supply-chain/lead-times', (req, res) => {
    const leadTimeAnalysis = supplyData
        .filter(d => d.totalLeadTime > 0)
        .map(d => ({
            year: d.Year,
            poNumber: d['PO Number'],
            totalLeadTime: d.totalLeadTime,
            shipToArrival: d.shipToArrival,
            arrivalToDelivery: d.arrivalToDelivery
        }))
        .sort((a, b) => b.year - a.year);
    
    res.json(leadTimeAnalysis);
});

// National Summary Dashboard
app.get('/api/dashboard/national', (req, res) => {
    const year = parseInt(req.query.year) || 2024;
    
    const yearDemand = demandData.filter(d => 
        d.year === year && d.targetPop === 'SAC'
    );
    
    const yearSupply = integrated.find(d => d.year === year);
    
    const summary = {
        year,
        demand: {
            totalLGAs: yearDemand.length,
            populationRequiring: yearDemand.reduce((sum, d) => sum + d.popReq, 0),
            populationTreated: yearDemand.reduce((sum, d) => sum + d.popTreat, 0),
            averageCoverage: (yearDemand.reduce((sum, d) => sum + d.cov, 0) / yearDemand.length).toFixed(2),
            tabletsNeeded: yearDemand.reduce((sum, d) => sum + d.tabletsNeeded, 0)
        },
        supply: yearSupply ? {
            tabletsSupplied: yearSupply.supplyTablets,
            supplyGap: yearSupply.supplyGap,
            adequacy: yearSupply.supplyAdequacy
        } : null,
        endemicity: {
            high: yearDemand.filter(d => d.endemicity === 'High prevalence (50% and above)').length,
            moderate: yearDemand.filter(d => d.endemicity === 'Moderate prevalence (10%-49%)').length,
            low: yearDemand.filter(d => d.endemicity === 'Low prevalence (less than 10%)').length,
            nonEndemic: yearDemand.filter(d => d.endemicity === 'Non-endemic').length
        }
    };
    
    res.json(summary);
});

// Priority LGAs
app.get('/api/priority/lgas', (req, res) => {
    const limit = parseInt(req.query.limit) || 50;
    res.json(priorityLGAs.slice(0, limit));
});

// State Summary
app.get('/api/states/summary', (req, res) => {
    res.json(stateSummary);
});

// GeoJSON Data
app.get('/api/geo/nigeria-iu', (req, res) => {
    const geoFile = path.join(__dirname, '../data/nigeria_iu_geojson.json');
    res.sendFile(geoFile);
});

app.get('/api/geo/nigeria-states', (req, res) => {
    const geoFile = path.join(__dirname, '../data/nigeria_states_geojson.json');
    res.sendFile(geoFile);
});

// Coverage Trend
app.get('/api/coverage/trend', (req, res) => {
    const years = [2020, 2021, 2022, 2023, 2024];
    
    const trend = years.map(year => {
        const yearData = demandData.filter(d => 
            d.year === year && d.targetPop === 'SAC'
        );
        
        return {
            year,
            coverage: (yearData.reduce((sum, d) => sum + d.cov, 0) / yearData.length).toFixed(2),
            treated: yearData.reduce((sum, d) => sum + d.popTreat, 0),
            requiring: yearData.reduce((sum, d) => sum + d.popReq, 0)
        };
    });
    
    res.json(trend);
});

// Supply Chain Performance Indicators
app.get('/api/supply-chain/performance', (req, res) => {
    const recentYears = integrated.filter(d => d.year >= 2020 && d.year <= 2024);
    
    const performance = {
        avgSupplyAdequacy: (recentYears.reduce((sum, d) => sum + (d.supplyAdequacy || 0), 0) / recentYears.length).toFixed(2),
        totalGap: recentYears.reduce((sum, d) => sum + (d.supplyGap || 0), 0),
        yearsAbove75Pct: recentYears.filter(d => d.supplyAdequacy >= 75).length,
        yearsBelowNeeds: recentYears.filter(d => d.supplyGap > 0).length,
        bestYear: recentYears.reduce((max, d) => d.supplyAdequacy > max.supplyAdequacy ? d : max),
        worstYear: recentYears.reduce((min, d) => d.supplyAdequacy < min.supplyAdequacy ? d : min)
    };
    
    res.json(performance);
});

// =============================================================================
// PAGE ROUTES
// =============================================================================

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../views/index.html'));
});

app.get('/supply-chain', (req, res) => {
    res.sendFile(path.join(__dirname, '../views/supply-chain.html'));
});

app.get('/map', (req, res) => {
    res.sendFile(path.join(__dirname, '../views/map.html'));
});

app.get('/forecast', (req, res) => {
    res.sendFile(path.join(__dirname, '../views/forecast.html'));
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'OK', 
        timestamp: new Date(),
        dataLoaded: {
            demand: !!demandData,
            supply: !!supplyData,
            integrated: !!integrated,
            forecasts: !!(supplyForecast && demandForecast)
        }
    });
});

// =============================================================================
// START SERVER
// =============================================================================

app.listen(PORT, () => {
    console.log('\n' + '='.repeat(80));
    console.log('🚀 NIGERIA SCH SUPPLY CHAIN ANALYTICS PLATFORM');
    console.log('='.repeat(80));
    console.log(`\n📍 Server: http://localhost:${PORT}`);
    console.log('\n📊 Dashboards:');
    console.log(`   - National Dashboard:    http://localhost:${PORT}/`);
    console.log(`   - Supply Chain Snapshot: http://localhost:${PORT}/supply-chain`);
    console.log(`   - Map View:              http://localhost:${PORT}/map`);
    console.log(`   - Forecast Analysis:     http://localhost:${PORT}/forecast`);
    console.log('\n🔗 API Endpoints:');
    console.log('   - GET /api/supply-chain/metrics');
    console.log('   - GET /api/supply-demand/historical');
    console.log('   - GET /api/supply/forecast');
    console.log('   - GET /api/forecast/combined');
    console.log('   - GET /api/procurement/orders');
    console.log('   - GET /api/dashboard/national?year=2024');
    console.log('   - GET /api/geo/nigeria-iu');
    console.log('\n' + '='.repeat(80) + '\n');
});
