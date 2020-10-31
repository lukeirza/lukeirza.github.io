# -*- coding: utf-8 -*-
"""
Created on Sat Sep 19 14:54:48 2020

@author: lukei
"""
import folium
from folium import plugins
import iris
from iris import plot as iplot
import matplotlib
import cartopy.crs as ccrs
import geojson
import datetime
import os
import branca
import matplotlib.pyplot as plt
import geojsoncontour
import numpy



#change the script's working directory to where it is stored.
def cd_script_loc():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    return os.getcwd()
    
#create a working directory to download all of the files into.
def dwnld_dir (dir_name, present_date, runtime):
    new_dir = os.getcwd()+'\\'+dir_name
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    os.chdir(new_dir)

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

#Make a  function to build each url for netcdf files.
def url_builder (base_url, region_file, present_date, runtime):
    url = base_url+present_date+'/'+region_file+present_date+'_'+runtime+'z'
    return url

#Make a function to name each netCDF file.
#def nc_file_name (name, variable, present_date, runtime):
#    savefile_name = name+'_'+variable+'_'+present_date+'_'+runtime+'z'+'.nc'
#    return savefile_name

#def tif_file_name (band, name, present_date, runtime):
#    savefile_name = band+'_'+name+'_'+present_date+'_'+runtime+'z'+'.tiff'
#    return savefile_name

#define a netcdf combiner:
#def nc_combiner (ds_1, ds_2):
#    ds_1 = ds_1.combine_first(ds_2)
#    return ds_1

#Define a conversion for time from NOAA conventions to Unix convention:
def jesus_2_unix(cube):
    #get all the time coordinates of the cube
    times = cube.coord('time').points
    #subtract days from 1-1-1 to 1-1-1970 and multiply by ms in day
    times_unix = (times - 719164)*86400000
    #change the type to int64
    return times_unix.astype('int64')

def jesus_2_unix_p(point):
    #subtract days from 1-1-1 to 1-1-1970 and multiply by ms in day
    times_unix = (point - 719164)*86400000
    #change the type to int64
    return int(times_unix)


#This edits the geojson so that there is a 'style' property with all of the right keys for folium. 
def style_function(feature):
    feature['properties']['style'] = {
        'color': feature['properties']['stroke'], 
        'weight': feature['properties']['stroke-width'], 
        'fillColor': feature['properties']['fill'],
        'fillOpacity': feature['properties']['fill-opacity'], 
        'opacity': feature['properties']['stroke-opacity'], 
        'smoothFactor':0
        }
    return

#location box
#mxlat=float(80)
#mnlat=float(10)
#mxlon=float(250)
#mnlon=float(190)

#define the date and runtime to pull:
present_date = present_runtime_calc()[0]
runtime = present_runtime_calc()[1]

#Changes the script working directory to where the file is stored.
prg_dir = cd_script_loc()

#Make a new directory for downloaded project files and change to it. 
dwnld_dir ('NOAA_mww3_netCDFs', present_date, runtime)

#Define the base directory url where all of the ncep files can be located. 
base_url = 'https://nomads.ncep.noaa.gov/dods/wave/mww3/'

#make a dictionary of all of the files and their names.
ds_r = {'glo':'multi_1.glo_30mext'
              , 'ep':'multi_1.ep_10m'
              , 'wc': 'multi_1.wc_4m'
              , 'ak': 'multi_1.ak_4m'
              , 'at': 'multi_1.at_4m'}

#variables that are of interest to surfers (combined swell height, swell direction, swell period, windspeed, wind direction)
ds_v = {'htsgwsfc':'meters', 'dirpwsfc':'degrees', 'perpwsfc':'seconds', 'windsfc':'m/s', 'wdirsfc':'degrees'}
v = list(ds_v.keys())
v_1 = v[0]


#Build a url to access data from any region file.
url = url_builder (base_url, ds_r['glo'], present_date, runtime)

#Load iris cubes of that file for the specified variable(s):
cubes = iris.load(url, v)

#iris loads the cubes into a list, we want the first item on the list
cube = cubes[0]
v_cube = cubes[1]

# Set up the folium plot
wavemap = folium.Map(location=[32, 360-117], zoom_start=7, min_zoom = 2)
wavemap.fit_bounds([[-90, 0], [90, 360]])

features = []
timestamps = []

#setup the plot axes. Mercator Projection is used.
ax = plt.axes(projection=ccrs.Mercator(central_longitude = 180.0))
ax.set_global()

# Setup colormap
#colors = ['#00dff8', '#0087f8', '#0025f8', '#00f892', '#83fc01', '#fcf601', '#fcb701', '#fc3a01', '#b801fc', '#fc01ed']
#vmin = 0
#vmax = 45
#levels = len(colors)
#cm = branca.colormap.LinearColormap(colors, vmin=vmin, vmax=vmax).to_step(levels)


# Add the colormap to the folium map
#cm.caption = 'htsgwsfc'
#wavemap.add_child(cm)

#set the levels of the contour
levels = [0,1,2,3,4,5,6,8,10,12,15,20,25,30,35,40,45]

#Get the colormap with as many colors as levels, then reverse it
colormap = matplotlib.cm.get_cmap("brewer_Spectral_11", len(levels))
colormap = colormap.reversed()

#Pull the rgb values from the colormap and convert to hexcodes.
cm_colors = []
for i in range(colormap.N):
    rgb = colormap(i)[:3] # will return rgba, we take only first 3 so we get rgb
    cm_colors.append(matplotlib.colors.rgb2hex(rgb))

#Pass the hexcodes to branca to make a legend. 
step = branca.colormap.StepColormap(colors=cm_colors
                        ,vmin=0
                        ,vmax=45
                        ,index=levels
                        ,caption='Significant Height of Swell and Wind Waves (ft)'
                        )

#Make a contour and convert it to geojson for each timestep
for t_cube in cube.slices_over('time'):
    
    #Pull data for only time step.
    t = t_cube.coord('time').points
    
    #Set the cube units per NOAA metadata. 
    t_cube.units = 'meters'
    
    #convert the units to feet
    t_cube.convert_units('feet')
    
    #Pull the timestamp from the plot
    timestamp = int(jesus_2_unix_p(t))
    
    #Plot the data at the timestamp
    contourf = iplot.contourf(t_cube
                              , axes=ax
                              , cmap=colormap
                              , levels=levels
                              , extend='max'
                              )
    
    #convert the contour plot to geojson that has a timestamp
    geo_json = geojsoncontour.contourf_to_geojson(
        contourf=contourf,
        min_angle_deg=1.0,
        stroke_width=0.5,
        fill_opacity=0.8)
    
    #Converts the geojson string into an indexable dict-like object
    geo_json = geojson.loads(geo_json)

    #For the timebar to work, there needs to be as many timestamps as coordinate objects. This makes sure there are enough timestamps for each feature
    for f in geo_json['features']:
        l_coords = len(f['geometry']['coordinates'])
        f['properties']['times'] = [timestamp]*l_coords
        style_function(f)

    #Append timestamped gejson to a list of geojson features
    features.append(geo_json)
    timestamps.append(timestamp)

#Plot the timestamped geojson
plugins.TimestampedGeoJson({
    'type': 'FeatureCollection',
    'features': features
    }, period='PT3H', transition_time = 750, time_slider_drag_update = True, duration = 'PT2H'
    ).add_to(wavemap)

#Add the legend to the map
wavemap.add_child(step)

#Save the map
wavemap.save('NOAA_Wavewatch_III_model_data_vis.html')

# And set the Axes limits in lat/lon coordinates:
#xlims = [cube.coord('longitude').points.min(), cube.coord('longitude').points.max() ]
#ylims = [cube.coord('latitude').points.min(), 84.0 ]



#ax.set_extent(xlims+ylims, crs=ccrs.Geodetic())

#colormap = matplotlib.cm.get_cmap("brewer_Spectral_11")
#colormap = colormap.reversed()

#contourf = iplot.contourf(t_cube, axes=ax,  cmap=colormap, )

# Convert matplotlib contourf to geojson
#geojson = geojsoncontour.contourf_to_geojson(
#    contourf=contourf,
#    min_angle_deg=1.0,
#    stroke_width=0.5,
#    fill_opacity=1.0,
#    geojson_properties={'times':times_unix[time_step]})
    
#print(geojson)



#Plot the contour plot on folium
#folium.GeoJson(geo_json).add_to(wavemap)

#Save the map
#wavemap.save('Mercator_projection_test_folium.html')




#swht = sw_cube_t.data
#lats = sw_cube_t.coord('projection_y_coordinate').points
#lons = sw_cube_t.coord('projection_x_coordinate').points


#in_ncname = ds_r['glo']+'_'+present_date+'_'+runtime+'.nc'
#out_ncname = 'wmerc'+'_'+in_ncname

#iris.save(cubes, ds_r['glo']+'_'+present_date+'_'+runtime+'.nc' )

#subprocess.run('gdalwarp -t_srs epsg:4326 -r BILINEAR -of NETCDF '+in_ncname+' temp.nc')
#subprocess.run('gdal_translate -of NETCDF -r BILINEAR -a_srs epsg:3857 -a_ullr -20037508 20037508 20037508 -20037508 -sds temp.nc '+out_ncname)
#subprocess.run('gdalwarp -t_srs epsg:4326 -r BILINEAR -of NETCDF '+in_ncname+' '+out_ncname)
#subprocess.run('gdal_translate -of NETCDF -r BILINEAR -a_srs epsg:4236 -a_ullr -20037508 20037508 20037508 -20037508 -sds temp.nc '+out_ncname)
#print('gdalwarp -t_srs epsg:4326 -r BILINEAR -wo SOURCE_EXTRA=1000 \--config CENTER_LONG 0-of NETCDF '+in_ncname+' '+out_ncname)

#print('gdal_translate -of NETCDF -r BILINEAR -a_srs epsg:3857 -a_ullr -20037508 20037508 20037508 -20037508 -sds '+in_ncname+' '+out_ncname)



#cubes = iris.load(out_ncname)

#sw_cube = cubes[0]
#print(sw_cube)

#sw_cube.units = 'meters'

#sw_cube.convert_units('feet')

#time_step = 0

#sw_cube_t = sw_cube[time_step]

#colormap = matplotlib.cm.get_cmap("brewer_Spectral_11")
#colormap = colormap.reversed()

#swht = sw_cube_t.data
#lats = sw_cube_t.coord('projection_y_coordinate').points
#lons = sw_cube_t.coord('projection_x_coordinate').points

#type(swht)
#type(lats)
#type(lons)

#print(swht)
#print(lats)
#print(lons)

#ax = plt.axes(projection=ccrs.epsg('3857'))

#iplot.contourf(sw_cube_t, cmap=colormap)

#matplotlib.pyplot.gca()

#ax.coastlines()

#plt.show()



#ax = plt.axes(projection=ccrs.epsg('3857'))

#iris.plot.contourf(sw_cube_t,cmap=colormap, ax=ax )

#sw_cube = cubes[0]




