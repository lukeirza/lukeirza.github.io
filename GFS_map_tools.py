# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 17:40:16 2021

@author: lukei
"""

import datetime
import xarray as xr
import numpy as np
import matplotlib
import cartopy
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import geojsoncontour
import folium
from folium import plugins
import branca
import geojson

#Get the nearest completed runtime and date. If none completed today, use last completed yeaterday.
def present_runtime_calc():
    present_1 = datetime.datetime.utcnow()
    present_2 = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    if int(present_1.strftime('%H')) >= 6:
        present_date = present_1.strftime('%Y%m%d')
        runtime = int(present_1.strftime('%H'))
        if runtime < 12:
            runtime = '00'
        elif runtime >= 12 and runtime < 18:
            runtime = '06'
        elif runtime >= 18:
            runtime = '12'
    else:
        present_date = present_2.strftime('%Y%m%d')
        runtime = '18'
    return present_date, runtime

#create the base url using the current time data
def gfswave_cdf_base_url (present_date, runtime):
    base_url = 'https://nomads.ncep.noaa.gov/dods/wave/gfswave/'+present_date+'/'
    return base_url

#create a funtion to name different region files in the directory
def gfswave_region_files(runtime):
    regions = {'glo16' : 'gfswave.global.0p16_'+runtime+'z'
    ,'glo25' : 'gfswave.global.0p25_'+runtime+'z'
    ,'gsouth' : 'gfswave.gsouth.0p25_'+runtime+'z'
    ,'wcoast' : 'gfswave.wcoast.0p16_'+runtime+'z'
    ,'atlocn' : 'gfswave.atlocn.0p16_'+runtime+'z'
    ,'epacif' : 'gfswave.epacif.0p16_'+runtime+'z'
    , 'arctic' : 'gfswave.arctic.9km_'+runtime+'z'}
    return regions

#function to return full urls for each region
def gfswave_region_url(present_date, runtime, region):
    base_url = gfswave_cdf_base_url (present_date, runtime)
    regions= gfswave_region_files(runtime)
    return base_url+regions[region]

#convert netCDF np.datetime values into unix milliseconds timestamp. This is useful for the final visualization..
def return_unix_time(numpy_datetime_64):
    unix_time = numpy_datetime_64.astype(np.timedelta64) / np.timedelta64(1, 'ms')
    return unix_time.astype('int64')

#convert netCDF np.datetime values into unix milliseconds timestamp. This is useful for the final visualization..
def convert_unix(nc, time_name):
    nc.coords['time'] = (nc.coords[time_name].astype(np.timedelta64) / np.timedelta64(1, 'ms'))
    nc.coords['time'] = nc.coords['time'].astype(np.int64)
    nc = nc.sortby(nc.time)
    return nc

#convert 360 lon into 180 lon on global datasets. 
def convert_360_180_glo(nc):
    t = 0
    try: 
        lon_180 = nc.sel(lon = 180)
    except:
        t += 1
    nc.coords['lon'] = (nc.coords['lon'] + 180) % 360 - 180
    if t==0:
        nc = xr.concat([nc, lon_180], dim="lon")
    else:
        pass
    nc = nc.sortby(nc.lon)
    return nc

#function to convert units in the netCDF file
def convert_units(data_array, conversion_factor):
    data_array.values = data_array.values * conversion_factor
    return data_array

#Define a funtion to plot data as contours
def contourplot_mercator(data_array, levels, color_pallette, central_lon):
    #setup the plot axes. Mercator Projection is used.
    ax = plt.axes(projection=cartopy.crs.Mercator(central_longitude = central_lon))
    #showing coastlines to test the projection.
    #ax.coastlines(resolution='10m')
  
    #Get the colormap with as many colors as levels. commented out code to reverse it.
    #colormap = matplotlib.cm.get_cmap("brewer_Spectral_11", len(levels))
    colormap = matplotlib.cm.get_cmap(color_pallette, len(levels))
    #colormap = colormap.reversed()
    
    #explictly describe the x and  y coords. Mesh them together for matplotlib. 
    y = data_array.coords['lat'][:]
    x = data_array.coords['lon'][:]
    lons, lats = np.meshgrid(x,y)
    
    #Plot the data
    contourf = plt.contourf(lons, lats, data_array
                              , axes=ax
                              , cmap=colormap
                              , levels=levels
                              , extend='max'
                              , transform=ccrs.PlateCarree()
                              )
    #plt.clf()
    #plt.cla()
    return contourf

#Define a function to convert controur plots into geojson
def contourf_to_geojson(contourf):
    geo_json = geojsoncontour.contourf_to_geojson(
        contourf=contourf
        , min_angle_deg=0.1
        , stroke_width=0.5
        , fill_opacity=0.8)
    return geo_json

#This edits the geojson so that there is a 'style' property with all of the right keys for folium. 
def style_function(feature):
    feature['properties']['style'] = {
        'color': feature['properties']['stroke'], 
        'weight': feature['properties']['stroke-width'], 
        'fillColor': feature['properties']['fill'],
        'fillOpacity': feature['properties']['fill-opacity'], 
        'opacity': feature['properties']['stroke-opacity'], 
        'smoothFactor':0.1, 'interactive' : False
        }
    return
    
#define a function that return geojson features
def geojson_from_netcdf(data_array, levels, color_pallette, central_lon, t):
    print('Processing timestamp: ', t)
    geo_json = contourplot_mercator(data_array.sel(time = t), levels, color_pallette, central_lon)
    geo_json = contourf_to_geojson(geo_json)
    plt.close()
    #Converts the geojson string into an indexable dict-like object
    geo_json = geojson.loads(geo_json)
    for f in geo_json['features']:
        l_coords = len(f['geometry']['coordinates'])
        f['properties']['times'] = [t]*l_coords
        style_function(f)
    #insert a bounding box to be displayed at all times. 
    print(t, 'Complete.')
    return geo_json

#create a branca element that can be added to folium
def step_legend(color_pallette, levels, vmin, vmax, caption):
    colormap = matplotlib.cm.get_cmap(color_pallette, len(levels))
    #Pull the rgb values from the colormap and convert to hexcodes.
    cm_colors = []
    for i in range(colormap.N):
        rgb = colormap(i)[:3] # will return rgba, we take only first 3 so we get rgb
        cm_colors.append(matplotlib.colors.rgb2hex(rgb))
    
    #Pass the hexcodes to branca to make a legend. 
    step = branca.colormap.StepColormap(colors=cm_colors
                            ,vmin=vmin
                            ,vmax=vmax
                            ,index=levels
                            ,caption=caption
                            )
    return step

#create a bounding box using geojson
def geojson_box(minlon, maxlon, minlat, maxlat, popup_html):#, t):
    minlon = str(minlon)
    maxlon = str(maxlon)
    minlat = str(minlat)
    maxlat = str(maxlat)
    box = {
          "type": "Feature",
          "properties": {"popup":popup_html},
          "geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                [
                  minlon,
                  minlat
                ],
                [
                  maxlon,
                  minlat
                ],
                [
                  maxlon,
                  maxlat
                ],
                [
                  minlon,
                  maxlat
                ],
                [
                  minlon,
                  minlat
                ]
              ]
            ]
          }
        }
    #l_coords = len(box['geometry']['coordinates'])
    #box['properties']['times'] = t
    return box

#Define a function to iterate through all points in an array
def iteray(lats, lons):
    lon_lat = [[lon, lat] for lat in lats for lon in lons]
    return lon_lat

#Define an arrow generating coordinate function
def arrow_coordinates(deg_dir, lat, lon, magnitude):
    rad_dir = deg_dir * (np.pi/180)
    lat_t = np.sin(rad_dir)*magnitude
    lon_t = np.cos(rad_dir)*magnitude
    head_1_lat_t = np.sin(rad_dir+(np.pi/4))*(magnitude/2)
    head_1_lon_t = np.cos(rad_dir+(np.pi/4))*(magnitude/2)
    head_2_lat_t = np.sin(rad_dir-(np.pi/4))*(magnitude/2)
    head_2_lon_t = np.cos(rad_dir-(np.pi/4))*(magnitude/2)
    
    tail = [lon+lon_t, lat+lat_t]
    head_1 = [lon+head_1_lon_t, lat+head_1_lat_t]
    head_2 = [lon+head_2_lon_t, lat+head_2_lat_t]
    origin = [lon, lat]
    return [tail, origin, head_1, origin, head_2]

#Define a function to return 
def arrow_timestamp_features(lon_lat, da, magnitude, t):
    print(da)
    features = []
    for ll in lon_lat:
        if np.isnan(da.loc[ll[1],ll[0]].data)==False:
            arrow = {
                'type': 'Feature',
                'geometry': {
                    'coordinates': arrow_coordinates(da.loc[ll[1],ll[0]].data, ll[1], ll[0], magnitude),
                    'type': 'LineString'
                },
                'properties': {'style':{'fillColor': '#ffffff', 
                            'color':'#000000', 
                            'fillOpacity': 0.8, 
                            'weight': 0.2}, 'interactive' : False}
            }
            l_coords = len(arrow['geometry']['coordinates'])
            arrow['properties']['times'] = [t]*l_coords
            features.append(arrow)
    else:
        pass
    return features
#==================================================================

