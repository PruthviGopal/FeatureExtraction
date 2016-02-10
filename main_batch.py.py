import Masking as ma
import BoundaryRegularizationV2 as br
from skimage import io
import time
import pickle

# Put this in a loop for later
def main():

	# listfiles = ["pt000002"]
	# listfiles = ["pt000015","pt000024","pt000113","pt000115","pt000120","pt000121","pt000127","pt000128"]
	listfiles = ["pt000002","pt000012","pt000015","pt000024","pt000113","pt000115","pt000120","pt000121","pt000127","pt000128"]
	t_start = time.time()
	for f in listfiles:
		print "Processing ",f,"..."
		# Load inputs

		t0 = time.time()
		print "Loading inputs..."

		ndsm = io.imread('E:\FeatureExtractionV4\pipelinev6/inputs/ndsms/'+f+'.tif',-1)
		slope = io.imread('E:\FeatureExtractionV4\pipelinev6/inputs/slopes/'+f+'.tif',-1)
		classified = io.imread('E:\FeatureExtractionV4\pipelinev6/inputs/classified_rasters/'+f+'.tif',-1)
		slopeslope = io.imread('E:\FeatureExtractionV4\pipelinev6\inputs/slopeslopes/'+f+'.tif',-1)

		t1 = time.time()
		print "Finished in",str(round(t1-t0,2))+"s"

		# Initial Mask Generation

		print "Generating Initial Mask..."
		veggieMask,initialMask = ma.generateInitialMask(ndsm,classified,slope,ndsmThreshold=3,slopeThreshold=60)
		# io.imsave("E:/FeatureExtractionV4/pipelinev4/"+f+"_veggieMask.tif",veggieMask)
		io.imsave("E:/FeatureExtractionV4/pipelinev6/outputs/initial_masks/"+f+"_initialMask.tif",initialMask)

		t2 = time.time()
		print "Finished in",str(round(t2-t1,2))+"s"

		# Generate markers for Watershed segmentation

		print "Generating markers for Watershed segmentation..."

		initialMarkers = ma.generateInitialMarkers(slopeslope,veggieMask)
		io.imsave("E:/FeatureExtractionV4/pipelinev6/outputs/initial_markers/"+f+"_initialMarkers.tif",initialMarkers)

		t3 = time.time()
		print "Finished in",str(round(t3-t2,2))+"s."

		# Perform watershed segmentation
		print "Performing Watershed segmentation..."

		labeledMask = ma.watershed2(ndsm,initialMask,initialMarkers,veggieMask)
		io.imsave("E:/FeatureExtractionV4/pipelinev6/outputs/watershed/"+f+"_watershed.tif",labeledMask)

		t4 = time.time()
		print "Finished in",str(round(t4-t3,2))+"s."

		# Perform basic region merging

		print "Performing basic region merging..."

		mergedMask = ma.mergeRegionsBasicV2(labeledMask,mergeThreshold=0.10,iterations=10)
		io.imsave("E:/FeatureExtractionV4/pipelinev6/outputs/merged/"+f+"_merged_10iter2.tif",mergedMask)


		t5 = time.time()
		print "Finished in",str(round(t5-t4,2))+"s."

		print "Performing basic boundary regularization..."
		
		pieces = br.performBoundaryRegularizationV2(mergedMask)
	
		t6 = time.time()
		print "Finished in",str(round(t6-t5,2))+"s."

		print "Creating final mask and saving output raster..."
		finalMask = ma.buildFinalMask(pieces,mergedMask)
		io.imsave("E:/FeatureExtractionV4/pipelinev6/outputs/final/"+f+".tif",finalMask)

		t7 = time.time()
		print "Finished in",str(round(t7-t6 ,2))+"s."
	
	t_end = time.time()

	print "Finished everything in",str(round(t_snd-t_start,2))+"s." 

if __name__ == '__main__':

	main()


# print "Saving output image file..."
# io.imsave("E:/FeatureExtractionV4/pipelinev4/"+f+"_merged.tif",mergedMask)

# t6 = time.time()
# print "Finished in",str(round(t5-t4,2))+"s."