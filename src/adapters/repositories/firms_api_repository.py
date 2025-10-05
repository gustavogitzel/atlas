"""
🛰️ NASA FIRMS API Repository
Fetches fire detection data from NASA FIRMS (Fire Information for Resource Management System)
API Documentation: https://firms.modaps.eosdis.nasa.gov/api/
"""

import requests
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import io
import time
import os

logger = logging.getLogger(__name__)


class FirmsAPIRepository:
    """Repository for NASA FIRMS API fire data"""
    
    # API Configuration
    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    API_KEY = "f88006d36b850babbc1dbd32ed0c394a"
    
    # Data sources
    SOURCES = {
        "MODIS_SP": "MODIS (Terra & Aqua) - South America",
        "VIIRS_SNPP_SP": "VIIRS S-NPP - South America",
        "VIIRS_NOAA20_SP": "VIIRS NOAA-20 - South America"
    }
    
    def __init__(self, cache_data: bool = True, data_dir: str = "./data/raw"):
        """
        Initialize FIRMS API repository
        
        Args:
            cache_data: Whether to cache data in memory (default: True)
            data_dir: Directory containing local CSV files (default: ./data/raw)
        """
        self.cache_data = cache_data
        self.data_dir = data_dir
        self.df = None
        self._last_fetch = None
        logger.info("🛰️ NASA FIRMS API Repository initialized")
    
    def fetch_date_range(
        self,
        start_date: str,
        end_date: str,
        source: str = "MODIS_SP",
        area: str = "world"
    ) -> pd.DataFrame:
        """
        Fetch fire data for a date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            source: Data source (MODIS_SP, VIIRS_SNPP_SP, VIIRS_NOAA20_SP)
            area: Geographic area (world, or coordinates)
            
        Returns:
            DataFrame with fire detections
        """
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # FIRMS API limits to 10 days per request
        # We need to split into chunks
        all_data = []
        current = start
        
        while current <= end:
            # Calculate chunk end (max 10 days)
            chunk_end = min(current + timedelta(days=9), end)
            
            # Calculate days difference
            days = (chunk_end - current).days + 1
            
            # Build API URL
            url = f"{self.BASE_URL}/{self.API_KEY}/{source}/{area}/{days}/{current.strftime('%Y-%m-%d')}"
            
            logger.info(f"📡 Fetching {source} data from {current.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")
            
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Parse CSV response
                if response.text.strip():
                    df_chunk = pd.read_csv(io.StringIO(response.text))
                    all_data.append(df_chunk)
                    logger.info(f"✅ Fetched {len(df_chunk)} fire detections")
                else:
                    logger.warning(f"⚠️ No data returned for {current.strftime('%Y-%m-%d')}")
                
                # Rate limiting - be nice to NASA's servers
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error fetching data: {str(e)}")
                # Continue with next chunk even if one fails
            
            # Move to next chunk
            current = chunk_end + timedelta(days=1)
        
        # Combine all chunks
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"🎉 Total fire detections fetched: {len(combined_df)}")
            return combined_df
        else:
            logger.warning("⚠️ No data fetched")
            return pd.DataFrame()
    
    def fetch_recent_days(self, days: int = 1, source: str = "MODIS_SP") -> pd.DataFrame:
        """
        Fetch fire data for recent days
        
        Args:
            days: Number of recent days (1-10)
            source: Data source
            
        Returns:
            DataFrame with fire detections
        """
        if days < 1 or days > 10:
            raise ValueError("Days must be between 1 and 10")
        
        url = f"{self.BASE_URL}/{self.API_KEY}/{source}/world/{days}"
        
        logger.info(f"📡 Fetching last {days} days of {source} data")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            if response.text.strip():
                df = pd.read_csv(io.StringIO(response.text))
                logger.info(f"✅ Fetched {len(df)} fire detections")
                return df
            else:
                logger.warning("⚠️ No data returned")
                return pd.DataFrame()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching data: {str(e)}")
            return pd.DataFrame()
    
    def _load_from_local_csv(self, csv_filename: str = "fire_archive_M-C61_669832.csv") -> pd.DataFrame:
        """
        Load fire data from local CSV file
        
        Args:
            csv_filename: Name of the CSV file to load
            
        Returns:
            DataFrame with fire detections
        """
        csv_path = os.path.join(self.data_dir, csv_filename)
        
        if not os.path.exists(csv_path):
            logger.error(f"❌ CSV file not found: {csv_path}")
            return pd.DataFrame()
        
        try:
            logger.info(f"📂 Loading data from local CSV: {csv_filename}")
            df = pd.read_csv(csv_path)
            logger.info(f"✅ Loaded {len(df)} fire detections from local file")
            return df
        except Exception as e:
            logger.error(f"❌ Error loading CSV file: {str(e)}")
            return pd.DataFrame()
    
    def load_historical_data(
        self,
        start_date: str = "2004-07-22",
        end_date: str = "2004-12-04",
        sources: Optional[List[str]] = None,
        use_local_csv: Optional[bool] = None
    ):
        """
        Load historical data and cache it
        
        Args:
            start_date: Start date (default: 2004-07-22)
            end_date: End date (default: 2004-12-04)
            sources: List of sources to fetch (default: MODIS_SP only)
            use_local_csv: Force use of local CSV (auto-detect if None)
        """
        if sources is None:
            sources = ["MODIS_SP"]
        
        logger.info(f"🚀 Loading historical data from {start_date} to {end_date}")
        
        # Auto-detect: Use local CSV for year 2004
        if use_local_csv is None:
            year = int(start_date.split('-')[0])
            use_local_csv = (year == 2004)
        
        if use_local_csv:
            logger.info("📂 Using local CSV file for 2004 data")
            df = self._load_from_local_csv("fire_archive_M-C61_669832.csv")
            
            if not df.empty:
                # Filter by date range
                if 'acq_date' in df.columns:
                    df = df[(df['acq_date'] >= start_date) & (df['acq_date'] <= end_date)]
                    logger.info(f"🔍 Filtered to date range: {len(df)} detections")
                
                self.df = df
                self._last_fetch = datetime.now()
                logger.info(f"✅ Historical data loaded from CSV: {len(self.df)} fire detections")
            else:
                logger.error("❌ Failed to load data from CSV")
                self.df = pd.DataFrame()
        else:
            # Fetch from NASA FIRMS API
            all_dfs = []
            for source in sources:
                logger.info(f"📡 Fetching {source} data from NASA FIRMS API...")
                df = self.fetch_date_range(start_date, end_date, source=source)
                if not df.empty:
                    all_dfs.append(df)
            
            if all_dfs:
                self.df = pd.concat(all_dfs, ignore_index=True)
                
                # Remove duplicates (same location, date, time)
                if not self.df.empty:
                    initial_count = len(self.df)
                    self.df = self.df.drop_duplicates(
                        subset=['latitude', 'longitude', 'acq_date', 'acq_time'],
                        keep='first'
                    )
                    duplicates_removed = initial_count - len(self.df)
                    if duplicates_removed > 0:
                        logger.info(f"🧹 Removed {duplicates_removed} duplicate detections")
                
                self._last_fetch = datetime.now()
                logger.info(f"✅ Historical data loaded from API: {len(self.df)} fire detections")
            else:
                logger.error("❌ Failed to load historical data from API")
                self.df = pd.DataFrame()
    
    def _ensure_data_loaded(self):
        """Lazy load data if not already loaded"""
        if self.df is None or self.df.empty:
            logger.info("📂 Lazy loading fire data from CSV...")
            self.load_historical_data(
                start_date="2004-07-22",
                end_date="2004-12-04"
            )
    
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
        self._ensure_data_loaded()
        
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
            logger.info(f"Sampled {max_points} from {len(filtered)} points")
        
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
        self._ensure_data_loaded()
        
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
        self._ensure_data_loaded()
        
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
            "daily_counts": daily_counts.to_dict('records'),
            "daily_frp": daily_frp.to_dict('records') if daily_frp is not None else None
        }
    
    def get_hotspot_clusters(self, grid_size: float = 0.5) -> List[Dict]:
        """
        Identify fire hotspot clusters
        
        Args:
            grid_size: Grid cell size in degrees
            
        Returns:
            List of hotspot clusters
        """
        self._ensure_data_loaded()
        
        if self.df is None or len(self.df) == 0:
            return []
        
        # Create grid cells
        df_copy = self.df.copy()
        df_copy['lat_cell'] = (df_copy['latitude'] / grid_size).round() * grid_size
        df_copy['lon_cell'] = (df_copy['longitude'] / grid_size).round() * grid_size
        
        # Group by grid cell
        clusters = df_copy.groupby(['lat_cell', 'lon_cell']).agg({
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
        self._ensure_data_loaded()
        
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
    
    def refresh_data(self, days: int = 1):
        """
        Refresh data with recent detections
        
        Args:
            days: Number of recent days to fetch (1-10)
        """
        logger.info(f"🔄 Refreshing data with last {days} days")
        
        recent_df = self.fetch_recent_days(days=days)
        
        if not recent_df.empty:
            if self.df is None or self.df.empty:
                self.df = recent_df
            else:
                # Append and remove duplicates
                self.df = pd.concat([self.df, recent_df], ignore_index=True)
                self.df = self.df.drop_duplicates(
                    subset=['latitude', 'longitude', 'acq_date', 'acq_time'],
                    keep='last'
                )
            
            self._last_fetch = datetime.now()
            logger.info(f"✅ Data refreshed: {len(self.df)} total detections")
