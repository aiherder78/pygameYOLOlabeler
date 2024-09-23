import sys
import os
from os import walk #more simply get all filenames in a directory
import argparse
import pathlib
from pathlib import Path
from PIL import Image   #pip install pillow
import pygame   #pip install pygame
from pygame.locals import *  #this is for drawing the box lines over the image (when you click for the corners + following the mouse cursor between clicks)

#TODO:  Make the paths completely os agnostic - currently I'm coding for *nix paths
#https://stackoverflow.com/questions/6036129/platform-independent-file-paths


#1.  Get input directory from argument OR detect any images in current directory
#2.  Put all image file names into a list (only inserting the image file types as determined by the extensions list)
#3.  Load first image and enter loop:
#	0.  'q' to exit program, saving any boxes first for image.
#	    's' to save boxes for image and go to next image.
#	   scroll the mouse wheel to change the class labels you will apply to any label boxes.
#	a.  Wait for mouse button up (left click to mark top-left box corner, left click again to mark bottom-right box corner)
#		i.  'd' to erase nearest box (box with closest top-left corner by x, then y...or it cancels the last box corner
#		ii.  When a top-left box corner has been drawn, continue drawing box to the mouse cursor, red in color.
#		iii.  Once bottom-right box corner has been placed with second left mouse click, box lines turn blue and are set.
#		iv.  Top-left and bottom-right points are kept in variables (topLeftX, topLefty, bottomRightX, bottomRightY.
#		v.  All completed boxes are kept in list.
#
#	b.  Once s is pressed, all boxes (a.vi) are written to text file, one per line.
#			classNumber  BoxCentroidX   BoxCentroidY   BoxWidth  BoxHeight
#			To calculate midpoint - get midpoint on Y and midpoint on X, that's the centroid...
#			Note:  detections from Yolo are marked:  classNum  confidence (for example .42)  boxCenterX boxCenterY width height


def printHelp():
	print("This program lets you create annotation boxes on item types you want YOLO to recognize in images.")
	print("\n")
	print("Example command: 'pygameLabeler -i path/to/input/dirctory'")
	print("'python pygamelabeler.py' will pull images from the current directory - \nso if you're in the directory with images and the script is elsewhere, give the full path to the script while in the image folder.")
	print("\n")
	print("Once in the program: ")
	print("\t 'q' exits the program.")
	print("\t 's' saves the annotation boxes and goes to the next input image.")
	print("\t You should have a labels.txt file in your input images folder with object class names in it.")
	print("\t Scroll the mouse wheel to change between labels.")
	print("\t Whatever the current label is, starting at the first one by default, that will be the label on any created boxes.")
	print("\t Left click marks upper left corner of a box and then lower right corner...right click removes one of these marks.")
	print("\t 'd' removes the nearest box to the mouse cursor, as defined by nearest top left corner to mouse x then mouse y.")
	print("\t Once 's' is pressed, a file is written out with the box annotations in txt format as expected by YOLO for training.")
	print("\t This file will have the same name as the image you're currently on, just .txt format extension.  Therefore, even if")
	print("\t you have gone through hundreds of images and then press q, you will not lose previously saved image annotations.")


def getInputDirectory():
	inputDirectory = None
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', default=os.getcwd())
	parser.add_argument('-d', '--docs', help='-d docs   Prints full help')
	args = parser.parse_args()

	if args.docs:
		printHelp()
		exit()

	else:
		if args.input:
			#If an input directory is given, get the full path and make sure it exists on disk:
			#inputDirectory = os.path.dirname(os.path.abspath(parser.input))
			inputDirectory = Path(args.input)
			if not os.path.isdir(inputDirectory):
				print("Attempted to find input directory: " + inputDirectory)
				exit("Input directory does not exist or path not recognized.")
		else:
			#If not input directory is given, set the input directory to the current working directory.
			#https://www.geeksforgeeks.org/get-current-directory-python/
			input_directory = os.path.dirname(os.path.abspath(sys.argv[0])) 

	if inputDirectory is None:
		print("No idea how we got here, but we have no input directory")
		exit()
	
	print("Input directory is: " + str(inputDirectory))
	return inputDirectory


def getInputFilenames(mypath):
	f = []
	files = []
	image_extensions = [".jpg", ".jpeg", ".bmp" , ".png"]  # I'm just detecting jpeg, bitmap, and png
	# I would use imghdr, but I saw a big discussion about the python maintainers deprecating it

	#https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
	for (dirpath, dirnames, filenames) in walk(mypath):
		f.extend(filenames)
		break

	#https://stackoverflow.com/questions/541390/extracting-extension-from-filename-in-python/
	for filename in f:
		name, extension = os.path.splitext(filename)
		if extension in image_extensions:
			files.append(filename)

	return files
	

#You are expected to put your labels in a file named "labels.txt" in the input directory.  See the example labels.txt given for format.
def getLabels(inputDirectory, labelFileName):
	labels = None
	with open(os.path.join(inputDirectory, labelFileName)) as f:
		labels = f.read().splitlines()
	return labels
			

#The annotation file for a given image will have the same filename, except the prefix will be .txt  (so there will be a separate annotation file for each image that holds all the label box details)
def getAnnotationFileName(inputDirectory, imageFilename):
	inputDirectory = Path(inputDirectory)
	filename, extension = os.path.splitext(imageFilename)  #get the image extension off the image file name
	
	annotationFilename = filename + ".txt" #the image annotation file has the same first part of the name but the extension is ".txt" instead of the image extension.

	annotationFileFullpath = inputDirectory / annotationFilename
	
	return annotationFileFullpath
	

#See calculateNormalizedBoxNumbers for exact formatting instructions / how to calculate them.
def getBoxesFromAnnotationFile(inputDirectory, imageFilename):
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	
	boxes = []
	with open(annotationFileFullpath, "r") as annotationFile:
		for line in annotationFile:
			boxes.append(line.rstrip())   #append to the boxes list without the "\n" line breaks
	
	return boxes


#I'll run this when saving the annotation file or when deleting a box.  When just adding a single box, I'll run addAnnotationFileBox() which opens the file in append mode.
def setAnnotationFileBoxes(inputDirectory, imageFilename, boxes):
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	with open(annotationFileFullpath, "w") as annotationFile:
		for box in boxes:
			annotationFile.write(box + "\n")


def addAnnotationFileBox(inputDirectory, imageFilename, box):
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	with open(annotationFileFullpath, "a") as annotationFile:
		annotationFile.write(box + "\n")


def calculateNormalizedBoxNumbers(imageWidth, imageHeight, boxX1, boxX2, boxY1, boxY2, labelIndex):
	#make sure to first get the actual position of the boxX1, boxX2, boxY1, and boxY2 in the image, just in case the window is not at upper left of the screen
	boxWidth = boxX2 - boxX1
	boxHeight = boxY2 - boxY1
	boxCenterX = boxX1 + (boxWidth / 2)
	boxCenterY = boxY1 + (boxHeight / 2)  #assuming the Y values get higher as they go down the screen...it's been awhile since I referenced image Ys and pygame Ys.
	
	#Box coordinates must be normalized by the dimensions of the image (i.e. have values between 0 and 1)
	normalizedBoxCenterX = boxCenterX / imageWidth
	normalizedBoxCenterY = boxCenterY / imageHeight
	normalizedBoxWidth = boxWidth / imageWidth
	normalizedBoxHeight = boxHeight / imageHeight
	#https://blog.paperspace.com/train-yolov5-custom-data/
	#All of these values must be normalized, which we just calculated above
	#One row per box (labels an object in an image)
	#Class labels come from labels.txt and are zero indexed -> so if you had labels:  dog  cat, dog's labelIndex would be 0, cat's label index would be 1.
	#Each row's format is: labelIndex normalizedBoxCenterX normalizedBoxCenterY normalizedBoxWidth normalizedBoxHeight
	
	boxFileLine = labelIndex + " " + normalizedCenterX + " " + normalizedCenterY + " " + normalizedWidth + " " + normalizedHeight + "\n"
	
	return boxFileLine  #Here's another thing I'm not sure about yet - how easy will it be to parse the string in this format for image screen drawing?


#TODO May need some debugging - box may not be in this format, it's a string right now
def getImageBoxCoordinateFromNormalizedValues(box, imageWidth, imageHeight):
	normalizedBoxCenterX = box[1]
	normalizedBoxCenterY = box[2]
	normalizedBoxWidth = box[3]
	normalizedBoxHeight = box[4]
	
	boxCenterX = normalizedBoxCenterX * imageWidth
	boxCenterY = normalizedBoxCenterY * imageHeight
	boxWidth = normalizedBoxWidth * imageWidth
	boxHeight = normalizedBoxHeight * imageHeight
	
	boxX1 = boxCenterX - (boxWidth / 2)
	boxY1 = boxCenterX - (boxHeight / 2)
	boxX2 = boxCenterX + (boxWidth / 2)
	boxY2 = boxCenterY + (boxHeight / 2)
	
	return boxX1, boxY1, boxX2, boxY2


def drawBoxOnImage(image, x1, y1, x2, y2, label):
	# Draw the boxes and put the label on its top line in a font
	#https://stackoverflow.com/questions/10077644/how-to-display-text-with-font-and-color-using-pygame
	#https://www.geeksforgeeks.org/pygame-drawing-objects-and-shapes/


def drawBoxesOnImage(image, boxes, labels):
	imageWidth, imageHeight = image.size
	for box in boxes:
		labelIndex = box[0]
		label = labels[labelIndex]
		x1, y1, x2, y2 = getImageBoxCoordinateFromNormalizedValues(box, imageWidth, imageHeight)
		image = drawBoxOnImage(image, x1, y1, x2, y2, label)
	return image


#This is entirely so that box lines will follow the mouse cursor / be visible between your first left-click and second left-click when creating a box.
#Remember, right-click to cancel box creation (before left-clicking the second time)
def drawTempBoxOnImage(image, x1, y1, label):
	drawBoxesOnImage(image, boxes, labels)  #I always want the boxes that are already set to be drawn.
	
	#Now draw a single temp box based on where the mouse cursor is:
	#https://www.pygame.org/docs/ref/mouse.html#pygame.mouse.get_pos
	x2, y2 = pygame.mouse.get_pos() #get the mouse cursor position for the next step
	
	#I always want the x1 and y1 to be the upper left corner, so if order is switched, put them in the right order
	if x1 > x2:
		x1temp = x1
		x1 = x2
		x2 = x1temp
	if y1 < y2:
		y1temp = y1
		y1 = y2
		y2 = y1temp
	
	drawBoxOnImage(image, x1, y1, x2, y2, label)


#I'm going to test only progressing forward through boxes and images first, then I'll add box delete functionality
def removeBoxFromBoxes(label_index, x1, y1, x2, y2, imageWidth, imageHeight, imageFileName):
	#TODO


#https://stackoverflow.com/questions/6444548/how-do-i-get-the-picture-size-with-pil
#Could also do these with cv2:  https://python-code.dev/articles/110664770  #images would be numpy arrays in this case, could be important for optimizing (if needed later)
def getImage(inputDirectory, imageFilename):
	image = Image.open(os.path.join(inputDirectory, imageFilename))
	imageWidth, imageHeight = image.size
	return image, imageWidth, imageHeight


def drawLoop(filenamesList, inputDirectory, labels):
	pygame.init()
	#Clear the screen and paste the first image
        #https://gamedevacademy.org/pygame-background-image-tutorial-complete-guide/
	labelIndex = 0
	label = labels[labelIndex]
	running = True
	filenamesListOffset = 0
	imageFileName = filenamesList[filenamesListOffset]
	image, imageWidth, imageHeight = getImage(inputDirectory, imageFileName)
	boxes = getBoxesFromAnnotationFile(inputDirectory, imageFilename) #just in case there are already annotations for this image...
	
	#https://stackoverflow.com/questions/4135928/pygame-display-position
	game_dislay = pygame.display.set_mode((imageWidth, imageHeight))
	window.fill((0, 0, 0))
	while running and image is not None:
		#Just being paranoid here about possible pygame window repositions by the user
		size = pygame.display.Info() #x, y, width, height
		imageTopLeftX = size[0]
		imageTopLeftY = size[1]
		if size[2] not imageWidth:
			print("Strange - size[2] from pygame.display.Info() is not the same as the image.size[2] (imageWidth) gotten from getImage()!! - debugging needed.")
		imageWidth = size[2]
		if size[3] not imageHeight:
			print("Strange - size[3] from pygame.display.Info() is not the same as the image.size[3] (imageHeight) gotten from getImage()!! - debugging needed.")
		imageHeight = size[3]
		
		boxX1 = None #tempBoxUpperLeftX
		boxY1 = None #tempBoxUpperLeftY
		boxX2 = None #tempBoxLowerRightX
		boxY2 = None #tempBoxLowerRightY

		#First order of business is just to get the debugging / testing done for recording annotation boxes and displaying them properly over the image (and getting the images displayed)
		#Then start iterating over images and making sure that box data is properly reflected / kept / able to be retrieved later and works.
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

			#https://stackoverflow.com/questions/10990137/pygame-mouse-clicking-detection
			if event.type == pygame.MOUSEBUTTONDOWN:

				if event.button == 1:  # left click
					#A backup might be:  https://stackoverflow.com/questions/25848951/python-get-mouse-x-y-position-on-click
					if tempBoxTopLeftX == None and :
						boxX1 = pos[0] - imageTopLeftX  #tempBoxUpperLeftX   #TODO I'm not too sure about these lines yet...plenty of debugging ahead...
						boxY1 = pos[1] - imageTopLeftY #tempBoxUpperLeftY
					else:
						boxX2 = pos[0] - imageTopLeftX  #tempBoxLowerRightX
						boxY2 = pos[1] - imageTopLeftY  #tempBoxLowerRightY

						box = calculateNormalizedBoxNumbers(imageWidth, imageHeight, boxX1, boxX2, boxY1, boxY2, labelIndex)
						addAnnotationFileBox(inputDirectory, imageFilename, box)
						boxes.append(box)

				#if event.button == 2:  # middle-click    #TODO:  Add this later and test/debug
				#	removeNearestBox()

				if event.button == 3:  # right-click --> clear the set box positions
					x1, y1, x2, y2 = None

				if event.button == 4:  # scroll-up
					#Change label previous (if not already #1)
					if label_index not 0:
						label_index -= 1
						label = labels(label_index)

				if event.button == 5:  # scroll-down
					#Change label next (if not at end)
					if labels.len > label_index + 1:
						label_index += 1
						label = labels(label_index)

			'''
			#handle keyboard button presses:
			if event.type == pygame

				if x1 not None:
					pos = pygame.mouse.get_pos()
					drawBoxesOnImage()
					drawTempBoxOnImage(x1, y1, pos[0], pos[1], label)
			'''

		game.display.blit(image, (0, 0))
		pygame.display.update()

	pygame.quit()

def main():
	inputDirectory = Path(getInputDirectory())

	filenamesList = getInputFilenames(inputDirectory)

	labels = getLabels(inputDirectory, "labels.txt")

	if filenamesList.len > 0:
		drawLoop(filenamesList, inputDirectory, labels)

	else:
		print("Sorry, the input directory is empty of recognized image files.")

if __name__ == "__main__":
	main()
