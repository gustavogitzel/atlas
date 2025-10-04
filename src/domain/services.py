"""
🧠 Domain Services - Business Logic Implementation
Pure domain logic, no infrastructure dependencies
"""

from typing import Optional, Dict, List
from datetime import datetime

from .models import (
    Region, EnvironmentalAnalysis, EnvironmentalScores, Alert,
    FireDetection, VegetationIndex, AirQuality, Temperature,
    Severity, Urgency, GameMission
)
from .ports import HDFDataRepository


class EnvironmentalAnalysisService:
    """Core business logic for environmental analysis"""
    
    def __init__(self, data_repository: HDFDataRepository):
        self.data_repository = data_repository
    
    async def analyze_region(
        self, 
        region: Region, 
        date: Optional[datetime] = None
    ) -> EnvironmentalAnalysis:
        """
        Perform complete environmental analysis
        
        Business rules:
        1. Collect all environmental data
        2. Calculate scores (0-100 scale)
        3. Generate diagnosis
        4. Create recommendations
        5. Determine urgency level
        """
        
        # Collect data from repository
        fire = await self.data_repository.get_fire_data(region, date)
        vegetation = await self.data_repository.get_vegetation_data(region, date)
        air_quality = await self.data_repository.get_air_quality_data(region, date)
        temperature = await self.data_repository.get_temperature_data(region, date)
        
        # Calculate scores
        scores = self._calculate_scores(fire, vegetation, air_quality, temperature)
        
        # Generate diagnosis
        diagnosis = self._generate_diagnosis(fire, vegetation, air_quality, temperature)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(fire, vegetation, air_quality, temperature)
        
        # Generate alerts
        alerts = self._generate_alerts(fire, vegetation, air_quality, temperature)
        
        # Determine urgency
        urgency = self._calculate_urgency(scores)
        
        # Determine season
        season = self._determine_season(date or datetime.now())
        
        return EnvironmentalAnalysis(
            region=region,
            date=date or datetime.now(),
            season=season,
            scores=scores,
            fire_detection=fire,
            vegetation=vegetation,
            air_quality=air_quality,
            temperature=temperature,
            diagnosis=diagnosis,
            recommendations=recommendations,
            alerts=alerts,
            urgency=urgency,
            data_source="unknown"  # Set by adapter
        )
    
    def _calculate_scores(
        self,
        fire: FireDetection,
        vegetation: VegetationIndex,
        air_quality: AirQuality,
        temperature: Temperature
    ) -> EnvironmentalScores:
        """Calculate environmental scores (0-100)"""
        
        # Fire safety score (inverse of severity)
        fire_score = self._fire_severity_to_score(fire.severity)
        
        # Vegetation health score
        veg_score = self._vegetation_health_to_score(vegetation.health_status)
        
        # Air quality score
        air_score = self._air_quality_to_score(air_quality.air_quality_status)
        
        # Climate stability score (based on temperature anomaly)
        climate_score = self._temperature_anomaly_to_score(temperature.mean_anomaly)
        
        # Overall score (weighted average)
        overall = (fire_score + veg_score + air_score + climate_score) / 4
        
        return EnvironmentalScores(
            overall=round(overall, 1),
            fire_safety=round(fire_score, 1),
            vegetation_health=round(veg_score, 1),
            air_quality=round(air_score, 1),
            climate_stability=round(climate_score, 1)
        )
    
    def _fire_severity_to_score(self, severity: Severity) -> float:
        """Convert fire severity to score"""
        mapping = {
            Severity.NONE: 100,
            Severity.LOW: 80,
            Severity.MODERATE: 50,
            Severity.HIGH: 25,
            Severity.CRITICAL: 0
        }
        return mapping.get(severity, 50)
    
    def _vegetation_health_to_score(self, health: str) -> float:
        """Convert vegetation health to score"""
        mapping = {
            "excellent": 100,
            "good": 80,
            "moderate": 60,
            "poor": 30,
            "critical": 0
        }
        return mapping.get(health, 50)
    
    def _air_quality_to_score(self, status: str) -> float:
        """Convert air quality status to score"""
        mapping = {
            "good": 100,
            "moderate": 75,
            "unhealthy_sensitive": 50,
            "unhealthy": 25,
            "very_unhealthy": 10,
            "hazardous": 0
        }
        return mapping.get(status, 50)
    
    def _temperature_anomaly_to_score(self, anomaly: float) -> float:
        """Convert temperature anomaly to score"""
        abs_anomaly = abs(anomaly)
        if abs_anomaly < 1:
            return 100
        elif abs_anomaly < 2:
            return 80
        elif abs_anomaly < 3:
            return 60
        elif abs_anomaly < 4:
            return 40
        else:
            return 20
    
    def _generate_diagnosis(
        self,
        fire: FireDetection,
        vegetation: VegetationIndex,
        air_quality: AirQuality,
        temperature: Temperature
    ) -> str:
        """Generate diagnostic message"""
        
        issues = []
        
        if fire.severity in [Severity.HIGH, Severity.CRITICAL]:
            issues.append(f"🔥 {fire.fire_count} focos de incêndio ativos")
        
        if vegetation.health_status in ["poor", "critical"]:
            issues.append(f"🌱 Vegetação em estado {vegetation.health_status} (NDVI: {vegetation.mean_ndvi:.2f})")
        
        if air_quality.air_quality_status in ["unhealthy", "very_unhealthy", "hazardous"]:
            issues.append(f"💨 Qualidade do ar {air_quality.air_quality_status} (AQI: {air_quality.mean_aqi:.0f})")
        
        if abs(temperature.mean_anomaly) > 2:
            issues.append(f"🌡️ Anomalia térmica de {temperature.mean_anomaly:+.1f}°C")
        
        if not issues:
            return "✅ Região em condições ambientais estáveis. Monitoramento preventivo recomendado."
        
        return "⚠️ " + " | ".join(issues)
    
    def _generate_recommendations(
        self,
        fire: FireDetection,
        vegetation: VegetationIndex,
        air_quality: AirQuality,
        temperature: Temperature
    ) -> List[str]:
        """Generate actionable recommendations"""
        
        recs = []
        
        # Fire recommendations
        if fire.severity == Severity.CRITICAL:
            recs.append("🚨 URGENTE: Mobilizar equipes de combate a incêndios imediatamente")
        elif fire.severity in [Severity.HIGH, Severity.MODERATE]:
            recs.append("🔥 Intensificar monitoramento de focos de calor e preparar brigadas")
        
        # Vegetation recommendations
        if vegetation.health_status in ["poor", "critical"]:
            recs.append("🌱 Implementar programa de recuperação de áreas degradadas")
        elif vegetation.degraded_percentage > 20:
            recs.append("🌿 Monitorar áreas com NDVI baixo para prevenção de degradação")
        
        # Air quality recommendations
        if air_quality.air_quality_status in ["unhealthy", "very_unhealthy", "hazardous"]:
            recs.append("💨 Emitir alerta de saúde pública - evitar atividades ao ar livre")
        
        # Temperature recommendations
        if temperature.mean_anomaly > 3:
            recs.append("🌡️ Anomalia térmica elevada - aumentar vigilância de incêndios")
        
        if not recs:
            recs.append("✅ Manter monitoramento contínuo e ações preventivas")
        
        return recs
    
    def _generate_alerts(
        self,
        fire: FireDetection,
        vegetation: VegetationIndex,
        air_quality: AirQuality,
        temperature: Temperature
    ) -> List[Alert]:
        """Generate specific alerts"""
        
        alerts = []
        
        if fire.fire_count > 100:
            alerts.append(Alert(
                type="fire",
                severity=Severity.CRITICAL,
                message=f"{fire.fire_count} focos ativos detectados",
                action="Mobilizar equipes de emergência"
            ))
        
        if vegetation.mean_ndvi < 0.3:
            alerts.append(Alert(
                type="vegetation",
                severity=Severity.HIGH,
                message=f"NDVI crítico: {vegetation.mean_ndvi:.2f}",
                action="Avaliar causas de degradação"
            ))
        
        if air_quality.mean_aqi > 150:
            alerts.append(Alert(
                type="air_quality",
                severity=Severity.HIGH,
                message=f"AQI perigoso: {air_quality.mean_aqi:.0f}",
                action="Emitir alerta de saúde"
            ))
        
        if abs(temperature.mean_anomaly) > 4:
            alerts.append(Alert(
                type="climate",
                severity=Severity.MODERATE,
                message=f"Anomalia térmica: {temperature.mean_anomaly:+.1f}°C",
                action="Monitorar impactos climáticos"
            ))
        
        return alerts
    
    def _calculate_urgency(self, scores: EnvironmentalScores) -> Urgency:
        """Determine urgency level based on scores"""
        
        if scores.overall < 30:
            return Urgency.CRITICAL
        elif scores.overall < 50:
            return Urgency.HIGH
        elif scores.overall < 70:
            return Urgency.MODERATE
        else:
            return Urgency.LOW
    
    def _determine_season(self, date: datetime) -> str:
        """Determine season (dry/wet) based on month"""
        # Dry season in Brazil: June to October
        return "dry" if date.month in [6, 7, 8, 9, 10] else "wet"


class GameMissionService:
    """Service for generating game missions"""
    
    def __init__(self, analysis_service: EnvironmentalAnalysisService):
        self.analysis_service = analysis_service
    
    async def generate_mission(
        self,
        region: Region,
        date: Optional[datetime] = None
    ) -> GameMission:
        """Generate game mission based on environmental analysis"""
        
        # Get analysis
        analysis = await self.analysis_service.analyze_region(region, date)
        
        # Determine mission type based on worst score
        scores = analysis.scores
        mission_type, objective, difficulty, reward = self._determine_mission_params(
            analysis.fire_detection,
            analysis.vegetation,
            analysis.air_quality,
            scores
        )
        
        # Time limit based on urgency
        time_limit = 30 if analysis.urgency == Urgency.CRITICAL else 60
        
        return GameMission(
            region=region,
            mission_type=mission_type,
            objective=objective,
            difficulty=difficulty,
            urgency=analysis.urgency,
            time_limit_minutes=time_limit,
            reward_multiplier=reward,
            current_scores=scores,
            target_improvement=20,
            tasks=analysis.recommendations
        )
    
    def _determine_mission_params(
        self,
        fire: FireDetection,
        vegetation: VegetationIndex,
        air_quality: AirQuality,
        scores: EnvironmentalScores
    ) -> tuple:
        """Determine mission parameters"""
        
        if scores.fire_safety < 50:
            return (
                "fire_control",
                f"Combater {fire.fire_count} focos de incêndio",
                "hard",
                2.0
            )
        elif scores.vegetation_health < 50:
            return (
                "reforestation",
                "Recuperar áreas degradadas",
                "medium",
                1.5
            )
        elif scores.air_quality < 50:
            return (
                "pollution_control",
                f"Melhorar qualidade do ar (AQI: {air_quality.mean_aqi:.0f})",
                "medium",
                1.3
            )
        else:
            return (
                "monitoring",
                "Monitoramento preventivo",
                "easy",
                1.0
            )
