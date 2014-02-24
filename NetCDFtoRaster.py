#=========================================================================================================
# Author, Date: John Broussard
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
# 	NetCDFtoRaster.py -i infile -o outdir -t timesliceAsIndex
#	example: NetCDFtoRaster.py -i cruncep_uwind_1901.nc -o uwind1901_rasters -t 230
#=========================================================================================================

# Import the modules we'll be using and set a shortcut
import arcpy, netCDF4, argparse, os

# Set up argument parsing: 1 input and 1 output
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--infile", dest="infile", action="store", help="File input to script")
parser.add_argument("-o", "--outdir", dest="outdir", action="store", help="File output from script")
parser.add_argument("-t", "--timeslice", dest="timeslice", default='0', action="store",
                    help="This is the timeslice (as index) to use if there are multiple time steps in the netcdf file. If specified timeslice is not within those allowed by the input file's time variable, then the first index (0) is used by default.")


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
    
    # If timeslice used, check that it is within the range
    if ('time' in rootgroup.variables) and (int(args.timeslice) in range(rootgroup.variables['time'].shape[0])):
        timeslice = args.timeslice
    else:
        timeslice = "0"
    
    # Get lat (and lon) resolution
    resolution = rootgroup.variables['lat'][0] - rootgroup.variables['lat'][1]

    
    # Get the variables contained in the infile that have lat and lon as dimensions
    # (These are the mappable variables) and create rasters for each.
    # Right now, only maps one slice of data, even if there are more time slices.
    variablesToMap = []
    for var in rootgroup.variables:
        if 'lat' in rootgroup.variables[var].dimensions and 'lon' in rootgroup.variables[var].dimensions:
            if 'time' in rootgroup.variables[var].dimensions:
                arcpy.MakeNetCDFTableView_md(infile, var, var, "lat;lon","time " + timeslice, "BY_INDEX")
                arcpy.MakeXYEventLayer_management(var,"lon","lat",var + "_pts")
                arcpy.FeatureToRaster_conversion(var + "_pts", var, var + "_" + timeslice, resolution)
            else:
                arcpy.MakeNetCDFTableView_md(infile, var, var, "lat;lon","","BY_INDEX")
                arcpy.MakeXYEventLayer_management(var,"lon","lat",var + "_pts")
                arcpy.FeatureToRaster_conversion(var + "_pts", var, var, resolution)

    rootgroup.close()

except Exception as e:
    print e.message
    arcpy.AddError(e.message)
