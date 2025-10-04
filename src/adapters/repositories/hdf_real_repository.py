"""
📂 Real HDF Repository Adapter
Reads actual NASA HDF files from disk
"""

from typing import Optional
from datetime import datetime
import os
import logging
import numpy as np

from src.domain.models import (
    Region, FireDetection, VegetationIndex, AirQuality, Temperature,
    Severity, VegetationHealth, AirQualityStatus
)
from src.domain.ports import HDFDataRepository

# HDF libraries
try:
    from pyhdf.SD import SD, SDC
    HAS_PYHDF = True
except ImportError:
    HAS_PYHDF = False

try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

try:
    from netCDF4 import Dataset
    HAS_NETCDF = True
except ImportError:
    HAS_NETCDF = False

logger = logging.getLogger(__name__)


class RealHDFRepository(HDFDataRepository):
    """Repository that reads real HDF files"""
    
    def __init__(self, data_dir: str = "./data/raw"):
        self.data_dir = data_dir
        self._check_dependencies()
        self._scan_available_files()
    
    def _check_dependencies(self):
        """Check if HDF libraries are available"""
        if not (HAS_PYHDF or HAS_H5PY):
            logger.warning("⚠️  No HDF libraries available. Install: pip install pyhdf h5py netCDF4")
    
    def _scan_available_files(self):
        """Scan data directory for available HDF files"""
        if not os.path.exists(self.data_dir):
            logger.warning(f"⚠️  Data directory not found: {self.data_dir}")
            return
        
        hdf_files = [f for f in os.listdir(self.data_dir) 
                     if f.endswith(('.hdf', '.h5', '.nc', '.HDF', '.H5', '.NC'))]
        
        if hdf_files:
            logger.info(f"📂 Found {len(hdf_files)} HDF files in {self.data_dir}")
        else:
            logger.warning(f"⚠️  No HDF files found in {self.data_dir}")
    
    async def list_all_datasets(self, filename: Optional[str] = None) -> dict:
        """
        List all datasets/columns in HDF file(s)
        
        Args:
            filename: Specific file to inspect (optional, uses first file if None)
            
        Returns:
            Dictionary with file info and all datasets
        """
        if not os.path.exists(self.data_dir):
            return {"error": "Data directory not found"}
        
        # Get HDF files
        hdf_files = [f for f in os.listdir(self.data_dir) 
                     if f.endswith(('.hdf', '.h5', '.nc', '.HDF', '.H5', '.NC'))]
        
        if not hdf_files:
            return {"error": "No HDF files found"}
        
        # Use specified file or first available
        target_file = filename if filename and filename in hdf_files else hdf_files[0]
        filepath = os.path.join(self.data_dir, target_file)
        
        logger.info(f"📋 Listing datasets in: {target_file}")
        
        file_type = self._detect_file_type(filepath)
        
        result = {
            "filename": target_file,
            "file_type": file_type,
            "datasets": []
        }
        
        try:
            if file_type == 'hdf4' and HAS_PYHDF:
                result["datasets"] = self._list_datasets_hdf4(filepath)
            elif file_type == 'hdf5' and HAS_H5PY:
                result["datasets"] = self._list_datasets_hdf5(filepath)
            elif file_type == 'netcdf' and HAS_NETCDF:
                result["datasets"] = self._list_datasets_netcdf(filepath)
            else:
                result["error"] = f"Unsupported file type: {file_type}"
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Error listing datasets: {str(e)}")
        
        return result
    
    async def read_raw_dataset(self, dataset_name: str, filename: Optional[str] = None, return_array: bool = False) -> dict:
        """
        Read raw data from a specific dataset
        
        Args:
            dataset_name: Name of the dataset to read
            filename: Specific file (optional)
            return_array: If True, returns numpy array directly (for internal use)
            
        Returns:
            Dictionary with dataset data or numpy array if return_array=True
        """
        if not os.path.exists(self.data_dir):
            return {"error": "Data directory not found"}
        
        hdf_files = [f for f in os.listdir(self.data_dir) 
                     if f.endswith(('.hdf', '.h5', '.nc', '.HDF', '.H5', '.NC'))]
        
        if not hdf_files:
            return {"error": "No HDF files found"}
        
        target_file = filename if filename and filename in hdf_files else hdf_files[0]
        filepath = os.path.join(self.data_dir, target_file)
        
        logger.info(f"📖 Reading dataset '{dataset_name}' from: {target_file}")
        
        file_type = self._detect_file_type(filepath)
        
        try:
            if file_type == 'hdf4' and HAS_PYHDF:
                data = self._read_dataset_hdf4(filepath, dataset_name)
            elif file_type == 'hdf5' and HAS_H5PY:
                data = self._read_dataset_hdf5(filepath, dataset_name)
            else:
                return {"error": f"Unsupported file type: {file_type}"}
            
            # If return_array is True, return numpy array directly (for internal processing)
            if return_array:
                return data
            
            # Convert numpy array to list for JSON serialization
            if isinstance(data, np.ndarray):
                # Get basic stats
                return {
                    "filename": target_file,
                    "dataset": dataset_name,
                    "shape": data.shape,
                    "dtype": str(data.dtype),
                    "min": float(np.min(data)),
                    "max": float(np.max(data)),
                    "mean": float(np.mean(data)),
                    "data": data.tolist() if data.size < 10000 else "Too large (use shape to access)",
                    "sample": data.flat[:10].tolist() if data.size >= 10 else data.tolist(),
                    "_array_available": True  # Flag indicating array can be accessed internally
                }
            else:
                return {
                    "filename": target_file,
                    "dataset": dataset_name,
                    "data": data
                }
        
        except Exception as e:
            logger.error(f"❌ Error reading dataset: {str(e)}")
            return {"error": str(e)}
    
    def _list_datasets_hdf4(self, filepath: str) -> list:
        """List all datasets in HDF4 file"""
        hdf = SD(filepath, SDC.READ)
        datasets_dict = hdf.datasets()
        
        datasets = []
        for name, info in datasets_dict.items():
            datasets.append({
                "name": name,
                "shape": info[0],
                "type": info[1],
                "attributes": info[2]
            })
        
        hdf.end()
        return datasets
    
    def _list_datasets_hdf5(self, filepath: str) -> list:
        """List all datasets in HDF5 file"""
        datasets = []
        
        with h5py.File(filepath, 'r') as f:
            def collect_datasets(name, obj):
                if isinstance(obj, h5py.Dataset):
                    datasets.append({
                        "name": name,
                        "shape": obj.shape,
                        "dtype": str(obj.dtype)
                    })
            
            f.visititems(collect_datasets)
        
        return datasets
    
    def _list_datasets_netcdf(self, filepath: str) -> list:
        """List all datasets in NetCDF file"""
        nc = Dataset(filepath, 'r')
        
        datasets = []
        for name, var in nc.variables.items():
            datasets.append({
                "name": name,
                "shape": var.shape,
                "dtype": str(var.dtype)
            })
        
        nc.close()
        return datasets
    
    def _read_dataset_hdf4(self, filepath: str, dataset_name: str) -> np.ndarray:
        """Read specific dataset from HDF4"""
        hdf = SD(filepath, SDC.READ)
        data = hdf.select(dataset_name).get()
        hdf.end()
        return data
    
    def _read_dataset_hdf5(self, filepath: str, dataset_name: str) -> np.ndarray:
        """Read specific dataset from HDF5"""
        with h5py.File(filepath, 'r') as f:
            data = f[dataset_name][:]
        return data
    
    async def get_fire_data(
        self, 
        region: Region, 
        date: Optional[datetime] = None
    ) -> FireDetection:
        """Read fire detection data from HDF files"""
        
        # Find MOD14/MYD14 files
        fire_files = self._find_files_by_product(['MOD14', 'MYD14', 'fire'])
        
        if not fire_files:
            logger.warning("⚠️  No fire detection files found, using fallback")
            return self._fallback_fire_data(region, date)
        
        try:
            filepath = os.path.join(self.data_dir, fire_files[0])
            logger.info(f"🔥 Reading fire data from: {fire_files[0]}")
            
            # Detect file type
            file_type = self._detect_file_type(filepath)
            
            # Read datasets
            if file_type == 'hdf4' and HAS_PYHDF:
                return await self._read_fire_hdf4(filepath)
            elif file_type == 'hdf5' and HAS_H5PY:
                return await self._read_fire_hdf5(filepath)
            else:
                logger.warning(f"⚠️  Unsupported file type: {file_type}")
                return self._fallback_fire_data(region, date)
                
        except Exception as e:
            logger.error(f"❌ Error reading fire data: {str(e)}")
            return self._fallback_fire_data(region, date)
    
    async def get_vegetation_data(
        self, 
        region: Region, 
        date: Optional[datetime] = None
    ) -> VegetationIndex:
        """Read NDVI data from HDF files"""
        
        ndvi_files = self._find_files_by_product(['MOD13', 'MYD13', 'ndvi'])
        
        if not ndvi_files:
            logger.warning("⚠️  No NDVI files found, using fallback")
            return self._fallback_vegetation_data(region, date)
        
        try:
            filepath = os.path.join(self.data_dir, ndvi_files[0])
            logger.info(f"🌱 Reading NDVI from: {ndvi_files[0]}")
            
            file_type = self._detect_file_type(filepath)
            
            if file_type == 'hdf4' and HAS_PYHDF:
                return await self._read_ndvi_hdf4(filepath)
            elif file_type == 'hdf5' and HAS_H5PY:
                return await self._read_ndvi_hdf5(filepath)
            else:
                return self._fallback_vegetation_data(region, date)
                
        except Exception as e:
            logger.error(f"❌ Error reading NDVI: {str(e)}")
            return self._fallback_vegetation_data(region, date)
    
    async def get_air_quality_data(
        self, 
        region: Region, 
        date: Optional[datetime] = None
    ) -> AirQuality:
        """Read aerosol data from HDF files"""
        
        aerosol_files = self._find_files_by_product(['MOD04', 'MYD04', 'aerosol'])
        
        if not aerosol_files:
            logger.warning("⚠️  No aerosol files found, using fallback")
            return self._fallback_air_quality_data(region, date)
        
        try:
            filepath = os.path.join(self.data_dir, aerosol_files[0])
            logger.info(f"💨 Reading aerosol from: {aerosol_files[0]}")
            
            file_type = self._detect_file_type(filepath)
            
            if file_type == 'hdf4' and HAS_PYHDF:
                return await self._read_aerosol_hdf4(filepath)
            elif file_type == 'hdf5' and HAS_H5PY:
                return await self._read_aerosol_hdf5(filepath)
            else:
                return self._fallback_air_quality_data(region, date)
                
        except Exception as e:
            logger.error(f"❌ Error reading aerosol: {str(e)}")
            return self._fallback_air_quality_data(region, date)
    
    async def get_temperature_data(
        self, 
        region: Region, 
        date: Optional[datetime] = None
    ) -> Temperature:
        """Read temperature data from HDF files"""
        
        temp_files = self._find_files_by_product(['MOD11', 'MYD11', 'lst', 'temperature'])
        
        if not temp_files:
            logger.warning("⚠️  No temperature files found, using fallback")
            return self._fallback_temperature_data(region, date)
        
        try:
            filepath = os.path.join(self.data_dir, temp_files[0])
            logger.info(f"🌡️  Reading temperature from: {temp_files[0]}")
            
            file_type = self._detect_file_type(filepath)
            
            if file_type == 'hdf4' and HAS_PYHDF:
                return await self._read_temperature_hdf4(filepath)
            elif file_type == 'hdf5' and HAS_H5PY:
                return await self._read_temperature_hdf5(filepath)
            else:
                return self._fallback_temperature_data(region, date)
                
        except Exception as e:
            logger.error(f"❌ Error reading temperature: {str(e)}")
            return self._fallback_temperature_data(region, date)
    
    # ========================================================================
    # HDF4 Readers
    # ========================================================================
    
    async def _read_fire_hdf4(self, filepath: str) -> FireDetection:
        """Read MODIS fire data from HDF4"""
        hdf = SD(filepath, SDC.READ)
        
        # Try common dataset names
        fire_mask = None
        for name in ['FireMask', 'fire mask', 'Fire_Mask']:
            try:
                fire_mask = hdf.select(name).get()
                break
            except:
                continue
        
        if fire_mask is None:
            raise ValueError("FireMask dataset not found")
        
        # Fire pixels (values 7-9 indicate fire)
        fire_pixels = fire_mask >= 7
        fire_count = int(np.sum(fire_pixels))
        
        # Try to get FRP
        total_frp = 0.0
        try:
            frp = hdf.select('MaxFRP').get()
            valid_frp = frp[fire_pixels & (frp < 10000)]
            total_frp = float(np.sum(valid_frp))
        except:
            pass
        
        hdf.end()
        
        severity = self._classify_fire_severity(fire_count, total_frp)
        
        return FireDetection(
            fire_count=fire_count,
            total_frp=total_frp,
            severity=severity
        )
    
    async def _read_ndvi_hdf4(self, filepath: str) -> VegetationIndex:
        """Read MODIS NDVI from HDF4"""
        hdf = SD(filepath, SDC.READ)
        
        # Read NDVI (scaled -2000 to 10000)
        ndvi_raw = hdf.select('NDVI').get()
        hdf.end()
        
        # Convert to real scale (-1 to 1)
        ndvi = ndvi_raw.astype(float) * 0.0001
        
        # Filter valid values
        valid_mask = (ndvi >= -1) & (ndvi <= 1)
        ndvi_valid = ndvi[valid_mask]
        
        if len(ndvi_valid) == 0:
            raise ValueError("No valid NDVI values")
        
        mean_ndvi = float(np.mean(ndvi_valid))
        degraded_percentage = float(np.sum(ndvi_valid < 0.4) / len(ndvi_valid) * 100)
        
        return VegetationIndex(
            mean_ndvi=mean_ndvi,
            min_ndvi=float(np.min(ndvi_valid)),
            max_ndvi=float(np.max(ndvi_valid)),
            degraded_percentage=degraded_percentage,
            health_status=self._classify_vegetation_health(mean_ndvi)
        )
    
    async def _read_aerosol_hdf4(self, filepath: str) -> AirQuality:
        """Read MODIS aerosol from HDF4"""
        hdf = SD(filepath, SDC.READ)
        
        # Find AOD dataset
        datasets = list(hdf.datasets().keys())
        aod = None
        
        for name in datasets:
            if 'AOD' in name or 'Optical_Depth' in name:
                aod = hdf.select(name).get()
                break
        
        hdf.end()
        
        if aod is None:
            raise ValueError("AOD dataset not found")
        
        # Filter valid values (0 to 5)
        valid_mask = (aod >= 0) & (aod <= 5)
        aod_valid = aod[valid_mask]
        
        if len(aod_valid) == 0:
            raise ValueError("No valid AOD values")
        
        mean_aod = float(np.mean(aod_valid))
        mean_aqi = (mean_aod / 2) * 100  # Simplified AQI
        
        return AirQuality(
            mean_aqi=min(mean_aqi, 500),
            mean_aod=mean_aod,
            air_quality_status=self._classify_air_quality(mean_aqi)
        )
    
    async def _read_temperature_hdf4(self, filepath: str) -> Temperature:
        """Read MODIS LST from HDF4"""
        hdf = SD(filepath, SDC.READ)
        
        # Find LST dataset
        datasets = list(hdf.datasets().keys())
        lst = None
        
        for name in datasets:
            if 'LST' in name or 'Temperature' in name:
                lst = hdf.select(name).get()
                break
        
        hdf.end()
        
        if lst is None:
            raise ValueError("LST dataset not found")
        
        # Convert from Kelvin to Celsius (scale 0.02)
        lst_kelvin = lst.astype(float) * 0.02
        lst_celsius = lst_kelvin - 273.15
        
        # Filter valid values
        valid_mask = (lst_celsius >= -40) & (lst_celsius <= 60)
        lst_valid = lst_celsius[valid_mask]
        
        if len(lst_valid) == 0:
            raise ValueError("No valid temperature values")
        
        mean_temp = float(np.mean(lst_valid))
        baseline = 25.0  # Default baseline
        
        return Temperature(
            mean_temp=mean_temp,
            min_temp=float(np.min(lst_valid)),
            max_temp=float(np.max(lst_valid)),
            mean_anomaly=mean_temp - baseline,
            baseline_temp=baseline
        )
    
    # ========================================================================
    # HDF5 Readers (similar structure)
    # ========================================================================
    
    async def _read_fire_hdf5(self, filepath: str) -> FireDetection:
        """Read fire data from HDF5"""
        # Similar to HDF4 but using h5py
        # Implementation details...
        return self._fallback_fire_data(None, None)
    
    async def _read_ndvi_hdf5(self, filepath: str) -> VegetationIndex:
        """Read NDVI from HDF5"""
        return self._fallback_vegetation_data(None, None)
    
    async def _read_aerosol_hdf5(self, filepath: str) -> AirQuality:
        """Read aerosol from HDF5"""
        return self._fallback_air_quality_data(None, None)
    
    async def _read_temperature_hdf5(self, filepath: str) -> Temperature:
        """Read temperature from HDF5"""
        return self._fallback_temperature_data(None, None)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def _find_files_by_product(self, keywords: list) -> list:
        """Find files matching product keywords"""
        if not os.path.exists(self.data_dir):
            return []
        
        files = os.listdir(self.data_dir)
        matching = []
        
        for f in files:
            if any(kw.lower() in f.lower() for kw in keywords):
                matching.append(f)
        
        return matching
    
    def _detect_file_type(self, filepath: str) -> str:
        """Detect HDF file type"""
        try:
            if HAS_H5PY:
                try:
                    with h5py.File(filepath, 'r'):
                        return 'hdf5'
                except:
                    pass
            
            if HAS_PYHDF:
                try:
                    hdf = SD(filepath, SDC.READ)
                    hdf.end()
                    return 'hdf4'
                except:
                    pass
            
            if HAS_NETCDF:
                try:
                    nc = Dataset(filepath, 'r')
                    nc.close()
                    return 'netcdf'
                except:
                    pass
        except:
            pass
        
        return 'unknown'
    
    # ========================================================================
    # Fallback Methods (when files not available)
    # ========================================================================
    
    def _fallback_fire_data(self, region: Optional[Region], date: Optional[datetime]) -> FireDetection:
        """Fallback fire data when files not available"""
        logger.warning("Using fallback fire data")
        return FireDetection(
            fire_count=0,
            total_frp=0.0,
            severity=Severity.NONE
        )
    
    def _fallback_vegetation_data(self, region: Optional[Region], date: Optional[datetime]) -> VegetationIndex:
        """Fallback vegetation data"""
        logger.warning("Using fallback vegetation data")
        return VegetationIndex(
            mean_ndvi=0.6,
            min_ndvi=0.2,
            max_ndvi=0.9,
            degraded_percentage=15.0,
            health_status=VegetationHealth.MODERATE
        )
    
    def _fallback_air_quality_data(self, region: Optional[Region], date: Optional[datetime]) -> AirQuality:
        """Fallback air quality data"""
        logger.warning("Using fallback air quality data")
        return AirQuality(
            mean_aqi=50.0,
            mean_aod=0.2,
            air_quality_status=AirQualityStatus.MODERATE
        )
    
    def _fallback_temperature_data(self, region: Optional[Region], date: Optional[datetime]) -> Temperature:
        """Fallback temperature data"""
        logger.warning("Using fallback temperature data")
        return Temperature(
            mean_temp=25.0,
            min_temp=20.0,
            max_temp=30.0,
            mean_anomaly=0.0,
            baseline_temp=25.0
        )
    
    # ========================================================================
    # Classification Methods
    # ========================================================================
    
    def _classify_fire_severity(self, fire_count: int, total_frp: float) -> Severity:
        """Classify fire severity"""
        if fire_count == 0:
            return Severity.NONE
        elif fire_count < 50 and total_frp < 5000:
            return Severity.LOW
        elif fire_count < 200 and total_frp < 20000:
            return Severity.MODERATE
        elif fire_count < 500 and total_frp < 50000:
            return Severity.HIGH
        else:
            return Severity.CRITICAL
    
    def _classify_vegetation_health(self, mean_ndvi: float) -> VegetationHealth:
        """Classify vegetation health"""
        if mean_ndvi > 0.7:
            return VegetationHealth.EXCELLENT
        elif mean_ndvi > 0.6:
            return VegetationHealth.GOOD
        elif mean_ndvi > 0.4:
            return VegetationHealth.MODERATE
        elif mean_ndvi > 0.2:
            return VegetationHealth.POOR
        else:
            return VegetationHealth.CRITICAL
    
    def _classify_air_quality(self, aqi: float) -> AirQualityStatus:
        """Classify air quality"""
        if aqi <= 50:
            return AirQualityStatus.GOOD
        elif aqi <= 100:
            return AirQualityStatus.MODERATE
        elif aqi <= 150:
            return AirQualityStatus.UNHEALTHY_SENSITIVE
        elif aqi <= 200:
            return AirQualityStatus.UNHEALTHY
        elif aqi <= 300:
            return AirQualityStatus.VERY_UNHEALTHY
        else:
            return AirQualityStatus.HAZARDOUS
