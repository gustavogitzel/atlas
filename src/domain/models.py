"""
🎯 Domain Models - Core Business Entities
Pure Python, no external dependencies
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum


class Severity(str, Enum):
    """Fire severity levels"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class VegetationHealth(str, Enum):
    """Vegetation health status"""
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    CRITICAL = "critical"


class AirQualityStatus(str, Enum):
    """Air quality classification"""
    GOOD = "good"
    MODERATE = "moderate"
    UNHEALTHY_SENSITIVE = "unhealthy_sensitive"
    UNHEALTHY = "unhealthy"
    VERY_UNHEALTHY = "very_unhealthy"
    HAZARDOUS = "hazardous"


class Urgency(str, Enum):
    """Alert urgency levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Region:
    """Geographic region entity"""
    code: str
    name: str
    bounds: tuple  # (lat_min, lon_min, lat_max, lon_max)
    baseline_ndvi: float
    baseline_temp: float


@dataclass
class FireDetection:
    """Fire detection data"""
    fire_count: int
    total_frp: float  # Fire Radiative Power (MW)
    severity: Severity
    confidence: Optional[List[float]] = None
    fire_mask: Optional[List[List[bool]]] = None


@dataclass
class VegetationIndex:
    """NDVI vegetation data"""
    mean_ndvi: float
    min_ndvi: float
    max_ndvi: float
    degraded_percentage: float
    health_status: VegetationHealth
    ndvi_grid: Optional[List[List[float]]] = None


@dataclass
class AirQuality:
    """Air quality data"""
    mean_aqi: float
    mean_aod: float  # Aerosol Optical Depth
    mean_co: Optional[float] = None  # CO concentration
    air_quality_status: AirQualityStatus = AirQualityStatus.MODERATE
    aqi_grid: Optional[List[List[float]]] = None


@dataclass
class Temperature:
    """Temperature data"""
    mean_temp: float
    min_temp: float
    max_temp: float
    mean_anomaly: float
    baseline_temp: float
    temperature_grid: Optional[List[List[float]]] = None


@dataclass
class EnvironmentalScores:
    """Calculated environmental scores (0-100)"""
    overall: float
    fire_safety: float
    vegetation_health: float
    air_quality: float
    climate_stability: float


@dataclass
class Alert:
    """Environmental alert"""
    type: str  # fire, vegetation, air_quality, climate
    severity: Severity
    message: str
    action: str


@dataclass
class EnvironmentalAnalysis:
    """Complete environmental analysis result"""
    region: Region
    date: datetime
    season: str  # dry or wet
    scores: EnvironmentalScores
    fire_detection: FireDetection
    vegetation: VegetationIndex
    air_quality: AirQuality
    temperature: Temperature
    diagnosis: str
    recommendations: List[str]
    alerts: List[Alert]
    urgency: Urgency
    data_source: str  # real_hdf, mock, hybrid


@dataclass
class GameMission:
    """Game mission based on real data"""
    region: Region
    mission_type: str
    objective: str
    difficulty: str
    urgency: Urgency
    time_limit_minutes: int
    reward_multiplier: float
    current_scores: EnvironmentalScores
    target_improvement: int
    tasks: List[str]
