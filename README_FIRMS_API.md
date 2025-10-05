# 🛰️ NASA FIRMS API Integration

## Overview

This application now fetches real-time fire detection data directly from **NASA FIRMS** (Fire Information for Resource Management System) instead of using static CSV files.

## What is FIRMS?

NASA's Fire Information for Resource Management System (FIRMS) distributes Near Real-Time (NRT) active fire data from MODIS and VIIRS instruments aboard NASA satellites.

- **MODIS**: Moderate Resolution Imaging Spectroradiometer (Terra & Aqua satellites)
- **VIIRS**: Visible Infrared Imaging Radiometer Suite (Suomi NPP & NOAA-20 satellites)

## Data Source

- **API Endpoint**: `https://firms.modaps.eosdis.nasa.gov/api/area/csv`
- **API Key**: `f88006d36b850babbc1dbd32ed0c394a`
- **Data Format**: CSV with the following fields:
  - `latitude`, `longitude`: Geographic coordinates
  - `brightness`: Brightness temperature (Kelvin)
  - `scan`, `track`: Pixel size
  - `acq_date`, `acq_time`: Acquisition date and time
  - `satellite`, `instrument`: Data source
  - `confidence`: Detection confidence (0-100)
  - `version`: Algorithm version
  - `bright_t31`: Channel 31 brightness temperature
  - `frp`: Fire Radiative Power (MW)
  - `daynight`: Day or Night detection
  - `type`: Fire type (0=presumed vegetation fire, other values for different types)

## How It Works

### Lazy Data Loading

The application uses **lazy loading** - data is loaded only when first requested, not at startup:

```python
# Data loads automatically on first API call
GET /csv/fire-points  # First call triggers data loading
```

**Benefits:**
- ⚡ **Fast startup** - Application starts instantly
- 💾 **Memory efficient** - Data loaded only when needed
- 🎯 **On-demand** - No wasted resources if endpoints not used

### Smart Data Loading Strategy

The repository automatically detects the year and chooses the best data source:

- **Year 2004**: Loads from local CSV file (`data/raw/fire_archive_M-C61_669832.csv`)
  - ✅ **Instant loading** (~1-2 seconds for 466k records)
  - ✅ **No rate limiting issues**
  - ✅ **Works offline**
  - 📂 **File**: `fire_archive_M-C61_669832.csv`
  
- **Other years**: Fetches from NASA FIRMS API
  - 📡 Real-time data from NASA servers
  - ⏱️ Automatic chunking (10-day limit per request)
  - 🔄 Rate limiting (1 second between requests)

**Note**: The FIRMS API has a 10-day limit per request, so the repository automatically splits large date ranges into chunks and fetches them sequentially with rate limiting.

### Available Data Sources

- `MODIS_SP`: MODIS (Terra & Aqua) - South America
- `VIIRS_SNPP_SP`: VIIRS S-NPP - South America
- `VIIRS_NOAA20_SP`: VIIRS NOAA-20 - South America

You can add more sources by modifying the `sources` parameter in `main.py`.

## API Endpoints

### Fire Data Endpoints (Updated)

All existing `/csv/*` endpoints now use NASA FIRMS API data:

#### `GET /csv/fire-points`
Get fire points for globe visualization (GeoJSON format)

**Query Parameters:**
- `max_points` (default: 5000): Maximum points to return
- `min_confidence` (default: 50): Minimum confidence level (0-100)
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)

**Example:**
```bash
curl "http://localhost:8000/csv/fire-points?max_points=1000&min_confidence=80"
```

#### `GET /csv/statistics`
Get overall statistics from fire data

**Returns:**
- Total detections
- Date range
- Geographic extent
- Brightness statistics
- FRP (Fire Radiative Power) statistics
- Confidence distribution
- Satellite breakdown
- Day/Night distribution

#### `GET /csv/temporal-analysis`
Get temporal analysis of fire detections over time

**Returns:**
- Daily fire counts
- Peak fire days
- Daily FRP totals
- Trends over time

#### `GET /csv/hotspots`
Get fire hotspot clusters

**Query Parameters:**
- `grid_size` (default: 0.5): Grid cell size in degrees

**Returns:**
- Top 50 hotspot clusters
- Fire count per cluster
- Average FRP
- Intensity classification

#### `GET /csv/fire-details`
Get detailed fire information near a point (for click events)

**Query Parameters:**
- `lat`: Latitude
- `lon`: Longitude
- `radius` (default: 0.1): Search radius in degrees

### New Endpoints

#### `GET /csv/data-status`
Check the status of loaded fire data

**Returns:**
```json
{
  "status": "ready",
  "total_detections": 125430,
  "date_range": {
    "start": "2004-07-22",
    "end": "2004-12-04"
  },
  "last_fetch": "2025-10-05T17:52:00",
  "data_source": "NASA FIRMS API",
  "satellites": ["Terra", "Aqua"]
}
```

#### `POST /csv/refresh`
Refresh data with recent detections from NASA FIRMS

**Query Parameters:**
- `days` (default: 1): Number of recent days to fetch (1-10)

**Example:**
```bash
curl -X POST "http://localhost:8000/csv/refresh?days=3"
```

**Returns:**
```json
{
  "status": "success",
  "message": "Data refreshed with last 3 days",
  "total_detections": 125650,
  "cache_cleared": true
}
```

## Caching

The application uses in-memory caching with a 5-minute TTL (Time To Live) to reduce API calls and improve performance:

- Fire points queries are cached
- Statistics are cached
- Temporal analysis is cached
- Hotspots are cached
- Cache is automatically cleared when data is refreshed

### Cache Management Endpoints

- `GET /cache/stats`: Get cache statistics
- `GET /cache/clear`: Clear all cache

## Configuration

### Environment Variables

You can configure the historical data range using environment variables:

```bash
export FIRMS_START_DATE="2004-07-22"
export FIRMS_END_DATE="2004-12-04"
export FIRMS_SOURCES="MODIS_SP"  # VIIRS only available from 2012+
```

### Modifying Data Sources

To fetch data from multiple sources, edit `main.py`:

```python
firms_api_repo.load_historical_data(
    start_date="2004-07-22",
    end_date="2004-12-04",
    sources=["MODIS_SP"]  # Only MODIS available in 2004
)
```

**Note**: More sources = more data = longer startup time

## Performance Considerations

### Startup Time

Loading historical data takes time depending on the date range:
- **1 month**: ~30 seconds
- **3 months**: ~90 seconds
- **6 months**: ~180 seconds

The application splits requests into 10-day chunks with 1-second delays between requests to respect NASA's rate limits.

### Memory Usage

Fire detection data is stored in memory using pandas DataFrames:
- **~100KB per 1000 detections**
- **~10MB for 100,000 detections**
- **~50MB for 500,000 detections**

### Rate Limiting

The repository implements rate limiting:
- 1-second delay between API requests
- Automatic retry on failures
- Graceful degradation if API is unavailable

## Frontend Integration

Your frontend code remains unchanged! The API endpoints maintain the same interface:

```typescript
// From your fireApi.ts
export async function fetchFirePoints(options: FireAPIOptions = {}): Promise<FirePointsResponse> {
  const {
    maxPoints = 10000,
    minConfidence = 0,
    startDate,
    endDate,
  } = options;

  const params = new URLSearchParams({
    max_points: maxPoints.toString(),
    min_confidence: minConfidence.toString(),
  });

  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await fetch(`${API_URL}/csv/fire-points?${params}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch fire points: ${response.status}`);
  }

  return response.json();
}
```

## Deployment Notes

### Render.com Deployment

The application will take longer to start on Render.com due to historical data loading:

1. **Cold Start**: First request may timeout while data loads
2. **Health Check**: Configure health check to wait for data loading
3. **Startup Logs**: Monitor logs to see data loading progress

### Recommended Render Configuration

```yaml
# render.yaml
services:
  - type: web
    name: nasa-firms-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    healthCheckPath: /health
    initialDelaySeconds: 120  # Wait for data loading
```

## Troubleshooting

### Data Not Loading

Check the logs for errors:
```bash
# Look for these log messages
🛰️ Initializing NASA FIRMS API repository...
📡 Loading historical fire data from NASA FIRMS...
📡 Fetching MODIS_SP data from 2024-07-22 to 2024-07-31
✅ Fetched 12543 fire detections
```

### API Rate Limiting

If you see rate limit errors, the repository will automatically retry with exponential backoff.

### Memory Issues

If the application runs out of memory:
1. Reduce the date range
2. Use only one data source (MODIS_SP)
3. Increase server memory allocation

## Future Enhancements

- [ ] Persistent data storage (PostgreSQL/MongoDB)
- [ ] Incremental updates (only fetch new data)
- [ ] Background data refresh scheduler
- [ ] Data compression for memory efficiency
- [ ] Multi-region support (not just South America)
- [ ] Real-time streaming updates

## Resources

- [NASA FIRMS Website](https://firms.modaps.eosdis.nasa.gov/)
- [FIRMS API Documentation](https://firms.modaps.eosdis.nasa.gov/api/)
- [MODIS Fire Products](https://modis.gsfc.nasa.gov/data/dataprod/mod14.php)
- [VIIRS Fire Products](https://www.earthdata.nasa.gov/learn/find-data/near-real-time/firms)

## License

This application uses NASA's publicly available FIRMS data. Please cite NASA FIRMS when using this data in publications or presentations.

**Citation:**
> FIRMS: Fire Information for Resource Management System. NASA. https://firms.modaps.eosdis.nasa.gov/
