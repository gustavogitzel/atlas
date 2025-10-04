"""
📍 Region Repository Adapter
In-memory implementation (can be replaced with DB)
"""

from typing import Optional, List, Dict

from src.domain.models import Region
from src.domain.ports import RegionRepository


class InMemoryRegionRepository(RegionRepository):
    """In-memory region repository"""
    
    REGIONS: Dict[str, Region] = {
        'amazonia': Region(
            code='amazonia',
            name='Amazônia',
            bounds=(-10, -73, 5, -50),
            baseline_ndvi=0.75,
            baseline_temp=26.0
        ),
        'cerrado': Region(
            code='cerrado',
            name='Cerrado',
            bounds=(-24, -60, -10, -41),
            baseline_ndvi=0.55,
            baseline_temp=24.0
        ),
        'mata_atlantica': Region(
            code='mata_atlantica',
            name='Mata Atlântica',
            bounds=(-30, -52, -5, -34),
            baseline_ndvi=0.70,
            baseline_temp=22.0
        ),
        'pantanal': Region(
            code='pantanal',
            name='Pantanal',
            bounds=(-22, -58, -16, -55),
            baseline_ndvi=0.60,
            baseline_temp=25.0
        ),
        'caatinga': Region(
            code='caatinga',
            name='Caatinga',
            bounds=(-17, -45, -3, -35),
            baseline_ndvi=0.35,
            baseline_temp=27.0
        )
    }
    
    async def get_region(self, code: str) -> Optional[Region]:
        """Get region by code"""
        return self.REGIONS.get(code)
    
    async def list_regions(self) -> List[Region]:
        """List all regions"""
        return list(self.REGIONS.values())
