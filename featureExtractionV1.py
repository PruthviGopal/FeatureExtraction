#
#	Filename: featureExtractionV1.py
#	Description: An ArcGIS script for the automated detection of man-made features in LiDAR datasets
#	Written by: Phil-LiDAR 1 UPLB	

import arcpy
import numpy
from scipy import ndimage
import copy

try:

	inDSM = arcpy.GetParameterAsText(0)
	inDTM = arcpy.GetParameterAsText(1)
	sizeThresh = float(arcpy.GetParameterAsText(2))
	outBinary = arcpy.GetParameterAsText(3)
	outFc = arcpy.GetParameterAsText(4)

	arcpy.AddMessage("Retrieving inputs...")

#	Retrieve the needed data for raster output
#	(starting x,y coordinates, cell size, no data value and spatial reference)

	desc = arcpy.Describe(inDSM)
	xmin = desc.extent.XMin
	ymin = desc.extent.YMin
	cellwidth = desc.meanCellWidth
	cellheight = desc.meanCellHeight
	nodata = desc.noDataValue
	sr = desc.spatialReference

#	Calculate the difference raster

	arcpy.AddMessage("Calculating height raster...")

	# Convert rasters to numpy arrays
	dsmArr = arcpy.RasterToNumPyArray(inDSM)
	dtmArr = arcpy.RasterToNumPyArray(inDTM)
	
	# Prepare for calculations
	numrows = len(dsmArr)
	numcols = len(dsmArr[0])
	heightArr = copy.deepcopy(dsmArr)

	# Get the difference of every pixel from the DSM and DTM
	# Make sure there are no negative values in the resultant numpy array
	for y in range(numrows):
		for x in range(numcols):
			if dsmArr[y][x] < 0 or dtmArr[y][x]  <0:
				heightArr[y][x] = 0
			else:
				heightArr[y][x] = dsmArr[y][x] - dtmArr[y][x]

	heightArr[heightArr<0] = 0

#	Remove presumed vegetation pixels	
	arcpy.AddMessage("Removing (obvious) vegetation...")

	stdArr = copy.deepcopy(heightArr)
	noVegArr = copy.deepcopy(heightArr)
	x=0
	y=0
	grid = [] 

	numrows = len(heightArr)
	numcols = len(heightArr[0])

	arcpy.AddMessage("Removing (obvious) vegetation...Processing Grids")

	# Per 2x2 grid, calculate for the standard deviation
	while y< numrows:
		while x<numcols:
			if y<numrows and x < numcols and heightArr[y][x] > 0: 
				grid.append(heightArr[y][x])
			if y<numrows and x+1 < numcols and heightArr[y][x+1] > 0:
				grid.append(heightArr[y][x+1])
			if y+1<numrows and x < numcols and heightArr[y+1][x] > 0:
				grid.append(heightArr[y+1][x])
			if y+1<numrows and x+1 < numcols and heightArr[y+1][x+1] > 0:
				grid.append(heightArr[y+1][x+1])	
			
			if numpy.isnan(numpy.std(grid)):	
				stdev = 0
			else:
				stdev = numpy.std(grid)

			if y<numrows and x < numcols:
				stdArr[y][x] = stdev
			if y<numrows and x+1 < numcols:
				stdArr[y][x+1] = stdev
			if y+1<numrows and x < numcols:
				stdArr[y+1][x] = stdev
			if y+1<numrows and x + 1 < numcols:
				stdArr[y+1][x+1] = stdev		
			
			grid = []
			x+=2
		x=0	
		y+=2

	arcpy.AddMessage("Removing (obvious) vegetation...Filtering...")

	# Apply a median filter blur the standard deviation array
	stdArrFiltered = ndimage.filters.median_filter(stdArr,(5,5))
	stdevThresh = stdArrFiltered.max() * 0.125
	
	# Remove pixels from the height raster if they belong to a grid cell with a high stdev	
	for y in range (0,numrows):
		for x in range(0,numcols):
			if stdArrFiltered[y][x] > stdevThresh:
				noVegArr[y][x] = 0

#	Perform binarization
	arcpy.AddMessage("Height Thresholding...")
	thresh = noVegArr > 2
	
	# Perform morphological operations for binary image cleaning
	clean = ndimage.morphology.binary_erosion(thresh)
	clean = ndimage.morphology.binary_fill_holes(clean)

	heightCleaned = clean * 1

#	Label connected components using an integer id
	arcpy.AddMessage("Connected Component Labeling...")
	labeled, numLabels = ndimage.label(heightCleaned)
	outArr = copy.deepcopy(labeled)

#	Remove connected components that are smaller than the user-defined threshold
	arcpy.AddMessage("Connected Component Cleaning...")

	# Create a histogram with every label id as bins
	histogram = [0]*(labeled.max()+1)
	droplist = []

	arcpy.AddMessage("Connected Component Cleaning...Calculating Histogram...")	
	
	# Increment bins
	for y in range(0,len(labeled)):
		for x in range(0, len(labeled[0])):
			histogram[labeled[y][x]] +=1

	# If the number of pixels is less than the threshold, add the label id to the droplist
	arcpy.AddMessage("Connected Component Cleaning...Populating droplist...")	
	for i in range(0, len(histogram)):
		if histogram[i] < sizeThresh:	
			droplist.append(i)
	
	# Remove connected components with labels inside the droplist 
	arcpy.AddMessage("Connected Component Cleaning...Dropping connected components...")			
	for i in range(0, len(droplist)):    
		outArr[outArr == droplist[i]] = 0

	# Save the binary image	
	arcpy.AddMessage("Saving output raster...")			
	outBinaryRas = arcpy.NumPyArrayToRaster(outArr, arcpy.Point(xmin, ymin), cellwidth, cellheight, nodata)
	outBinaryRas.save(outBinary)

	# Create a shapefile as well
	# For the next version, remove the polygon for the label id 0
	arcpy.AddMessage(outFc)
	arcpy.RasterToPolygon_conversion(outBinary, outFc, "SIMPLIFY", "VALUE")


except:
	arcpy.AddError("Fail")
	arcpy.AddMessage(arcpy.GetMessages())