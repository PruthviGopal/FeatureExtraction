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

	# inDSMRas = arcpy.Raster(inDSM) 
	# inDTMRas = arcpy.Raster(inDTM)

	desc = arcpy.Describe(inDSM)

	xmin = desc.extent.XMin
	ymin = desc.extent.YMin
	cellwidth = desc.meanCellWidth
	cellheight = desc.meanCellHeight
	nodata = desc.noDataValue
	sr = desc.spatialReference

	arcpy.AddMessage("Calculating height raster...")

	#fix DTM and DTM first
	dsmArr = arcpy.RasterToNumPyArray(inDSM)
	dtmArr = arcpy.RasterToNumPyArray(inDTM)
	

	numrows = len(dsmArr)
	numcols = len(dsmArr[0])

	heightArr = copy.deepcopy(dsmArr)

	for y in range(numrows):
		for x in range(numcols):
			if dsmArr[y][x] < 0 or dtmArr[y][x]  <0:
				heightArr[y][x] = 0
			else:
				heightArr[y][x] = dsmArr[y][x] - dtmArr[y][x]

	# heightArr = dsmArr-dtmArr
	# heightRas = arcpy.Raster(inDSM) - arcpy.Raster(inDTM)
	# heightArr = arcpy.RasterToNumPyArray(heightRas)
	heightArr[heightArr<0] = 0

	# arcpy.AddMessage(str(heightArr.max()))
	
	arcpy.AddMessage("Removing (obvious) vegetation...")

	stdArr = copy.deepcopy(heightArr)
	noVegArr = copy.deepcopy(heightArr)
	x=0
	y=0
	grid = [] 

	numrows = len(heightArr)
	numcols = len(heightArr[0])

	arcpy.AddMessage("Removing (obvious) vegetation...Processing Grids")

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

	stdArrFiltered = ndimage.filters.median_filter(stdArr,(5,5))
	stdevThresh = stdArrFiltered.max() * 0.125
	arcpy.AddMessage(str(stdevThresh))

	arcpy.AddMessage(str(stdArrFiltered))
	arcpy.AddMessage(stdevThresh)
	for y in range (0,numrows):
		for x in range(0,numcols):
			if stdArrFiltered[y][x] > stdevThresh:
				# arcpy.AddMessage("Hello. :)")
				noVegArr[y][x] = 0

	# tempRas = arcpy.NumPyArrayToRaster(noVegArr)
	# tempRas.save("C:/FeatureExtractionV1/noveg.tif")

	arcpy.AddMessage("Height Thresholding...")
	thresh = noVegArr > 2

	clean = ndimage.morphology.binary_erosion(thresh)
	# clean = ndimage.morphology.binary_dilation(clean)
	clean = ndimage.morphology.binary_fill_holes(clean)

	heightCleaned = clean * 1

	arcpy.AddMessage("Connected Component Labeling...")
	labeled, numLabels = ndimage.label(heightCleaned)
	outArr = copy.deepcopy(labeled)


	arcpy.AddMessage("Connected Component Cleaning...")
	
	histogram = [0]*(labeled.max()+1)
	droplist = []

	arcpy.AddMessage("Connected Component Cleaning...Calculating Histogram...")	
	for y in range(0,len(labeled)):
		for x in range(0, len(labeled[0])):
			histogram[labeled[y][x]] +=1

	arcpy.AddMessage("Connected Component Cleaning...Populating droplist...")	
	for i in range(0, len(histogram)):
		if histogram[i] < sizeThresh:	
			droplist.append(i)
	
	arcpy.AddMessage("Connected Component Cleaning...Dropping connected components...")			
	for i in range(0, len(droplist)):    
		outArr[outArr == droplist[i]] = 0

	arcpy.AddMessage("Saving output raster...")			
	outBinaryRas = arcpy.NumPyArrayToRaster(outArr, arcpy.Point(xmin, ymin), cellwidth, cellheight, nodata)
	# arcpy.Define_projection(heightBinaryRas, sr)
	outBinaryRas.save(outBinary)
	# arcpy.Define_projection(outBinary, sr)

	arcpy.AddMessage(outFc)
	arcpy.RasterToPolygon_conversion(outBinary, outFc, "SIMPLIFY", "VALUE")


except:
	arcpy.AddError("Fail")
	arcpy.AddMessage(arcpy.GetMessages())