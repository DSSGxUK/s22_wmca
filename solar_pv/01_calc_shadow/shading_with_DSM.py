# Run on OSGeo Shell
from qgis.core import *
from PyQt5.QtCore import QDate, QTime, QVariant
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
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry

from glob import glob
import shutil
import os
from pathlib import Path
import time
import pickle

class CalculateShading():
    """
    Compute attributes (shading, slope, aspect, area) to calculate solar pv output.
    """
    def __init__(self, DSM_PATH, HOUSE_SHP_PATH=None, crs='EPSG:27700'):
        self.PROJECT_CRS = QgsCoordinateReferenceSystem(crs)
        self.ROOT_DIR = os.getcwd() + "//"
        if not os.path.isdir(self.ROOT_DIR + "temp//"):
            os.makedirs(self.ROOT_DIR + "temp//")
        self.TEMP_PATH = self.ROOT_DIR + "temp//"
        self.clear_temp_folder()

        self.tile_name = Path(DSM_PATH).stem
        print(self.tile_name)
        
        self.DSM_path = self.convert_DSM_to_tif(DSM_PATH)
        self.extent = self.get_extent(self.DSM_path)
        self.HOUSE_SHP_PATH = self.clip_polygon(HOUSE_SHP_PATH, self.extent)

    def convert_DSM_to_tif(self, layer):
        """
        Convert .asc layers to .tif for QGIS functionality and save in DSM folder of root dir

        Input:
        layer(str): Path to .asc layer

        Output:
        (str): Path to DSM raster layer in .asc
        """
        print("Converting DSM to tif...")
        start = time.time()

        asc_to_tif_params = {
            'INPUT':layer,
            'TARGET_CRS':self.PROJECT_CRS,
            'NODATA':None,
            'COPY_SUBDATASETS':True,
            'OPTIONS':'',
            'EXTRA':'',
            'DATA_TYPE':0,
            'OUTPUT':self.TEMP_PATH + 'converted_DSM.tif'
        }

        output = processing.run("gdal:translate", asc_to_tif_params)
        
        end = time.time()
        print(f"Completed converting DSM to tif in {end-start}")
        
        return output['OUTPUT']

    def clear_temp_folder(self):
        "Clear temp folder"
        print("Clearing temp folder...")
        shutil.rmtree(self.TEMP_PATH)
        os.makedirs(self.TEMP_PATH)
        print("Temp folder cleared.")

    def calculate_slope(self, layer):
        """
        Calculate slope of DSM tile and save in slope folder of root dir.

        Input:
        layer(str): Path to DSM raster layer

        Output:
        (str): Path to slope raster layer 
        """
        print("Calculating DSM slope...")
        start = time.time()

        slope_params = {
            'INPUT':layer,
            'BAND':1,
            'SCALE':1,
            'AS_PERCENT':False,
            'COMPUTE_EDGES':False,
            'ZEVENBERGEN':False,
            'OPTIONS':'',
            'EXTRA':'',
            'OUTPUT':'TEMPORARY_OUTPUT'
        }

        output = processing.run("gdal:slope", slope_params)

        end = time.time()
        print(f"DSM slope calculated in {end-start}")

        return output['OUTPUT']

    def calculate_aspect(self, layer):
        """
        Calculate aspect of DSM tile and save in aspect folder of root dir.

        Input:
        layer(str): Path to DSM raster layer

        Output:
        (str): Path to aspect raster layer
        """
        print("Calculating DSM aspect.")
        start = time.time()

        aspect_params = {
            'INPUT': layer,
            'Z_FACTOR':1,
            'OUTPUT': 'TEMPORARY_OUTPUT'
            }

        output = processing.run("native:aspect", aspect_params)

        params = {
            'INPUT_A':output['OUTPUT'],
            'BAND_A':1,
            'INPUT_B':None,'BAND_B':None,
            'INPUT_C':None,'BAND_C':None,
            'INPUT_D':None,'BAND_D':None,
            'INPUT_E':None,'BAND_E':None,
            'INPUT_F':None,'BAND_F':None,
            'FORMULA':'A*3.14159265359/180',
            'NO_DATA':None,
            'PROJWIN':self.extent,
            'RTYPE':5,
            'OPTIONS':'',
            'EXTRA':'',
            'OUTPUT': 'TEMPORARY_OUTPUT'}
        
        output2 = processing.run("gdal:rastercalculator", params)

        end = time.time()
        print(f"DSM aspect calculated in {end-start}s")

        return output2['OUTPUT']

    def reclass(self, layer, table):
        """
        Classify each pixel in tile and save as temporary file.
        Recommended table for slope = ['0','20','1','20','40','2','40','60','3','60','','4']
        1 = 0° - 20°
        2 = 20° - 40° 
        3 = 40° - 60°
        4 = > 60°

        Recommended table for aspect = ['0','45','1','45','135','2','135','225','3','225','315','4','315','360','1']
        1 = 315° - 45°
        2 = 45° - 135°
        3 = 135° - 225°
        4 = 225° - 315°

        Input:
        layer(str): Path to raster layer
        foldername(str): 'slope' or 'aspect'
        table(list): [MIN, MAX, CLASS, MIN, MAX, CLASS, ...]

        Output:
        (str): Path to reclassed raster layer
        """
        print(f"Reclassing...")
        start = time.time()

        reclassify_params = {
            'INPUT_RASTER':layer,
            'RASTER_BAND':1,
            'TABLE':table,
            'NO_DATA':-9999,
            'RANGE_BOUNDARIES':0,
            'NODATA_FOR_MISSING':False,
            'DATA_TYPE':5,
            'OUTPUT': 'TEMPORARY_OUTPUT'
            }

        output = processing.run("native:reclassifybytable", reclassify_params)

        end = time.time()
        print(f"Completed Reclassing in {end-start}s")

        return output['OUTPUT']

    def sieve(self, layer, threshold=10):
        """
        Removes raster polygons smaller than a provided threshold size (in pixels) and replaces them with the pixel value of the largest neighbour polygon. Recommended threshold for aspect = 2px and slope = 12px

        Input:
        layer(str): Path to raster layer 
        foldername(str): Name of folder where layer sits with '//' at the end
        threshold(int): Minimum size of polygons (in pixels) to replace

        Output:
        (str): Path to sieved raster layer 
        """
        print(f"Sieving...")
        start = time.time()

        sieve_params =  {
            'INPUT': layer,
            'THRESHOLD':threshold,
            'EIGHT_CONNECTEDNESS':False,
            'NO_MASK':False,
            'MASK_LAYER':None,
            'EXTRA':'',
            'OUTPUT': 'TEMPORARY_OUTPUT'
            }

        output = processing.run("gdal:sieve", sieve_params)
        
        end = time.time()
        print(f"Completed sieving in {end-start}s")
        
        return output['OUTPUT']

    def get_extent(self, layer):
        """
        Get and format extent of raster layer.

        Input
        layer(str): Path to raster layer

        Output
        (str): Formatted extent of raster
        """
        layer = QgsRasterLayer(layer)
        
        ext = layer.extent()
        xmin = ext.xMinimum()
        xmax = ext.xMaximum()
        ymin = ext.yMinimum()
        ymax = ext.yMaximum()
        coords = "%f,%f,%f,%f [EPSG:27700]" %(xmin, xmax, ymin, ymax)

        print(f"Retrieved extent {coords}")
        return coords

    def clip_raster_by_mask(self, layer):
        """
        Clip raster with polygon vector layer

        Inputs:
        layer(str): Path to raster layer 
        mask_path(str): Path to vector layer

        Output:
        (str): Path to clipped raster layer
        """
        print(f"Clipping raster...")
        start = time.time()

        extent = self.get_extent(layer)

        clipped_mask = self.clip_polygon(self.HOUSE_SHP_PATH, extent)

        clip_params = {
            'INPUT': layer,
            'MASK': clipped_mask,
            'SOURCE_CRS':None,
            'TARGET_CRS':None,
            'TARGET_EXTENT':None,
            'NODATA':-999,
            'ALPHA_BAND':False,
            'CROP_TO_CUTLINE':True,
            'KEEP_RESOLUTION':False,
            'SET_RESOLUTION':False,
            'X_RESOLUTION':None,
            'Y_RESOLUTION':None,
            'MULTITHREADING':False,
            'OPTIONS':'',
            'DATA_TYPE':0,
            'EXTRA':'',
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }

        output = processing.run("gdal:cliprasterbymasklayer", clip_params)
        
        end = time.time()
        print(f"Completed clipping raster in {end-start}s")
        
        return output['OUTPUT']


    def clip_polygon(self, layer, extent):
        """
        Clip raster to vector layer.

        Input:
        layer(str): Path to raster layer 
        extent(str): 4-point coordinates of extent to clip with
        """
        print("Clipping polygon...")
        start = time.time()

        print(extent)

        clip_params = {
            'INPUT':layer,
            'EXTENT':extent, 
            'CLIP':True,
            'OUTPUT': 'TEMPORARY_OUTPUT'
            }
        
        output = processing.run("native:extractbyextent", clip_params)

        end = time.time()
        print(f"Completed clipping polygon in {end-start}s")

        return output['OUTPUT']

    def polygonize(self, layer, field):
        """
        Create vector polygons from raster layer and outputs as a shapefile.

        Inputs:
        layer(str): Path to clipped raster layer 
        field(str): Name of attribute column ('slope' or 'aspect')
        """
        print(f"Polygonising {field}...")
        start = time.time()

        polygonize_params = {
            'INPUT': layer,
            'BAND':1,
            'FIELD':field,
            'EIGHT_CONNECTEDNESS':False,
            'EXTRA':'',
            'OUTPUT': 'TEMPORARY_OUTPUT'
            }

        output = processing.run("gdal:polygonize", polygonize_params)

        end = time.time()
        print(f"Completed polygonising {field} in {end-start}s")

        return output['OUTPUT']

    def intersection(self, aspect_polygon, slope_polygon):
        """
        Get intersection of aspect and slope polygons to represent roof planes.

        Input:
        aspect_polygon(str): Relative path to clipped aspect shapefile from root dir
        slope_polygon(str): Relative path to clipped slope shapefile from root dir
        """
        print(f"Finding intersection of aspect and slope polygons...")
        start = time.time()
            
        intersection_params = {
            'INPUT': aspect_polygon,
            'OVERLAY':slope_polygon,
            'INPUT_FIELDS':[],
            'OVERLAY_FIELDS':[],
            'OVERLAY_FIELDS_PREFIX':'',
            'OUTPUT': 'TEMPORARY_OUTPUT'
            }
            
        output = processing.run("native:intersection", intersection_params)

        end = time.time()
        print(f"Completed finding intersection between aspect and slope polygons in {end-start}s")

        return output['OUTPUT']

    def buffer(self, layer_path, distance, output_path = 'TEMPORARY_OUTPUT'):
        """
        Computes a buffer area for all the features in an input layer. End cap style set to 'Flat', default was 'Round'.
        
        Input:
        layer_path(str): Path to vector layer for buffer
        distance(int): Buffer size in meters
        """

        print(f"Adding buffer {distance}...")
        start = time.time()

        buffer_params = {
            'INPUT': layer_path,
            'DISTANCE':distance,
            'SEGMENTS':5,
            'END_CAP_STYLE':1,
            'JOIN_STYLE':0,
            'MITER_LIMIT':2,
            'DISSOLVE':False,
            'OUTPUT': output_path
            }
        
        layer = processing.run("native:buffer", buffer_params)
        
        end = time.time()
        print(f"Added buffer in {end-start}s")
        
        return layer['OUTPUT']

    def zonal_statistics(self, layer, mask, prefix = ''):
        """
        Calculate zonal statistics within house shapefile. Only calculates mean.

        Input:
        layer(str): Path to polygon shapefile 
        raster(str): Path to raster layer (.tif)
        prefix(str): Column prefix
        """
        print(f"Computing zonal statistics {prefix}")
        start = time.time()

        stats_params = {
            'INPUT':mask,
            'INPUT_RASTER':layer,
            'RASTER_BAND':1,
            'COLUMN_PREFIX':prefix + '_',
            'STATISTICS':[2],
            'OUTPUT': self.TEMP_PATH + prefix + '.geojson'
            # 'OUTPUT': 'TEMPORARY_OUTPUT'
            }

        output = processing.run("native:zonalstatisticsfb", stats_params)

        end = time.time()
        print(f"Computed zonal statistics in {end-start}s")
        
        return output['OUTPUT']

    def merge_vector_layers(self, layerA, layerB, fields, output_path='TEMPORARY_OUTPUT'):
        """
        Merge attribute tables of vector layers.

        Input:
        layers_list(list): List of vector layers to merge.
        
        Output:
        (str): Path to merged vector layer
        """
        print("Merging vector layers...")
        start = time.time()

        params = {
            'INPUT':layerA,
            'FIELD':'fid',
            'INPUT_2':layerB,
            'FIELD_2':'fid',
            'FIELDS_TO_COPY':fields,
            'METHOD':1,
            'DISCARD_NONMATCHING':True,
            'PREFIX':'',
            'OUTPUT': output_path
            }
        
        output = processing.run("native:joinattributestable", params)

        end = time.time()
        print(f"Completed merged vector layers {end-start}s")

        return output['OUTPUT']

    def calculate_area(self, layer):
        """
        Calculate area of each polygon and replace file with added attribute.

        Input:
        layer(str): Path to vector layer to calculate area of polygons
        
        """
        print("Calculating area of layer...")
        start = time.time()

        OUTPUT_DIR = self.ROOT_DIR + 'output//roof_segments_unfiltered//'
        if not os.path.isdir(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        area_params = {
            'INPUT':layer,
            'FIELD_NAME':'AREA',
            'FIELD_TYPE':0,
            'FIELD_LENGTH':0,
            'FIELD_PRECISION':0,
            'FORMULA':'area($geometry)/cos("slope_mean" * 3.14159265359 / 180)',
            'OUTPUT': OUTPUT_DIR + self.tile_name + '.geojson'
            }

        output = processing.run("native:fieldcalculator", area_params)

        end = time.time()
        print(f"Completing calculating area of layer {end-start}s")

        return output['OUTPUT']

    def filter_polygons(self, layer):
        """
        Filter polygons for area > 5m^2, slope betweeon 0-60 degrees and aspect between 67.5 and 292.5

        Input
        layer(str): Path to vector layer
        
        Output:
        (str): Path to filtered vector layer
        """
        print("Filtering polygons based on criteria...")
        start = time.time()

        filter_params = {
            'INPUT':layer,
            'EXPRESSION':' ("AREA" > 5 AND 10 < "slope_mean" <= 60 AND 1.178097 <= "aspect_mean" <= 5.1050881) OR ("AREA" > 5 AND 0 < "slope_mean" <= 10 AND "aspect_mean" > 0)',
            'OUTPUT':self.TEMP_PATH + 'filtered_houses.geojson'
            }

        output = processing.run("native:extractbyexpression", filter_params)
        
        end = time.time()
        print(f"Completed filtering in {end-start}s")

        return output['OUTPUT']

    def calculate_shading(self, layer, mask, UTC=1):
        """
        Get average shading for spring (20/3/2022) and fall (23/9/2022) equinoxes.

        Input:
        layer(str): Path to DSM raster layer
        UTC(int): Timezone in UTC default to UK
        
        Output:
        (str): Path to vector layer with total shading (0-1) of each roof segment
        """
        print("Calcuating average shading...")
        start = time.time()

        baseraster = gdal.Open(layer)
        fillraster = baseraster.ReadAsArray().astype(float)
        fillraster = fillraster * 0.0
        
        index = 0
        
        if not os.path.isdir(self.TEMP_PATH + 'shading//'):
            os.makedirs(self.TEMP_PATH + 'shading//')

        dates_dict = {
            'spring': QDate.fromString("23-9-2022", "d-M-yyyy"),
            'winter': QDate.fromString("21-12-2022", "d-M-yyyy"),
            'summer': QDate.fromString("21-6-2022", "d-M-yyyy"),
            'fall': QDate.fromString("20-3-2022", "d-M-yyyy")
        }

        for name, date in dates_dict.items():
            print(f"Shading {name}...")
            shading_params = {
                'INPUT_DSM':layer,
                'INPUT_CDSM':None,
                'TRANS_VEG':3,
                'INPUT_TDSM':None,
                'INPUT_THEIGHT':25,
                'INPUT_HEIGHT':None,
                'INPUT_ASPECT':None,
                'UTC':UTC,
                'DST':False,
                'DATEINI':date,
                'ITERTIME':120,
                'ONE_SHADOW':False,
                'TIMEINI':QTime(12, 46, 56),
                'OUTPUT_DIR': self.TEMP_PATH + 'shading//'
                }
            
            output = processing.run("umep:Solar Radiation: Shadow Generator", shading_params)

            print(f"Shaded for {name}")

            no_of_files = os.listdir(self.TEMP_PATH + 'shading//')

            for j in range(0, no_of_files.__len__()):
                tempgdal = gdal.Open(self.TEMP_PATH + 'shading//' + no_of_files[j])
                tempraster = tempgdal.ReadAsArray().astype(float)
                fillraster = fillraster + tempraster
                tempgdal = None
                os.remove(self.TEMP_PATH + 'shading//' + no_of_files[j])

                index = index + 1 #A counter that specifies total numer of shadows in a year (2 hour resolution)

        fillraster = fillraster / index
        
        print("Saving raster...")
        self.saveraster(baseraster, self.TEMP_PATH + 'Shadow_Aggregated.tif', fillraster)

        output = self.zonal_statistics(self.TEMP_PATH + 'Shadow_Aggregated.tif', mask, 'shading')

        end = time.time()
        print(f"Completed calculating average shading in {end-start}s")
        return output

    def saveraster(self, gdal_data, filename, raster):
        rows = gdal_data.RasterYSize
        cols = gdal_data.RasterXSize

        outDs = gdal.GetDriverByName("GTiff").Create(filename, cols, rows, int(1), GDT_Float32)
        outBand = outDs.GetRasterBand(1)

        # write the data
        outBand.WriteArray(raster, 0, 0)
        # flush data to disk, set the NoData value and calculate stats
        outBand.FlushCache()
        outBand.SetNoDataValue(-9999)

        # georeference the  image and set the projection
        outDs.SetGeoTransform(gdal_data.GetGeoTransform())
        outDs.SetProjection(gdal_data.GetProjection())

    def roof_segmentation(self):
        """
        Convert DSM (.asc) to (.tif) -> Calculate slope and aspect -> Merge pixels with same slope and aspect as a roof segment

        Input:
        DSM(str): Path to DSM (.asc/.tif)

        Output:
        (str): Path to vector layer with segmented roofs.
        """
        print("Perfoming roof segmentation...")

        self.slope_path = self.calculate_slope(self.DSM_path)
        self.aspect_path = self.calculate_aspect(self.DSM_path)

        params = {
            'slope': {
                'path': self.slope_path,
                'table': ['0','20','1','20','40','2','40','60','3','60','','4'],
                'threshold': 12
            },
            'aspect' : {
                'path': self.aspect_path,
                'table': ['0','0.78539816339','1','0.78539816339','2.35619','2','2.35619','3.92699','3','3.92699','5.49779','4','5.49779','6.28319','1'],
                'threshold': 2
            }
        }

        polygon_path = []

        for x in ['slope', 'aspect']:
            reclass_layer = self.reclass(params[x]['path'], params[x]['table'])
            sieve_layer = self.sieve(reclass_layer, params[x]['threshold'])
            
            clip_layer = self.clip_raster_by_mask(sieve_layer)
            polygon_layer = self.polygonize(clip_layer, x)
            polygon_path.append(polygon_layer)

        # Get intersection
        intersection_path = self.intersection(polygon_path[0],  polygon_path[1])

        # Add buffer
        buffer_path = self.buffer(intersection_path, -0.8)
        buffer_path = self.buffer(buffer_path, 0.8)
        buffer_path = self.buffer(buffer_path, 1)
        buffer_path = self.buffer(buffer_path, -2) # added 1m buffer 

        print("Completed roof segmentation.")
        return buffer_path
    
    def filter_roof_segments(self, layer):
        """
        Filter roof segments for slope, area and shading.

        Input:
        layer(str): Path to vector layer with roof segments

        Output:
        (str): Path to vector layer with filtered roof segments
        
        """
        print("Filtering houses...")
        start = time.time()
        
        # Calculate stats
        slope_stats = self.zonal_statistics(self.slope_path, layer, 'slope')
        aspect_stats = self.zonal_statistics(self.aspect_path, layer, 'aspect')
        height_stats = self.zonal_statistics(self.DSM_path, layer, 'height')
        shading_stats = self.calculate_shading(self.DSM_path, layer)
    
        # Get final merged layer
        slope_aspect_merge = self.merge_vector_layers(slope_stats, aspect_stats, ['aspect_mean'])        
        height_merge = self.merge_vector_layers(slope_aspect_merge, height_stats, ['height_mean'])
        merged = self.merge_vector_layers(height_merge, shading_stats, ['shading_mean'])
        area = self.calculate_area(merged)

        # Add uprn
        final_layer = self.add_uprn(filtered)

        # Filter layers
        filtered = self.filter_polygons(final_layer)

        end = time.time()
        print(f"Completed filtering houses {end-start}s")
        return final_layer

    def add_uprn(self, layer):
        print("Adding UPRN...")
        start = time.time()

        OUTPUT_DIR = self.ROOT_DIR + 'output//roof_segments//'
        if not os.path.isdir(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        params = {
            'INPUT':layer,
            'PREDICATE':[5],
            'JOIN':self.HOUSE_SHP_PATH,
            'JOIN_FIELDS':['uprn','buildingNumber', 'thoroughfare', 'postcode', 'parentUPRN'],
            'METHOD':0,
            'DISCARD_NONMATCHING':False,
            'PREFIX':'',
            'OUTPUT': OUTPUT_DIR + self.tile_name + ".geojson"
            }
        output = processing.run("native:joinattributesbylocation", params)

        end = time.time()
        print(f"Completed adding UPRN {end-start}s")

        return output['OUTPUT']

    def clip_raster_by_extent(self, layer, extent):
        if not os.path.isdir(self.TEMP_PATH + 'clip_raster//'):
            os.makedirs(self.TEMP_PATH + 'clip_raster//')

        name = layer.split('.')[-2]
        print(name)

        params = {
            'INPUT':layer,
            'PROJWIN':extent,
            'OVERCRS':False,
            'NODATA':-999,
            'OPTIONS':'',
            'DATA_TYPE':0,
            'EXTRA':'',
            'OUTPUT': self.TEMP_PATH + f'clip_raster//{name}.tif'
            }
        
        output = processing.run("gdal:cliprasterbyextent", params)

        return output['OUTPUT']

def main():
    with open('/../00_compare_grid/os_mapping.pkl', 'rb') as f:
        os_mapping = pickle.load(f)
    
    DSM_DIR = "/../../data/external/DSM/"
    DSM_files = glob(DSM_DIR + "*.asc")
    print(DSM_files)

    HOUSE_DIR = "/../../data/processed/output/"
    house_files = glob(HOUSE_DIR + "*.geojson")
    house_files = [path.replace('\\', '/') for path in house_files]

    for DSM_PATH in DSM_files:
        tile_name = Path(DSM_PATH).stem.split('_')[0].upper()
        HOUSE_SHP_PATH = HOUSE_DIR + os_mapping[tile_name] + '.geojson'
        print(HOUSE_SHP_PATH)

        if HOUSE_SHP_PATH in house_files:
            program = CalculateShading(DSM_PATH, HOUSE_SHP_PATH)
            segmented_layer = program.roof_segmentation()
            filtered_layer = program.filter_roof_segments(segmented_layer)
   
    
if __name__ == "__main__":
    main()