# -*- coding: utf-8 -*-
"""
Created on Sun May  2 17:21:54 2021

@author: lukei
"""
import GFS_map_tools as mt
import xarray as xr
import folium
from folium import plugins

def swell_data_geojson_features(sw_dir_da, sw_ht_da, feet, arrow_size, levels, color_pallette, central_lon):
    #process the height data.
    htsgwsfc = mt.convert_unix(sw_ht_da, 'time')
    if feet == True:
        htsgwsfc = mt.convert_units(htsgwsfc, 3.2808399)
    else:
        pass
    htsgwsfc = mt.convert_360_180_glo(htsgwsfc)
    
    #process the direction data:
    dirpwsfc = mt.convert_unix(sw_dir_da, 'time')
    dirpwsfc = mt.convert_360_180_glo(dirpwsfc)
    
    #get a list of lats and lons to format for geojson of arrows.
    lats = dirpwsfc.coords['lat'].values
    lons = dirpwsfc.coords['lon'].values
    times = dirpwsfc.coords['time'].values
    
    #convert lat lons to format for geojson
    lon_lat = mt.iteray(lats, lons)
    
    #generate the geojson for the map by combining arrows and contour polygons
    features = []
    for t in times:
        t = int(t)
        features.append(mt.geojson_from_netcdf(htsgwsfc, levels, color_pallette, central_lon, t))
        features.extend(mt.arrow_timestamp_features(lon_lat, dirpwsfc.sel(time = t), arrow_size, t))
    return features

#define style functions for any bounding boxes.
style_funct = lambda x: {'fillColor': '#042069', 
                            'color':'#042069', 
                            'fillOpacity': 0.0, 
                            'weight': 1.0}

highlight_funct= lambda x: {'fillColor': '#042069', 
                                'color':'#042069', 
                                'fillOpacity': 0.50, 
                                'weight': 2.0}


regions_list = ['glo25', 'glo16', 'gsouth', 'wcoast', 'atlocn', 'epacif', 'arctic']

gfs_variable_def = {"surface primary wave direction [deg]":{"name":"dirpwsfc"},
                    "surface significant height of combined wind waves and swell [m]":{"name":"htsgwsfc"},
                    "surface primary wave mean period [s]":{"name":"perpwsfc"},
                    "1 in sequence direction of swell waves [deg]":{"name":"swdir_1"},
                    "2 in sequence direction of swell waves [deg]":{"name":"swdir_2"},
                    "3 in sequence direction of swell waves [deg]":{"name":"swdir_3"},
                    "1 in sequence significant height of swell waves [m]":{"name":"swell_1"},
                    "2 in sequence significant height of swell waves [m]":{"name":"swell_2"},
                    "3 in sequence significant height of swell waves [m]":{"name":"swell_3"},
                    "1 in sequence mean period of swell waves [s]":{"name":"swper_1"},
                    "2 in sequence mean period of swell waves [s]":{"name":"swper_2"},
                    "3 in sequence mean period of swell waves [s]":{"name":"swper_3"},
                    "surface u-component of wind [m/s]":{"name":"ugrdsfc"},
                    "surface v-component of wind [m/s]":{"name":"vgrdsfc"},
                    "surface wind direction (from which blowing) [degtrue]":{"name":"wdirsfc"},
                    "surface wind speed [m/s]":{"name":"windsfc"},
                    "surface direction of wind waves [deg]":{"name":"wvdirsfc"},
                    "surface significant height of wind waves [m]":{"name":"wvhgtsfc"},
                    "surface mean period of wind waves [s]":{"name":"wvpersfc"}}


present_date = mt.present_runtime_calc()[0]
runtime = mt.present_runtime_calc()[1]

levels = [0,1,2,3,4,5,6,8,10,12,15,20,25,30,35,40,45]
color_pallette = 'Spectral_r'

#Export glo25:
region = regions_list[0]

gfs_url = mt.gfswave_region_url(present_date, runtime, region)
ds = xr.open_dataset(gfs_url)

sw_dir = ds.dirpwsfc[::4,::12,::12]
sw_ht = ds.htsgwsfc[::4, :, :]

lat_min = min(sw_dir.coords['lat'].values)
lat_max = max(sw_dir.coords['lat'].values)
lon_min = min(sw_dir.coords['lon'].values)
lon_max = max(sw_dir.coords['lon'].values)

print(lat_min, lat_max, lon_min, lon_max)

features = swell_data_geojson_features(sw_dir, sw_ht, feet=True, arrow_size=0.5, levels=levels, color_pallette=color_pallette, central_lon=0)

#intitate the map
print('Generating Map...')
wavemap = folium.Map(location=[32, -117], zoom_start=7, min_zoom = 2, worldCopyJump = True)
#create a legend
step = mt.step_legend(color_pallette, levels, 0, 45, 'Significant Height of Swell and Wind Waves (ft)')
#create a timestamped geojson object
time_geojson = plugins.TimestampedGeoJson({'type': 'FeatureCollection','features': features}, period='PT3H', transition_time = 750, time_slider_drag_update = True, duration = 'PT2H', auto_play=False, add_last_point = False)

#socal_bbox = folium.features.GeoJson(data = mt.geojson_box(-120.5, -116.5, 31.5, 34.0, "<p><a href='NOAA_GFS_wave_model_data_vis_glo25_1.html'>Southern California</a></p>"), zoom_on_click =False, highlight_function=highlight_funct, style_function = style_funct, popup = folium.features.GeoJsonPopup(fields = ['popup'], labels = False))

wavemap.add_child(step)
wavemap.add_child(time_geojson)
#wavemap.add_child(socal_bbox)



wavemap.save('NOAA_GFS_wave_model_data_vis_'+region+'.html')

#Export wcoast:
region = regions_list[3]

gfs_url = mt.gfswave_region_url(present_date, runtime, region)
ds = xr.open_dataset(gfs_url)

sw_dir = ds.dirpwsfc[:,::4,::4]
sw_ht = ds.htsgwsfc[:,:,:]

lat_min = min(sw_dir.coords['lat'].values)
lat_max = max(sw_dir.coords['lat'].values)
lon_min = min(sw_dir.coords['lon'].values)
lon_max = max(sw_dir.coords['lon'].values)

print(lat_min, lat_max, lon_min, lon_max)

features = swell_data_geojson_features(sw_dir, sw_ht, feet=True, arrow_size=0.16, levels=levels, color_pallette=color_pallette, central_lon=0)

#intitate the map
print('Generating Map...')
wavemap = folium.Map(location=[32, -117], zoom_start=7, min_zoom = 2, worldCopyJump = True)
#create a legend
step = mt.step_legend(color_pallette, levels, 0, 45, 'Significant Height of Swell and Wind Waves (ft)')
#create a timestamped geojson object
time_geojson = plugins.TimestampedGeoJson({'type': 'FeatureCollection','features': features}, period='PT3H', transition_time = 750, time_slider_drag_update = True, duration = 'PT2H', auto_play=False, add_last_point = False)

#socal_bbox = folium.features.GeoJson(data = mt.geojson_box(-120.5, -116.5, 31.5, 34.0, "<p><a href='NOAA_GFS_wave_model_data_vis_glo25_1.html'>Southern California</a></p>"), zoom_on_click =False, highlight_function=highlight_funct, style_function = style_funct, popup = folium.features.GeoJsonPopup(fields = ['popup'], labels = False))

wavemap.add_child(step)
wavemap.add_child(time_geojson)
#wavemap.add_child(socal_bbox)



wavemap.save('NOAA_GFS_wave_model_data_vis_'+region+'.html')



#Export atl:
region = regions_list[4]

gfs_url = mt.gfswave_region_url(present_date, runtime, region)
ds = xr.open_dataset(gfs_url)

sw_dir = ds.dirpwsfc[:,::8,::8]
sw_ht = ds.htsgwsfc[:, ::2, ::2]

lat_min = min(sw_dir.coords['lat'].values)
lat_max = max(sw_dir.coords['lat'].values)
lon_min = min(sw_dir.coords['lon'].values)
lon_max = max(sw_dir.coords['lon'].values)

print(lat_min, lat_max, lon_min, lon_max)

features = swell_data_geojson_features(sw_dir, sw_ht, feet=True, arrow_size=0.16, levels=levels, color_pallette=color_pallette, central_lon=0)

#intitate the map
print('Generating Map...')
wavemap = folium.Map(location=[32, -117], zoom_start=7, min_zoom = 2, worldCopyJump = True)
#create a legend
step = mt.step_legend(color_pallette, levels, 0, 45, 'Significant Height of Swell and Wind Waves (ft)')
#create a timestamped geojson object
time_geojson = plugins.TimestampedGeoJson({'type': 'FeatureCollection','features': features}, period='PT3H', transition_time = 750, time_slider_drag_update = True, duration = 'PT2H', auto_play=False, add_last_point = False)

#socal_bbox = folium.features.GeoJson(data = mt.geojson_box(-120.5, -116.5, 31.5, 34.0, "<p><a href='NOAA_GFS_wave_model_data_vis_glo25_1.html'>Southern California</a></p>"), zoom_on_click =False, highlight_function=highlight_funct, style_function = style_funct, popup = folium.features.GeoJsonPopup(fields = ['popup'], labels = False))

wavemap.add_child(step)
wavemap.add_child(time_geojson)
#wavemap.add_child(socal_bbox)



wavemap.save('NOAA_GFS_wave_model_data_vis_'+region+'.html')

#Export epac:
region = regions_list[5]

gfs_url = mt.gfswave_region_url(present_date, runtime, region)
ds = xr.open_dataset(gfs_url)

sw_dir = ds.dirpwsfc[:,::4,::4]
sw_ht = ds.htsgwsfc[:, :, :]

lat_min = min(sw_dir.coords['lat'].values)
lat_max = max(sw_dir.coords['lat'].values)
lon_min = min(sw_dir.coords['lon'].values)
lon_max = max(sw_dir.coords['lon'].values)

print(lat_min, lat_max, lon_min, lon_max)

features = swell_data_geojson_features(sw_dir, sw_ht, feet=True, arrow_size=0.16, levels=levels, color_pallette=color_pallette, central_lon=0)

#intitate the map
print('Generating Map...')
wavemap = folium.Map(location=[32, -117], zoom_start=7, min_zoom = 2, worldCopyJump = True)
#create a legend
step = mt.step_legend(color_pallette, levels, 0, 45, 'Significant Height of Swell and Wind Waves (ft)')
#create a timestamped geojson object
time_geojson = plugins.TimestampedGeoJson({'type': 'FeatureCollection','features': features}, period='PT3H', transition_time = 750, time_slider_drag_update = True, duration = 'PT2H', auto_play=False, add_last_point = False)

#socal_bbox = folium.features.GeoJson(data = mt.geojson_box(-120.5, -116.5, 31.5, 34.0, "<p><a href='NOAA_GFS_wave_model_data_vis_glo25_1.html'>Southern California</a></p>"), zoom_on_click =False, highlight_function=highlight_funct, style_function = style_funct, popup = folium.features.GeoJsonPopup(fields = ['popup'], labels = False))

wavemap.add_child(step)
wavemap.add_child(time_geojson)
#wavemap.add_child(socal_bbox)



wavemap.save('NOAA_GFS_wave_model_data_vis_'+region+'.html')

#Export artic:
region = regions_list[6]

gfs_url = mt.gfswave_region_url(present_date, runtime, region)
ds = xr.open_dataset(gfs_url)

sw_dir = ds.dirpwsfc[:,:,:]
sw_ht = ds.htsgwsfc[:, :, :]

lat_min = min(sw_dir.coords['lat'].values)
lat_max = max(sw_dir.coords['lat'].values)
lon_min = min(sw_dir.coords['lon'].values)
lon_max = max(sw_dir.coords['lon'].values)

print(lat_min, lat_max, lon_min, lon_max)

features = swell_data_geojson_features(sw_dir, sw_ht, feet=True, arrow_size=0.16, levels=levels, color_pallette=color_pallette, central_lon=0)

#intitate the map
print('Generating Map...')
wavemap = folium.Map(location=[32, -117], zoom_start=7, min_zoom = 2, worldCopyJump = True)
#create a legend
step = mt.step_legend(color_pallette, levels, 0, 45, 'Significant Height of Swell and Wind Waves (ft)')
#create a timestamped geojson object
time_geojson = plugins.TimestampedGeoJson({'type': 'FeatureCollection','features': features}, period='PT3H', transition_time = 750, time_slider_drag_update = True, duration = 'PT2H', auto_play=False, add_last_point = False)

#socal_bbox = folium.features.GeoJson(data = mt.geojson_box(-120.5, -116.5, 31.5, 34.0, "<p><a href='NOAA_GFS_wave_model_data_vis_glo25_1.html'>Southern California</a></p>"), zoom_on_click =False, highlight_function=highlight_funct, style_function = style_funct, popup = folium.features.GeoJsonPopup(fields = ['popup'], labels = False))

wavemap.add_child(step)
wavemap.add_child(time_geojson)
#wavemap.add_child(socal_bbox)



wavemap.save('NOAA_GFS_wave_model_data_vis_'+region+'.html')