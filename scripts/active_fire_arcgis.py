# This Python file uses the following encoding: utf-8
import requests
import os
import zipfile
import arcpy
import tempfile


# Sobreescribir los resultados
arcpy.env.overwriteOutput = True

# Urls a los active fire
openvirs_noaa = 'https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/shapes/zips/J1_VIIRS_C2_Global_24h.zip'
openvirs_snpp = 'https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/shapes/zips/SUOMI_VIIRS_C2_Global_24h.zip'
openmodis = 'https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/shapes/zips/MODIS_C6_1_Global_24h.zip'
urls_dic = [
    {'url': openvirs_noaa, 'zip': 'J1_VIIRS_C2_Global_24h.zip', 'shp': 'J1_VIIRS_C2_Global_24h.shp'},
    {'url': openvirs_snpp, 'zip': 'SUOMI_VIIRS_C2_Global_24h.zip', 'shp': 'SUOMI_VIIRS_C2_Global_24h.shp'},
    {'url': openmodis, 'zip': 'MODIS_C6_1_Global_24h.zip', 'shp': 'MODIS_C6_1_Global_24h.shp'},
]

# Area de interes
fc_clip = arcpy.GetParameterAsText(0)

# Ruta de salida
out_path = arcpy.GetParameterAsText(1)

is_pro = arcpy.GetInstallInfo()['ProductName'] == 'ArcGISPro'

# Directorio donde se almacenará el archivo ZIP descargado
pluginpath = tempfile.gettempdir()

for url in urls_dic:
    if is_pro:
        r = requests.get(url['url'], allow_redirects=True, verify=False)
        # Escribir el contenido del archivo ZIP descargado en el disco
        with open(os.path.join(pluginpath, url['zip']), 'wb') as f:
            f.write(r.content)
    else:
        import urllib2
        r = urllib2.urlopen(url['url'])
        # Escribir el contenido del archivo ZIP descargado en el disco
        with open(os.path.join(pluginpath, url['zip']), 'wb') as f:
            f.write(r.read())

    # Descomprimir el archivo ZIP en una carpeta temporal
    with zipfile.ZipFile(os.path.join(pluginpath, url['zip']), 'r') as archivo_zip:
        archivo_zip.extractall(pluginpath)
    
    # Hacer un clip por el AOI
    fc = os.path.join(pluginpath, url['shp'])
    name, ext = os.path.splitext(url['shp'])
    out_fc = os.path.join(out_path, name + '_clip')
    if is_pro:
        arcpy.PairwiseClip_analysis(fc, fc_clip, out_fc)
        p = arcpy.mp.ArcGISProject('current')
        m = p.activeMap
        m.addDataFromPath(out_fc)
    else:
        arcpy.analysis.Clip(fc, fc_clip, out_fc)
        mxd = arcpy.mapping.MapDocument("CURRENT")
        m = mxd.activeDataFrame
        layer = arcpy.mapping.Layer(out_fc)
        arcpy.mapping.AddLayer(m, layer)

    # Eliminar los archivos de scratch
    arcpy.Delete_management(os.path.join(pluginpath, url['zip']))
    arcpy.Delete_management(fc)
