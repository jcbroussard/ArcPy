#======================================================================
# Author, Date: John Broussard, (Started: 09/10/2013)
# Purpose: 1) This script will take data from a csv (or excel worksheet)
#   and will add the fields in that file to a given shapefile, joining 
#   on the common country field.
#   2) After this, a thematic map will be created for each in a subset
#       of fields.
#   3) Then the maps will be exported to PDFs.
#======================================================================

import os
import arcpy
from arcpy import env
env.overwriteOutput = True

#======================================================================
# Step 0): Init
#======================================================================

# Set initial workspace details
workingDir = arcpy.GetParameterAsText(0)
if workingDir == '#' or not workingDir:
    workingDir = r'C:\Users\jcbrou\Documents\ArcGIS\AutoMap\Coursera'

# Specifiy background mxd and conditions
background = arcpy.GetParameterAsText(1)
if background == '#' or not background:
    background = workingDir + r'\worldBackground.mxd'
workingMxd = arcpy.mapping.MapDocument(background)
workingMxd.relativePaths = True

# Input excel workbook and relevant sheets
excelWorkbook = arcpy.GetParameterAsText(2)
if excelWorkbook == '#' or not excelWorkbook:
    excelWorkbook = workingDir + r'\MapData.xlsx'

mapDataTable = arcpy.GetParameterAsText(3)
if mapDataTable == '#' or not mapDataTable:
    mapDataTable = workingDir + 'ForMaps$'

fieldTable = arcpy.GetParameterAsText(4)
if fieldTable == '#' or not fieldTable:
    fieldTable = workingDir + 'FieldTable$'

# Set name of and geodatabaseshapefile file
workingGdb = arcpy.GetParameterAsText(5)
if workingGdb == '#' or not workingGdb:
    workingGdb = workingDir + r'\data.gdb'

givenShape = arcpy.GetParameterAsText(6)
if givenShape == '#' or not givenShape:
    givenShape = 'worldCountries.shp'
    
symbology = arcpy.GetParameterAsText(7)
if symbology == '#' or not symbology:
    symbology = 'symbology.lyr'

# Specify the tables and features to be created and saved in the GDB
readTable = 'classDataTable'
titleTable = 'titleTextTable'
mapData = 'mapData'

##readTable = arcpy.GetParameterAsText(8)
##if readTable == '#' or not readTable:
##    readTable = 'classDataTable'
##
##titleTable = arcpy.GetParameterAsText(9)
##if titleTable == '#' or not titleTable:
##    titleTable = 'titleTextTable'
##
##mapData = arcpy.GetParameterAsText(10)
##if mapData == '#' or not mapData:
##    mapData = 'courseraData'


#======================================================================
# Step 1): Open the data, and join to the given shapefile
#======================================================================

try:
    # To get at the excel worksheet, we need to set the workbook in which
    # is set as an ArcPy workspace
    env.workspace = excelWorkbook

    # Convert the excel data worksheet to a table in the gdb
    arcpy.TableToTable_conversion(mapDataTable, workingGdb, readTable)

    # Convert the title text into a table in the gdb
    arcpy.TableToTable_conversion(fieldTable, workingGdb, titleTable)

    # Set workspace back to workingDir
    env.workspace = workingDir

    # Join the table to the template Country shapefile
    givenLayerName = os.path.splitext(givenShape)[0]
    arcpy.MakeFeatureLayer_management(givenShape, givenLayerName)
    arcpy.AddJoin_management(givenLayerName, "CntryCode", workingGdb + "\\" + readTable, "CntryCode")

    # Copy the worldCountries shapefile into the GDB and rename. This will create a new shapefile
    # with all of the desired data included
    arcpy.CopyFeatures_management(givenLayerName, workingGdb + "\\" + mapData)

    # Remove Join
    arcpy.RemoveJoin_management(givenLayerName)
except Exception as e:
    print e.message
    arcpy.AddError(e.message)

#======================================================================
# Step 2): Now make publication-worthy maps using the pre-chosen splits
#           and colors.
#======================================================================

# Set new workspace to be the GDB
env.workspace = workingGdb

# Before diving into the map stuff, let's grab the title text for each map and place it in a dict
# Here the classes are specified by the field "FieldShort" and the title text by the fields "TitleOne" and
# "TitleTwo"
titleDict = {}
fieldList = []
fieldString = "FieldShort; TitleOne; TitleTwo"
rows = arcpy.SearchCursor(titleTable, fields = fieldString)
for row in rows:
	titleDict[row.getValue("FieldShort")] = (row.getValue("TitleOne"),row.getValue("TitleTwo"))
	fieldList.append(row.getValue("FieldShort"))

print fieldList

# Create a layer containing the new shapefile 'givenShape'
courseraLyr = arcpy.mapping.Layer(mapData)
symbolLyr = arcpy.mapping.Layer(symbology)

# Turn on the legend
legend = arcpy.mapping.ListLayoutElements(workingMxd, "LEGEND_ELEMENT")[0]
legend.autoAdd = False

# Add new layer to the mxd
df = arcpy.mapping.ListDataFrames(workingMxd, "Layers")[0]
arcpy.mapping.AddLayer(df, symbolLyr, "TOP")
legend.autoAdd = True
arcpy.mapping.AddLayer(df, courseraLyr, "TOP")

# Get list of layers in the map
# layers[0] = 'mapData' and layers[1] = 'symbology'
layers = arcpy.mapping.ListLayers(workingMxd, "", df)
arcpy.mapping.UpdateLayer(df, layers[0], layers[1], True)

# Get list of fields with the suffix "Pct" (not case-sensitive)
dataFieldList = arcpy.ListFields(layers[0])

# Loop through all of the desired fields, apply the symbology, then save the mxd
for field in fieldList:

    # Set symbology for current field
    for layer in layers:
        if layer.name == "mapData":
            # Set the symbology field to one of the listed fields
            for dataField in dataFieldList:
                if dataField.aliasName == field:
                    layer.symbology.valueField = dataField.name #field.name

            # Alter map title to reflect current map
            tableText = arcpy.mapping.ListLayoutElements(workingMxd, "TEXT_ELEMENT")[1]
##            textElements = arcpy.mapping.ListLayoutElements(workingMxd, "TEXT_ELEMENT")
##            for element in textElements:
##                if element.text == u'Text':
##                    tableText = element
            
            # Grab the title text from the dictionary we that holds the titles for each course
            title = titleDict[field][0] #titleDict[field.name[15:]][0]
            if titleDict[field][1] == None: #titleDict[field.name[15:]][1]==None:
                subtitle = ""
            else:
                subtitle = titleDict[field][1] #titleDict[field.name[15:]][1]
            tableText.text = title + "\n\r" + subtitle
    
    # Save the mxd and export a PDF
    workingMxd.saveACopy(workingDir + "\\" + field + '.mxd') ##workingMxd.saveACopy(workingDir + "\\" + field.name + '.mxd')
    arcpy.mapping.ExportToPDF(workingMxd, workingDir + "\\" + field + '.pdf') ##arcpy.mapping.ExportToPDF(workingMxd, workingDir + "\\" + field.name + '.pdf')

# Release stuff from memory
del workingMxd, courseraLyr, symbolLyr, rows
arcpy.Delete_management(givenLayerName, "Layer")
