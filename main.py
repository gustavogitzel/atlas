"""
🚀 FastAPI Main Application - NASA HDF Processor
Hexagonal Architecture + Async + Dependency Injection
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List
import logging
import os
import numpy as np

from src.domain.services import EnvironmentalAnalysisService, GameMissionService
from src.domain.ports import HDFDataRepository, RegionRepository
from src.adapters.repositories.hdf_real_repository import RealHDFRepository
from src.adapters.repositories.region_repository import InMemoryRegionRepository
from src.adapters.repositories.hdf_geospatial import HDFGeospatialConverter
from src.adapters.repositories.csv_fire_repository import CSVFireRepository

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dependency Injection Container
class Container:
    """DI Container"""
    
    def __init__(self, data_dir: str = "./data/raw"):
        # Repositories (Adapters)
        self.region_repo = InMemoryRegionRepository()
        self.hdf_repo = RealHDFRepository(data_dir=data_dir)
        
        # Services (Domain)
        self.analysis_service = EnvironmentalAnalysisService(self.hdf_repo)
        self.game_service = GameMissionService(self.analysis_service)

# Initialize container with data directory
DATA_DIR = os.getenv("HDF_DATA_DIR", "./data/raw")
container = Container(data_dir=DATA_DIR)

# Initialize geospatial converter
geo_converter = HDFGeospatialConverter()

# Initialize CSV fire repository
csv_fire_repo = CSVFireRepository(data_dir=DATA_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting NASA HDF API (Hexagonal Architecture)...")
    logger.info(f"   📂 Data directory: {DATA_DIR}")
    logger.info("   ✅ Domain services initialized")
    logger.info("   ✅ Real HDF repository connected")
    yield
    logger.info("🛑 Shutting down NASA HDF API...")


# Create FastAPI app
app = FastAPI(
    title="NASA HDF Processor API",
    description="Environmental data processing with Hexagonal Architecture",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 🎯 ENDPOINTS
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "name": "NASA HDF Processor API",
        "version": "2.0.0",
        "architecture": "Hexagonal (Ports & Adapters)",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/regions", tags=["regions"])
async def list_regions():
    """List all available regions"""
    regions = await container.region_repo.list_regions()
    return {
        "regions": [
            {
                "code": r.code,
                "name": r.name,
                "bounds": r.bounds,
                "baseline_ndvi": r.baseline_ndvi,
                "baseline_temp": r.baseline_temp
            }
            for r in regions
        ],
        "count": len(regions)
    }


@app.get("/hdf/fire/{region_code}", tags=["hdf-raw"])
async def get_fire_data(region_code: str):
    """Read raw fire detection data from HDF file"""
    
    region = await container.region_repo.get_region(region_code)
    if not region:
        raise HTTPException(status_code=404, detail=f"Region '{region_code}' not found")
    
    fire_data = await container.hdf_repo.get_fire_data(region)
    
    return {
        "region": region.code,
        "fire_count": fire_data.fire_count,
        "total_frp": fire_data.total_frp,
        "severity": fire_data.severity.value
    }


@app.get("/hdf/vegetation/{region_code}", tags=["hdf-raw"])
async def get_vegetation_data(region_code: str):
    """Read raw NDVI data from HDF file"""
    
    region = await container.region_repo.get_region(region_code)
    if not region:
        raise HTTPException(status_code=404, detail=f"Region '{region_code}' not found")
    
    veg_data = await container.hdf_repo.get_vegetation_data(region)
    
    return {
        "region": region.code,
        "mean_ndvi": veg_data.mean_ndvi,
        "min_ndvi": veg_data.min_ndvi,
        "max_ndvi": veg_data.max_ndvi,
        "degraded_percentage": veg_data.degraded_percentage,
        "health_status": veg_data.health_status.value
    }


@app.get("/hdf/air-quality/{region_code}", tags=["hdf-raw"])
async def get_air_quality_data(region_code: str):
    """Read raw aerosol data from HDF file"""
    
    region = await container.region_repo.get_region(region_code)
    if not region:
        raise HTTPException(status_code=404, detail=f"Region '{region_code}' not found")
    
    air_data = await container.hdf_repo.get_air_quality_data(region)
    
    return {
        "region": region.code,
        "mean_aqi": air_data.mean_aqi,
        "mean_aod": air_data.mean_aod,
        "air_quality_status": air_data.air_quality_status.value
    }


@app.get("/hdf/temperature/{region_code}", tags=["hdf-raw"])
async def get_temperature_data(region_code: str):
    """Read raw temperature data from HDF file"""
    
    region = await container.region_repo.get_region(region_code)
    if not region:
        raise HTTPException(status_code=404, detail=f"Region '{region_code}' not found")
    
    temp_data = await container.hdf_repo.get_temperature_data(region)
    
    return {
        "region": region.code,
        "mean_temp": temp_data.mean_temp,
        "min_temp": temp_data.min_temp,
        "max_temp": temp_data.max_temp,
        "mean_anomaly": temp_data.mean_anomaly,
        "baseline_temp": temp_data.baseline_temp
    }


@app.get("/hdf/all/{region_code}", tags=["hdf-raw"])
async def get_all_hdf_data(region_code: str):
    """Read all HDF data for a region"""
    
    region = await container.region_repo.get_region(region_code)
    if not region:
        raise HTTPException(status_code=404, detail=f"Region '{region_code}' not found")
    
    # Read all data in parallel
    fire_data = await container.hdf_repo.get_fire_data(region)
    veg_data = await container.hdf_repo.get_vegetation_data(region)
    air_data = await container.hdf_repo.get_air_quality_data(region)
    temp_data = await container.hdf_repo.get_temperature_data(region)
    
    return {
        "region": region.code,
        "fire": {
            "fire_count": fire_data.fire_count,
            "total_frp": fire_data.total_frp,
            "severity": fire_data.severity.value
        },
        "vegetation": {
            "mean_ndvi": veg_data.mean_ndvi,
            "min_ndvi": veg_data.min_ndvi,
            "max_ndvi": veg_data.max_ndvi,
            "degraded_percentage": veg_data.degraded_percentage,
            "health_status": veg_data.health_status.value
        },
        "air_quality": {
            "mean_aqi": air_data.mean_aqi,
            "mean_aod": air_data.mean_aod,
            "status": air_data.air_quality_status.value
        },
        "temperature": {
            "mean_temp": temp_data.mean_temp,
            "min_temp": temp_data.min_temp,
            "max_temp": temp_data.max_temp,
            "anomaly": temp_data.mean_anomaly
        }
    }


@app.get("/hdf/datasets", tags=["hdf-raw"])
async def list_datasets(filename: Optional[str] = None):
    """
    List all datasets/columns in HDF file
    
    Query params:
        - filename: Specific file to inspect (optional, uses first file if not provided)
    """
    result = await container.hdf_repo.list_all_datasets(filename)
    return result


@app.get("/hdf/dataset/{dataset_name}", tags=["hdf-raw"])
async def read_dataset(dataset_name: str, filename: Optional[str] = None):
    """
    Read raw data from a specific dataset/column
    
    Path params:
        - dataset_name: Name of the dataset (e.g., 'FireMask', 'MaxFRP')
    
    Query params:
        - filename: Specific file (optional)
    """
    result = await container.hdf_repo.read_raw_dataset(dataset_name, filename)
    return result


@app.get("/map/fire-points", tags=["mapping"])
async def get_fire_points(
    filename: Optional[str] = None,
    format: str = "geojson",
    max_points: int = 5000,
    aggregate: bool = False,
    grid_size: float = 0.1
):
    """
    Get fire detection points for mapping (optimized for React Globe)
    
    Query params:
        - filename: Specific HDF file (optional, uses first fire file)
        - format: 'geojson' or 'points' (default: geojson)
        - max_points: Maximum points to return (default: 5000)
        - aggregate: Aggregate to grid cells for performance (default: false)
        - grid_size: Grid cell size in degrees if aggregate=true (default: 0.1)
    
    Returns:
        GeoJSON FeatureCollection or array of points with lat/lon
    """
    
    try:
        # Read fire mask array directly (bypass JSON conversion)
        fire_mask = await container.hdf_repo.read_raw_dataset("FireMask", filename, return_array=True)
        
        # Get metadata
        file_info = await container.hdf_repo.read_raw_dataset("FireMask", filename)
        if "error" in file_info:
            raise HTTPException(status_code=404, detail=file_info["error"])
        
        if not isinstance(fire_mask, np.ndarray):
            raise HTTPException(status_code=500, detail="Failed to read fire mask data")
        
        # Extract tile numbers from filename
        h, v = geo_converter.extract_tile_from_filename(file_info["filename"])
        
        if h is None or v is None:
            raise HTTPException(status_code=400, detail="Could not extract tile coordinates from filename")
        
        # Try to get confidence and FRP arrays directly
        confidence = await container.hdf_repo.read_raw_dataset("QA", filename, return_array=True)
        frp = await container.hdf_repo.read_raw_dataset("MaxFRP", filename, return_array=True)
        
        # Validate arrays
        confidence = confidence if isinstance(confidence, np.ndarray) else None
        frp = frp if isinstance(frp, np.ndarray) else None
        
        # Extract fire points with coordinates
        points = geo_converter.extract_fire_points(
            fire_mask=fire_mask,
            h=h,
            v=v,
            confidence=confidence,
            frp=frp,
            max_points=max_points
        )
        
        if not points:
            return {
                "message": "No fire points found",
                "count": 0,
                "points": []
            }
        
        # Aggregate if requested
        if aggregate:
            points = geo_converter.aggregate_to_grid(points, grid_size)
        
        # Return in requested format
        if format == "geojson":
            return geo_converter.create_geojson(
                points,
                properties={
                    "source": file_info["filename"],
                    "tile": f"h{h:02d}v{v:02d}",
                    "count": len(points)
                }
            )
        else:
            return {
                "source": file_info["filename"],
                "tile": f"h{h:02d}v{v:02d}",
                "count": len(points),
                "points": points
            }
    
    except Exception as e:
        logger.error(f"Error generating fire points: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/map/burned-area", tags=["mapping"])
async def get_burned_area(
    filename: Optional[str] = None,
    format: str = "geojson",
    max_points: int = 5000
):
    """
    Get burned area points for mapping (MCD64A1 product)
    
    Query params:
        - filename: Specific HDF file (optional)
        - format: 'geojson' or 'points' (default: geojson)
        - max_points: Maximum points to return (default: 5000)
    """
    
    try:
        # Read burn date array directly (bypass JSON conversion)
        burn_date = await container.hdf_repo.read_raw_dataset("Burn Date", filename, return_array=True)
        
        # Get metadata
        file_info = await container.hdf_repo.read_raw_dataset("Burn Date", filename)
        if "error" in file_info:
            raise HTTPException(status_code=404, detail=file_info["error"])
        
        if not isinstance(burn_date, np.ndarray):
            raise HTTPException(status_code=500, detail="Failed to read burn date data")
        
        # Extract tile numbers
        h, v = geo_converter.extract_tile_from_filename(file_info["filename"])
        
        if h is None or v is None:
            raise HTTPException(status_code=400, detail="Could not extract tile coordinates")
        
        # Extract burned area points
        points = geo_converter.extract_burned_area_points(
            burn_date=burn_date,
            h=h,
            v=v,
            max_points=max_points
        )
        
        if not points:
            return {
                "message": "No burned area found",
                "count": 0,
                "points": []
            }
        
        # Return in requested format
        if format == "geojson":
            return geo_converter.create_geojson(
                points,
                properties={
                    "source": file_info["filename"],
                    "tile": f"h{h:02d}v{v:02d}",
                    "count": len(points)
                }
            )
        else:
            return {
                "source": file_info["filename"],
                "tile": f"h{h:02d}v{v:02d}",
                "count": len(points),
                "points": points
            }
    
    except Exception as e:
        logger.error(f"Error generating burned area: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/csv/fire-points", tags=["csv-fire"])
async def get_csv_fire_points(
    max_points: int = 5000,
    min_confidence: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get fire points from CSV for React Globe mapping
    
    Query params:
        - max_points: Maximum points to return (default: 5000)
        - min_confidence: Minimum confidence 0-100 (default: 50)
        - start_date: Filter by start date YYYY-MM-DD (optional)
        - end_date: Filter by end date YYYY-MM-DD (optional)
    
    Returns:
        GeoJSON FeatureCollection with fire detections
    """
    geojson = csv_fire_repo.get_fire_points_geojson(
        max_points=max_points,
        min_confidence=min_confidence,
        start_date=start_date,
        end_date=end_date
    )
    return geojson


@app.get("/csv/statistics", tags=["csv-fire"])
async def get_csv_statistics():
    """
    Get overall statistics from CSV fire data
    
    Returns interesting metrics for cards/dashboard
    """
    stats = csv_fire_repo.get_statistics()
    return stats


@app.get("/csv/temporal-analysis", tags=["csv-fire"])
async def get_temporal_analysis():
    """
    Get temporal analysis of fire detections
    
    Shows fire trends over time
    """
    analysis = csv_fire_repo.get_temporal_analysis()
    return analysis


@app.get("/csv/hotspots", tags=["csv-fire"])
async def get_hotspots(grid_size: float = 0.5):
    """
    Get fire hotspot clusters
    
    Query params:
        - grid_size: Grid cell size in degrees (default: 0.5)
    
    Returns:
        List of hotspot clusters with intensity
    """
    hotspots = csv_fire_repo.get_hotspot_clusters(grid_size=grid_size)
    return {
        "hotspots": hotspots,
        "count": len(hotspots)
    }


@app.get("/csv/fire-details", tags=["csv-fire"])
async def get_fire_details(lat: float, lon: float, radius: float = 0.1):
    """
    Get detailed fire information near a point (for click events)
    
    Query params:
        - lat: Latitude of click
        - lon: Longitude of click  
        - radius: Search radius in degrees (default: 0.1)
    
    Returns:
        List of nearby fire detections with full details
    """
    fires = csv_fire_repo.get_fire_details(lat, lon, radius)
    return {
        "fires": fires,
        "count": len(fires),
        "center": {"lat": lat, "lon": lon},
        "radius": radius
    }


@app.get("/insights/burned-area", tags=["insights"])
async def get_burned_area_insights(filename: Optional[str] = None):
    """
    Get detailed insights from MCD64A1 Burned Area dataset
    
    Returns interesting statistics and analysis about the burned area
    """
    
    try:
        # Read all relevant datasets directly as numpy arrays (bypass JSON conversion)
        burn_date_arr = await container.hdf_repo.read_raw_dataset("Burn Date", filename, return_array=True)
        burn_unc_arr = await container.hdf_repo.read_raw_dataset("Burn Date Uncertainty", filename, return_array=True)
        first_day_arr = await container.hdf_repo.read_raw_dataset("First Day", filename, return_array=True)
        last_day_arr = await container.hdf_repo.read_raw_dataset("Last Day", filename, return_array=True)
        qa_arr = await container.hdf_repo.read_raw_dataset("QA", filename, return_array=True)
        
        # Get filename for metadata
        file_info = await container.hdf_repo.read_raw_dataset("Burn Date", filename)
        if "error" in file_info:
            raise HTTPException(status_code=404, detail=file_info["error"])
        
        if not isinstance(burn_date_arr, np.ndarray):
            raise HTTPException(status_code=500, detail="Failed to read burn date data")
        
        # Calculate statistics
        burned_pixels = burn_date_arr > 0
        total_burned = int(np.sum(burned_pixels))
        
        # Area calculation (500m resolution = 0.25 km² per pixel)
        pixel_area_km2 = 0.25
        total_area_km2 = total_burned * pixel_area_km2
        
        # Burn date statistics
        valid_burn_dates = burn_date_arr[burned_pixels]
        earliest_burn = int(np.min(valid_burn_dates)) if len(valid_burn_dates) > 0 else 0
        latest_burn = int(np.max(valid_burn_dates)) if len(valid_burn_dates) > 0 else 0
        
        # Uncertainty statistics
        uncertainty_stats = {}
        if burn_unc_arr is not None:
            valid_uncertainty = burn_unc_arr[burned_pixels]
            uncertainty_stats = {
                "mean_uncertainty_days": float(np.mean(valid_uncertainty)),
                "max_uncertainty_days": int(np.max(valid_uncertainty)),
                "high_uncertainty_pixels": int(np.sum(valid_uncertainty > 10))
            }
        
        # Burn duration (difference between first and last day)
        burn_duration = {}
        if first_day_arr is not None and last_day_arr is not None:
            duration = last_day_arr - first_day_arr
            valid_duration = duration[burned_pixels]
            burn_duration = {
                "mean_duration_days": float(np.mean(valid_duration)),
                "max_duration_days": int(np.max(valid_duration)),
                "single_day_burns": int(np.sum(valid_duration == 0)),
                "multi_day_burns": int(np.sum(valid_duration > 0))
            }
        
        # Temporal distribution (burns per day)
        temporal_distribution = {}
        if len(valid_burn_dates) > 0:
            unique_days, counts = np.unique(valid_burn_dates, return_counts=True)
            temporal_distribution = {
                "total_days_with_burns": len(unique_days),
                "peak_burn_day": int(unique_days[np.argmax(counts)]),
                "peak_burn_count": int(np.max(counts)),
                "burns_per_day": [
                    {"day": int(day), "count": int(count), "area_km2": float(count * pixel_area_km2)}
                    for day, count in zip(unique_days[:10], counts[:10])  # Top 10 days
                ]
            }
        
        # Quality assessment
        qa_stats = {}
        if qa_arr is not None:
            qa_burned = qa_arr[burned_pixels]
            qa_stats = {
                "good_quality_pixels": int(np.sum(qa_burned == 0)),
                "marginal_quality_pixels": int(np.sum(qa_burned == 1)),
                "poor_quality_pixels": int(np.sum(qa_burned >= 2)),
                "quality_percentage": {
                    "good": float(np.sum(qa_burned == 0) / len(qa_burned) * 100) if len(qa_burned) > 0 else 0,
                    "marginal": float(np.sum(qa_burned == 1) / len(qa_burned) * 100) if len(qa_burned) > 0 else 0,
                    "poor": float(np.sum(qa_burned >= 2) / len(qa_burned) * 100) if len(qa_burned) > 0 else 0
                }
            }
        
        # Extract tile info
        h, v = geo_converter.extract_tile_from_filename(file_info["filename"])
        
        return {
            "source": file_info["filename"],
            "tile": f"h{h:02d}v{v:02d}" if h and v else "unknown",
            "resolution": "500m",
            "pixel_size_km2": pixel_area_km2,
            
            "summary": {
                "total_burned_pixels": total_burned,
                "total_burned_area_km2": round(total_area_km2, 2),
                "total_burned_area_hectares": round(total_area_km2 * 100, 2),
                "percentage_of_tile": round(total_burned / (2400 * 2400) * 100, 2)
            },
            
            "temporal": {
                "earliest_burn_day_of_year": earliest_burn,
                "latest_burn_day_of_year": latest_burn,
                "burn_period_days": latest_burn - earliest_burn + 1,
                **temporal_distribution
            },
            
            "burn_characteristics": {
                **burn_duration,
                **uncertainty_stats
            },
            
            "quality_assessment": qa_stats,
            
            "interesting_facts": [
                f"🔥 Total área queimada: {round(total_area_km2, 2)} km² ({round(total_area_km2 * 100, 2)} hectares)",
                f"📅 Período de queimadas: dia {earliest_burn} a {latest_burn} do ano",
                f"📊 {temporal_distribution.get('total_days_with_burns', 0)} dias diferentes com detecção de fogo",
                f"🎯 Dia com mais queimadas: dia {temporal_distribution.get('peak_burn_day', 0)} ({temporal_distribution.get('peak_burn_count', 0)} pixels)",
                f"⏱️ Queimadas de um único dia: {burn_duration.get('single_day_burns', 0)} pixels",
                f"🔄 Queimadas de múltiplos dias: {burn_duration.get('multi_day_burns', 0)} pixels",
                f"✅ Qualidade boa: {qa_stats.get('quality_percentage', {}).get('good', 0):.1f}% dos pixels"
            ]
        }
    
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level="info"
    )
