# Run on OSGeo Shell
from qgis.core import *
from PyQt5.QtCore import QDate, QTime
import sys

# Initialize QGIS Application
QgsApplication.setPrefixPath("C://OSGeo4W64//apps//qgis", True)
app = QgsApplication([], True)
app.initQgis()

# Add the path to Processing framework
sys.path.append('C://Program Files//QGIS 3.24.3//apps//qgis//python//plugins')
sys.path.append('C://Users//lilia//AppData//Roaming//QGIS//QGIS3//profiles//default//python//plugins')

# Import UMEP
from processing_umep.processing_umep_provider import ProcessingUMEPProvider
umep_provider = ProcessingUMEPProvider()
QgsApplication.processingRegistry().addProvider(umep_provider)

# Import and initialize Processing framework
from processing.core.Processing import Processing
Processing.initialize()

import processing
from osgeo import gdal
from osgeo.gdalconst import *

import pandas as pd
from glob import glob
import shutil
import os
from pathlib import Path
import time

from shading_with_DSM import CalculateShading

class ApproximateShading(CalculateShading):
    def __init__(self, HOUSE_SHP_PATH, crs='EPSG:27700'):
        self.PROJECT_CRS = QgsCoordinateReferenceSystem(crs)
        self.ROOT_DIR = os.getcwd() + "//"
        
        self.TEMP_PATH = self.ROOT_DIR + "temp//"
        if not os.path.isdir(self.TEMP_PATH):
            os.makedirs(self.TEMP_PATH)
        # self.clear_temp_folder()
          
        self.HOUSE_SHP_PATH = HOUSE_SHP_PATH
        self.extent = self.extract_extent(self.HOUSE_SHP_PATH)
        self.tile_name = Path(HOUSE_SHP_PATH).stem
        print(self.tile_name)     
        
    def build_pseudo_DSM(self, building_height, topology_area):
        """
        Create pseudo-DSM from building height.

        Input
        building_height(str): Path to building height attribute file
        topology_area(str): Path to topology area file

        Output
        (str): Path to pseudo-DSM
        
        """
        print("Building pseudo DSM...")
        start = time.time()

        building_df = pd.read_csv(
            building_height, 
            header=None,
            names= ['fid','OS_TOPO_TOID_VERSION','BHA_ProcessDate','TileRef', 'AbsHMin', 'AbsH2','AbsHMax','RelH2','RelHMax','BHA_Conf'],
            on_bad_lines='skip'
            )
        building_df.head()
        building_df = building_df[['fid', 'AbsHMax']]

        building_df.to_csv(self.TEMP_PATH + 'building_height.csv', index=False)

        params = {
            'INPUT':self.TEMP_PATH + 'building_height.csv',
            'FIELDS_MAPPING':[{'expression': '"fid"','length': 0,'name': 'fid','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'expression': '"AbsHMax"','length': 0,'name': 'AbsHMax','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'OUTPUT':'TEMPORARY_OUTPUT'
            }
        building_refactored = processing.run("native:refactorfields", params)

        params = {
            'INPUT': topology_area + '|layername=TopographicArea',
            'FIELD':'fid',
            'INPUT_2':building_refactored['OUTPUT'],
            'FIELD_2':'fid',
            'FIELDS_TO_COPY':['AbsHMax'],
            'METHOD':1,
            'DISCARD_NONMATCHING':True,
            'PREFIX':'',
            'OUTPUT': self.TEMP_PATH + 'topo.geojson'
            # 'OUTPUT': 'TEMPORARY_OUTPUT'
            }
        
        output = processing.run("native:joinattributestable", params)

        self.pseudo_DSM = self.rasterize(output['OUTPUT']) 

        end = time.time()
        print(f"Completed building pseudo DSM in {end-start}s")

        return self.pseudo_DSM
    
    def extract_extent(self, layer):
        """
        Get and format extent from vector layer.

        Input
        layer(str): Path to vector layer

        Output
        ext(str): Extent of vector layer
        
        """

        output = processing.run('qgis:reprojectlayer', {
            'INPUT':layer, 
            'TARGET_CRS': 'EPSG:27700', 
            'OUTPUT': self.TEMP_PATH + 'reprojected.geojson'
            })

        ext = QgsVectorLayer(output['OUTPUT'], '', 'ogr' ).extent()
        ext = f"{ext.xMinimum()},{ext.xMaximum()},{ext.yMinimum()},{ext.yMaximum()} [EPSG:27700]"

        print(f"Retrieved extent {ext}.")
        return ext

    def rasterize(self, layer):
        """
        Convert vector layer to pseudo DSM raster layer.

        Input
        layer(str): Path to vector layer

        Output
        (str): Path to raster layer
        """
        print('Rasterising vector layer...')
        start = time.time()

        params = {
            'INPUT':layer,
            'FIELD':'AbsHMax',
            'BURN':0,
            'USE_Z':False,
            'UNITS':1,
            'WIDTH':0.5,
            'HEIGHT':0.5,
            'EXTENT':self.extent,
            'NODATA':0,
            'OPTIONS':'',
            'DATA_TYPE':5,
            'INIT':0,
            'INVERT':False,
            'EXTRA':'',
            'OUTPUT': self.TEMP_PATH + 'pseudoDSM.tif'
            # 'OUTPUT':'TEMPORARY_OUTPUT'
            }

        output = processing.run("gdal:rasterize", params)

        end = time.time()
        print(f"Completed rasterising in {end-start}s")

        return output['OUTPUT']

    def filter_houses(self, filename):
        """
        Calculate shading on rooftops and export as vector layer.

        Input:
        layer(str): Path to vector layer

        Output:
        merged(str): Path to merged vector layer
        
        """
        output_path = self.ROOT_DIR + 'output//no_DSM//'
        if not os.path.isdir(output_path):
            os.makedirs(output_path)

        shading_stats = self.calculate_shading(self.pseudo_DSM, self.HOUSE_SHP_PATH)
        
        params = {
            'INPUT': shading_stats,
            'FIELDS':['uprn','postcode','buildingNumber','thoroughfare','parentUPRN','calculatedAreaValue','AbsHMax','shading_mean'],
            'OUTPUT':output_path + f"{filename}.geojson"
            }
        output = processing.run("native:retainfields", params)
        
        return output['OUTPUT']


def main(): 
    TOPOLOGY_DIR = "../../data/external/topology/"
    BUILDING_HEIGHT_DIR = "../../data/external/building_height/"
    BUILDING_FOOTPRINT_DIR = "../../data/processed/output/"

    footprint_files = glob(BUILDING_FOOTPRINT_DIR + "*.geojson")
    footprint_files = [path.replace('\\', '/') for path in footprint_files]

    for path in footprint_files:
        filename = Path(path).stem
        topology_path = TOPOLOGY_DIR + f"5882272-{filename}.gml"
        building_path = BUILDING_HEIGHT_DIR + f"{filename}.csv"
        program = ApproximateShading(path)
        program.build_pseudo_DSM(building_path, topology_path)
        program.filter_houses(filename)
        

if __name__ == "__main__":
    main()