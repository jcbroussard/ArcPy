#======================================================================
# Author, Date: John Broussard, (Edited: 01/15/2014)
# Purpose: Convert data within a NetCDF database to a raster, then
#           post to ArcGIS Online account.
#
# Requirements:
#   1) Arcpy - Comes with ArcGIS
#   2) netCDF4 - https://code.google.com/p/netcdf4-python/
#
# Actions:
#   1) Open the netcdf file in python, grab the plotable variable names
#   2) Create rasters of all variables in that list
#   3) Save each raster to specified folder
# 
# Usage:
# 	NetCDFtoRaster.py 
#======================================================================

# Import the modules we'll be using and set a shortcut
import arcpy, netCDF4, argparse, os
import arcpy.mapping as map

# Set up argument parsing: 1 input and 1 output
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--infile", dest="infile", action="store", help="file input to script")
parser.add_argument("-o", "--outdir", dest="outdir", action="store", help="file putput from script")


try:
    args = parser.parse_args()

    infile = ""
    outdir = ""
    if args.infile == None:
        print "ERROR: no input file was provided"
        exit(1)
    elif args.outdir == None:
        print "ERROR: no output directory was provided"
        exit(1)
    else:
        infile = args.infile
        outdir = args.outdir

    # Set ArcPy workspace and allow files to be overwritten
    arcpy.env.workspace = outdir
    arcpy.env.overwriteOutput = True

    # Open the model (netCDF) file
    rootgroup = netCDF4.Dataset(infile, 'r')

    # Get lat (and lon) resolution
    resolution = rootgroup.variables['lat'][0] - rootgroup.variables['lat'][1]

    # Get the variables contained in the infile that have lat and lon as dimensions
    # (These are the mappable variables) and create rasters for each.
    # Right now, only maps one slice of data, even if there are more time slices.
    variablesToMap = []
    for var in rootgroup.variables:
        if 'lat' in rootgroup.variables[var].dimensions and 'lon' in rootgroup.variables[var].dimensions:
            ##variablesToMap.append(var)
            arcpy.MakeNetCDFTableView_md(infile, var, var, "lat;lon","","BY_INDEX")
            arcpy.MakeXYEventLayer_management(var,"lon","lat",var + "_pts")
            arcpy.FeatureToRaster_conversion(var + "_pts", var, var, resolution)

    rootgroup.close()

except Exception as e:
    print e.message
    arcpy.AddError(e.message)
