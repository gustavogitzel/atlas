"""
🔌 Domain Ports - Interfaces (Hexagon boundaries)
Define contracts without implementation
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime

from .models import (
    Region, FireDetection, VegetationIndex, AirQuality, 
    Temperature, EnvironmentalAnalysis, GameMission
)


class HDFDataRepository(ABC):
    """Port: Data access interface"""
    
    @abstractmethod
    async def get_fire_data(self, region: Region, date: Optional[datetime] = None) -> FireDetection:
        """Retrieve fire detection data"""
        pass
    
    @abstractmethod
    async def get_vegetation_data(self, region: Region, date: Optional[datetime] = None) -> VegetationIndex:
        """Retrieve vegetation index data"""
        pass
    
    @abstractmethod
    async def get_air_quality_data(self, region: Region, date: Optional[datetime] = None) -> AirQuality:
        """Retrieve air quality data"""
        pass
    
    @abstractmethod
    async def get_temperature_data(self, region: Region, date: Optional[datetime] = None) -> Temperature:
        """Retrieve temperature data"""
        pass


class RegionRepository(ABC):
    """Port: Region data access"""
    
    @abstractmethod
    async def get_region(self, code: str) -> Optional[Region]:
        """Get region by code"""
        pass
    
    @abstractmethod
    async def list_regions(self) -> List[Region]:
        """List all available regions"""
        pass


class AnalysisService(ABC):
    """Port: Analysis service interface"""
    
    @abstractmethod
    async def analyze_region(
        self, 
        region: Region, 
        date: Optional[datetime] = None
    ) -> EnvironmentalAnalysis:
        """Perform complete environmental analysis"""
        pass
    
    @abstractmethod
    async def compare_regions(self) -> Dict[str, EnvironmentalAnalysis]:
        """Compare all regions"""
        pass
    
    @abstractmethod
    async def generate_game_mission(
        self, 
        region: Region, 
        date: Optional[datetime] = None
    ) -> GameMission:
        """Generate game mission based on real data"""
        pass


class CachePort(ABC):
    """Port: Caching interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict]:
        """Get cached value"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Dict, ttl: int = 300):
        """Set cached value with TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        """Delete cached value"""
        pass


class StoragePort(ABC):
    """Port: File storage interface (local, S3, etc)"""
    
    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[str]:
        """List available HDF files"""
        pass
    
    @abstractmethod
    async def read_file(self, filepath: str) -> bytes:
        """Read file content"""
        pass
    
    @abstractmethod
    async def file_exists(self, filepath: str) -> bool:
        """Check if file exists"""
        pass
