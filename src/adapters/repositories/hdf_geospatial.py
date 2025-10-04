"""
🌍 HDF Geospatial Adapter
Converts HDF grid data to geographic coordinates (lat/lon) for mapping
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class HDFGeospatialConverter:
    """
    Converts MODIS sinusoidal grid to lat/lon coordinates
    
    MODIS uses sinusoidal projection with tiles (h/v system)
    Each tile is 10° x 10° at equator
    """
    
    # MODIS tile system constants
    TILE_SIZE = 1200  # pixels per tile (for 1km products)
    EARTH_RADIUS = 6371007.181  # meters
    TILE_WIDTH = 1111950.0  # meters (10 degrees at equator)
    
    def __init__(self):
        pass
    
    def grid_to_latlon(
        self, 
        h: int, 
        v: int, 
        row: int, 
        col: int,
        resolution: int = 1000
    ) -> Tuple[float, float]:
        """
        Convert MODIS grid coordinates to lat/lon
        
        Args:
            h: Horizontal tile number (0-35)
            v: Vertical tile number (0-17)
            row: Row within tile (0-1199 for 1km)
            col: Column within tile (0-1199 for 1km)
            resolution: Pixel resolution in meters (1000 for 1km, 500 for 500m)
            
        Returns:
            (latitude, longitude) in degrees
        """
        
        # Calculate position in sinusoidal projection
        x = (h * self.TILE_SIZE + col) * resolution
        y = (v * self.TILE_SIZE + row) * resolution
        
        # Convert to lat/lon
        lat = 90 - (y / self.EARTH_RADIUS) * (180 / np.pi)
        
        # Sinusoidal projection: lon depends on latitude
        lon = (x / (self.EARTH_RADIUS * np.cos(lat * np.pi / 180))) * (180 / np.pi) - 180
        
        return (lat, lon)
    
    def extract_fire_points(
        self,
        fire_mask: np.ndarray,
        h: int,
        v: int,
        confidence: Optional[np.ndarray] = None,
        frp: Optional[np.ndarray] = None,
        min_confidence: int = 50,
        max_points: int = 10000
    ) -> List[Dict]:
        """
        Extract fire points with coordinates
        
        Args:
            fire_mask: 2D array with fire detection (7-9 = fire)
            h: Horizontal tile number
            v: Vertical tile number
            confidence: Optional confidence array
            frp: Optional Fire Radiative Power array
            min_confidence: Minimum confidence to include (0-100)
            max_points: Maximum points to return (for performance)
            
        Returns:
            List of fire points with lat/lon
        """
        
        # Find fire pixels (values 7-9 in MODIS fire mask)
        fire_pixels = np.where(fire_mask >= 7)
        
        if len(fire_pixels[0]) == 0:
            logger.info("No fire pixels found")
            return []
        
        logger.info(f"Found {len(fire_pixels[0])} fire pixels")
        
        # Filter by confidence if provided
        if confidence is not None:
            conf_mask = confidence[fire_pixels] >= min_confidence
            fire_pixels = (fire_pixels[0][conf_mask], fire_pixels[1][conf_mask])
            logger.info(f"After confidence filter: {len(fire_pixels[0])} pixels")
        
        # Limit number of points
        if len(fire_pixels[0]) > max_points:
            logger.warning(f"Too many points ({len(fire_pixels[0])}), sampling {max_points}")
            indices = np.random.choice(len(fire_pixels[0]), max_points, replace=False)
            fire_pixels = (fire_pixels[0][indices], fire_pixels[1][indices])
        
        # Convert to lat/lon
        points = []
        for i in range(len(fire_pixels[0])):
            row = int(fire_pixels[0][i])
            col = int(fire_pixels[1][i])
            
            lat, lon = self.grid_to_latlon(h, v, row, col)
            
            point = {
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "type": "fire"
            }
            
            # Add optional attributes
            if confidence is not None:
                point["confidence"] = int(confidence[row, col])
            
            if frp is not None:
                point["frp"] = float(frp[row, col])
            
            points.append(point)
        
        return points
    
    def extract_burned_area_points(
        self,
        burn_date: np.ndarray,
        h: int,
        v: int,
        max_points: int = 10000
    ) -> List[Dict]:
        """
        Extract burned area points from MCD64A1
        
        Args:
            burn_date: 2D array with burn dates (day of year, 0 = no burn)
            h: Horizontal tile number
            v: Vertical tile number
            max_points: Maximum points to return
            
        Returns:
            List of burned area points with lat/lon
        """
        
        # Find burned pixels (non-zero values)
        burned_pixels = np.where(burn_date > 0)
        
        if len(burned_pixels[0]) == 0:
            logger.info("No burned pixels found")
            return []
        
        logger.info(f"Found {len(burned_pixels[0])} burned pixels")
        
        # Sample if too many
        if len(burned_pixels[0]) > max_points:
            logger.warning(f"Sampling {max_points} from {len(burned_pixels[0])} pixels")
            indices = np.random.choice(len(burned_pixels[0]), max_points, replace=False)
            burned_pixels = (burned_pixels[0][indices], burned_pixels[1][indices])
        
        # Convert to lat/lon
        points = []
        for i in range(len(burned_pixels[0])):
            row = int(burned_pixels[0][i])
            col = int(burned_pixels[1][i])
            
            lat, lon = self.grid_to_latlon(h, v, row, col, resolution=500)  # MCD64 is 500m
            
            points.append({
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "burn_day": int(burn_date[row, col]),
                "type": "burned_area"
            })
        
        return points
    
    def create_geojson(self, points: List[Dict], properties: Optional[Dict] = None) -> Dict:
        """
        Convert points to GeoJSON format (standard for web maps)
        
        Args:
            points: List of points with lat/lon
            properties: Optional metadata
            
        Returns:
            GeoJSON FeatureCollection
        """
        
        features = []
        
        for point in points:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point["lon"], point["lat"]]  # GeoJSON is [lon, lat]
                },
                "properties": {k: v for k, v in point.items() if k not in ["lat", "lon"]}
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        if properties:
            geojson["properties"] = properties
        
        return geojson
    
    def aggregate_to_grid(
        self,
        points: List[Dict],
        grid_size: float = 0.1
    ) -> List[Dict]:
        """
        Aggregate points to grid cells (for performance)
        
        Args:
            points: List of points with lat/lon
            grid_size: Grid cell size in degrees (0.1 = ~10km)
            
        Returns:
            List of aggregated grid cells
        """
        
        # Group points by grid cell
        grid = {}
        
        for point in points:
            lat_cell = round(point["lat"] / grid_size) * grid_size
            lon_cell = round(point["lon"] / grid_size) * grid_size
            key = (lat_cell, lon_cell)
            
            if key not in grid:
                grid[key] = {
                    "lat": lat_cell,
                    "lon": lon_cell,
                    "count": 0,
                    "total_frp": 0.0,
                    "max_confidence": 0
                }
            
            grid[key]["count"] += 1
            
            if "frp" in point:
                grid[key]["total_frp"] += point["frp"]
            
            if "confidence" in point:
                grid[key]["max_confidence"] = max(
                    grid[key]["max_confidence"],
                    point["confidence"]
                )
        
        # Convert to list
        aggregated = []
        for cell in grid.values():
            if cell["count"] > 0:
                cell["avg_frp"] = cell["total_frp"] / cell["count"] if cell["total_frp"] > 0 else 0
                aggregated.append(cell)
        
        logger.info(f"Aggregated {len(points)} points to {len(aggregated)} grid cells")
        
        return aggregated
    
    def extract_tile_from_filename(self, filename: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extract h/v tile numbers from MODIS filename
        
        Example: MOD14A1.A2019274.h11v09.061.hdf -> (11, 9)
        """
        
        import re
        match = re.search(r'h(\d{2})v(\d{2})', filename)
        
        if match:
            h = int(match.group(1))
            v = int(match.group(2))
            return (h, v)
        
        return (None, None)
