"""
📊 CSV Fire Archive Repository
Processes MODIS/VIIRS fire detection CSV files
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


class CSVFireRepository:
    """Repository for CSV fire archive data"""
    
    def __init__(self, data_dir: str = "./data/raw"):
        self.data_dir = data_dir
        self.df = None
        self._load_csv_files()
    
    def _load_csv_files(self):
        """Load all CSV files from data directory"""
        if not os.path.exists(self.data_dir):
            logger.warning(f"Data directory not found: {self.data_dir}")
            return
        
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            logger.warning("No CSV files found")
            return
        
        # Load all CSV files and concatenate
        dfs = []
        for csv_file in csv_files:
            filepath = os.path.join(self.data_dir, csv_file)
            try:
                df = pd.read_csv(filepath)
                dfs.append(df)
                logger.info(f"📊 Loaded {len(df)} fire detections from {csv_file}")
            except Exception as e:
                logger.error(f"Error loading {csv_file}: {str(e)}")
        
        if dfs:
            self.df = pd.concat(dfs, ignore_index=True)
            logger.info(f"✅ Total fire detections loaded: {len(self.df)}")
    
    def get_fire_points_geojson(
        self,
        max_points: Optional[int] = 5000,
        min_confidence: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        bbox: Optional[tuple] = None
    ) -> Dict:
        """
        Get fire points as GeoJSON for mapping
        
        Args:
            max_points: Maximum points to return
            min_confidence: Minimum confidence (0-100)
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            bbox: Bounding box (min_lat, min_lon, max_lat, max_lon)
            
        Returns:
            GeoJSON FeatureCollection
        """
        if self.df is None or len(self.df) == 0:
            return {
                "type": "FeatureCollection",
                "features": [],
                "properties": {"count": 0, "message": "No data available"}
            }
        
        # Filter data
        filtered = self.df.copy()
        
        # Confidence filter
        if 'confidence' in filtered.columns:
            filtered = filtered[filtered['confidence'] >= min_confidence]
        
        # Date filters
        if start_date and 'acq_date' in filtered.columns:
            filtered = filtered[filtered['acq_date'] >= start_date]
        
        if end_date and 'acq_date' in filtered.columns:
            filtered = filtered[filtered['acq_date'] <= end_date]
        
        # Bounding box filter
        if bbox:
            min_lat, min_lon, max_lat, max_lon = bbox
            filtered = filtered[
                (filtered['latitude'] >= min_lat) &
                (filtered['latitude'] <= max_lat) &
                (filtered['longitude'] >= min_lon) &
                (filtered['longitude'] <= max_lon)
            ]
        
        # Sample if too many points
        if max_points and len(filtered) > max_points:
            filtered = filtered.sample(n=max_points, random_state=42)
            logger.info(f"Sampled {max_points} from {len(self.df)} points")
        
        # Convert to GeoJSON
        features = []
        for _, row in filtered.iterrows():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row['longitude']), float(row['latitude'])]
                },
                "properties": {
                    "brightness": float(row.get('brightness', 0)),
                    "confidence": int(row.get('confidence', 0)),
                    "frp": float(row.get('frp', 0)),
                    "acq_date": str(row.get('acq_date', '')),
                    "acq_time": str(row.get('acq_time', '')),
                    "satellite": str(row.get('satellite', '')),
                    "instrument": str(row.get('instrument', '')),
                    "daynight": str(row.get('daynight', '')),
                    "type": int(row.get('type', 0))
                }
            }
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "count": len(features),
                "total_available": len(self.df),
                "filtered_count": len(filtered)
            }
        }
    
    def get_statistics(self) -> Dict:
        """Get overall statistics from fire data"""
        if self.df is None or len(self.df) == 0:
            return {"error": "No data available"}
        
        stats = {
            "total_detections": len(self.df),
            "date_range": {
                "start": str(self.df['acq_date'].min()) if 'acq_date' in self.df.columns else None,
                "end": str(self.df['acq_date'].max()) if 'acq_date' in self.df.columns else None
            },
            "geographic_extent": {
                "min_lat": float(self.df['latitude'].min()),
                "max_lat": float(self.df['latitude'].max()),
                "min_lon": float(self.df['longitude'].min()),
                "max_lon": float(self.df['longitude'].max())
            },
            "brightness": {
                "mean": float(self.df['brightness'].mean()) if 'brightness' in self.df.columns else None,
                "max": float(self.df['brightness'].max()) if 'brightness' in self.df.columns else None
            },
            "frp": {
                "mean": float(self.df['frp'].mean()) if 'frp' in self.df.columns else None,
                "max": float(self.df['frp'].max()) if 'frp' in self.df.columns else None,
                "total": float(self.df['frp'].sum()) if 'frp' in self.df.columns else None
            },
            "confidence": {
                "mean": float(self.df['confidence'].mean()) if 'confidence' in self.df.columns else None,
                "high_confidence": int((self.df['confidence'] >= 80).sum()) if 'confidence' in self.df.columns else None,
                "medium_confidence": int(((self.df['confidence'] >= 50) & (self.df['confidence'] < 80)).sum()) if 'confidence' in self.df.columns else None,
                "low_confidence": int((self.df['confidence'] < 50).sum()) if 'confidence' in self.df.columns else None
            },
            "satellites": self.df['satellite'].value_counts().to_dict() if 'satellite' in self.df.columns else {},
            "day_night": self.df['daynight'].value_counts().to_dict() if 'daynight' in self.df.columns else {}
        }
        
        return stats
    
    def get_temporal_analysis(self) -> Dict:
        """Analyze fire detections over time"""
        if self.df is None or len(self.df) == 0 or 'acq_date' not in self.df.columns:
            return {"error": "No temporal data available"}
        
        # Group by date
        daily_counts = self.df.groupby('acq_date').size().reset_index(name='count')
        daily_frp = self.df.groupby('acq_date')['frp'].sum().reset_index(name='total_frp') if 'frp' in self.df.columns else None
        
        # Find peak days
        peak_day = daily_counts.loc[daily_counts['count'].idxmax()]
        
        return {
            "total_days": len(daily_counts),
            "peak_day": {
                "date": str(peak_day['acq_date']),
                "count": int(peak_day['count'])
            },
            "daily_average": float(daily_counts['count'].mean()),
            "daily_counts": daily_counts.to_dict('records')[:30],  # Last 30 days
            "daily_frp": daily_frp.to_dict('records')[:30] if daily_frp is not None else None
        }
    
    def get_hotspot_clusters(self, grid_size: float = 0.5) -> List[Dict]:
        """
        Identify fire hotspot clusters
        
        Args:
            grid_size: Grid cell size in degrees
            
        Returns:
            List of hotspot clusters
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        # Create grid cells
        self.df['lat_cell'] = (self.df['latitude'] / grid_size).round() * grid_size
        self.df['lon_cell'] = (self.df['longitude'] / grid_size).round() * grid_size
        
        # Group by grid cell
        clusters = self.df.groupby(['lat_cell', 'lon_cell']).agg({
            'latitude': 'mean',
            'longitude': 'mean',
            'frp': ['sum', 'mean', 'count'],
            'confidence': 'mean'
        }).reset_index()
        
        # Flatten column names
        clusters.columns = ['lat_cell', 'lon_cell', 'lat', 'lon', 'total_frp', 'avg_frp', 'count', 'avg_confidence']
        
        # Sort by count
        clusters = clusters.sort_values('count', ascending=False)
        
        # Convert to list of dicts
        hotspots = []
        for _, row in clusters.head(50).iterrows():  # Top 50 hotspots
            hotspots.append({
                "lat": float(row['lat']),
                "lon": float(row['lon']),
                "fire_count": int(row['count']),
                "total_frp": float(row['total_frp']),
                "avg_frp": float(row['avg_frp']),
                "avg_confidence": float(row['avg_confidence']),
                "intensity": "high" if row['count'] > 100 else "medium" if row['count'] > 50 else "low"
            })
        
        return hotspots
    
    def get_fire_details(self, lat: float, lon: float, radius: float = 0.1) -> List[Dict]:
        """
        Get detailed fire information near a point
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in degrees
            
        Returns:
            List of nearby fire detections
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        # Filter by distance
        nearby = self.df[
            (self.df['latitude'] >= lat - radius) &
            (self.df['latitude'] <= lat + radius) &
            (self.df['longitude'] >= lon - radius) &
            (self.df['longitude'] <= lon + radius)
        ]
        
        # Convert to list
        fires = []
        for _, row in nearby.head(100).iterrows():  # Limit to 100
            fires.append({
                "lat": float(row['latitude']),
                "lon": float(row['longitude']),
                "brightness": float(row.get('brightness', 0)),
                "confidence": int(row.get('confidence', 0)),
                "frp": float(row.get('frp', 0)),
                "date": str(row.get('acq_date', '')),
                "time": str(row.get('acq_time', '')),
                "satellite": str(row.get('satellite', '')),
                "instrument": str(row.get('instrument', '')),
                "day_night": str(row.get('daynight', ''))
            })
        
        return fires
