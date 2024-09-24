import sys
import os
from os import walk #more simply get all filenames in a directory
import argparse
import pathlib
from pathlib import Path
from PIL import Image   #pip install pillow
import pygame   #pip install pygame
from pygame.locals import *  #this is for drawing the box lines over the image (when you click for the corners + following the mouse cursor between clicks)
from copy import copy
import math  #for finding the distance between two points when testing distance from cursor to boxes you might want to delete
from operator import itemgetter  #for sorting a list, lets you do sorts of lists of list by multiple indexes

#TODO:  Make the paths completely os agnostic - currently I'm coding for *nix paths
#https://stackoverflow.com/questions/6036129/platform-independent-file-paths

#Idea:  I could make this intermittently copy already annotated image files and their annotations to a separate directory to be automatically
#processed - to train a YOLO model, then have that model also running here (and updated as it finishes training), putting boxes of a blue color around things it thinks it recognizes
#then you could position the mouse cursor over those and press a key to have that marked as well.
#This would be a sort of progressive training - would help annotators to see progress and see how the model was learning in real time.

#Idea2:  It would be nice to have a key you could press that would throw keybind help up on the screen using pygame fonts.
#Then you could press escape to exit that help and go back to doing annotations.
#'h' would be good.


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


#Just give me values I can work with on screen:
def getBoxValuesFromStrings(box, imageWidth, imageHeight, labels):
	#print(box)
	labelIndexStr, normalizedBoxCentroidXStr, normalizedBoxCentroidYStr, normalizedBoxWidthStr, normalizedBoxHeightStr = box.split(' ')
	label = labels[int(labelIndexStr)]
	normalizedBoxCentroidX = float(normalizedBoxCentroidXStr)
	normalizedBoxCentroidY = float(normalizedBoxCentroidYStr)
	normalizedBoxWidth = float(normalizedBoxWidthStr)
	normalizedBoxHeight = float(normalizedBoxHeightStr)
	
	box = [label, normalizedBoxCentroidX, normalizedBoxCentroidY, normalizedBoxWidth, normalizedBoxHeight]

	return box


def getImageBoxCoordinateFromNormalizedValues(box, imageWidth, imageHeight, labels):
	#print("entering getImageBoxCoordinateFromNormalizedValues()")
	box = getBoxValuesFromStrings(box, imageWidth, imageHeight, labels)
	
	label = box[0]
	
	normalizedBoxCenterX = float(box[1])
	normalizedBoxCenterY = float(box[2])
	normalizedBoxWidth = float(box[3])
	normalizedBoxHeight = float(box[4])
	
	boxCenterX = normalizedBoxCenterX * imageWidth
	boxCenterY = normalizedBoxCenterY * imageHeight
	boxWidth = normalizedBoxWidth * imageWidth
	boxHeight = normalizedBoxHeight * imageHeight
	
	boxX1 = boxCenterX - (boxWidth / 2)
	boxY1 = boxCenterY - (boxHeight / 2)
	boxX2 = boxCenterX + (boxWidth / 2)  
	boxY2 = boxCenterY + (boxHeight / 2)
	
	boxDataForDrawing = [label, boxX1, boxY1, boxX2, boxY2]
	
	return boxDataForDrawing


#The next two functions I'll only use for convenience in removeBox().
#Once I have the box I want to remove, I'll get all the raw boxes, convert that single box to normalized / raw, get it's line
#then loop through and match the line I want gone.  Then I'll take that out of the list and send the list to the setRawBoxesToAnnotationFile().
def getRawBoxesFromAnnotationFile(inputDirectory, imageFilename, imageWidth, imageHeight):
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	rawBoxes = []
	try:
		with open(annotationFileFullpath, "r") as annotationFile:
			for line in annotationFile:
				rawBoxes.append(line.rstrip())
				
	except OSError as e:
		print("Annotation file does not exist yet.  Normally it'll be created while you left-click adding label boxes." + str(annotationFileFullpath))
	
	return rawBoxes


#See calculateNormalizedBoxNumbers for exact formatting instructions / how to calculate them.
def getBoxesFromAnnotationFile(inputDirectory, imageFilename, imageWidth, imageHeight, labels):
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	
	rawBoxes = []
	boxes = []
	rawBoxes = getRawBoxesFromAnnotationFile(inputDirectory, imageFilename, imageWidth, imageHeight)
	for box in rawBoxes:
		boxForDrawing = getImageBoxCoordinateFromNormalizedValues(box, imageWidth, imageHeight, labels)
		boxes.append(boxForDrawing)
	
	return boxes


#This converts from a box in list format to a string so it can be written to an image annotation file.
def getBoxWriteLine(box):
	return str(box[0]) + " " + str(box[1]) + " " + str(box[2]) + " " + str(box[3]) + " " + str(box[4]) + "\n"
	
	
def setRawBoxesToAnnotationFile(inputDirectory, imageFilename, imageWidth, imageHeight, boxLines):
	#print("in setRawBoxesToAnnotationFile()")
	print("In setRawBoxesToAnnotationFile - new boxes:")
	for line in boxLines:
		print(line)
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	
	with open(annotationFileFullpath, "w") as annotationFile:
		for line in boxLines:
			annotationFile.write(line)


#In the annotation files, all the boxes (one per line) are stored in normalized format in a space delimited string (with a line break '\n' at the end).
#In order to display the boxes over the image, I need their X1, Y1, X2, and Y2 values in image coords.
#I also need the values as separate elements in a list in order to be easily referenced.
def calculateNormalizedBoxNumbers(label, boxX1, boxY1, boxX2, boxY2, imageWidth, imageHeight, labels):

	labelIndex = labels.index(label)

	boxWidth = boxX2 - boxX1
	boxHeight = boxY2 - boxY1
	boxCenterX = boxX1 + (boxWidth / 2)
	boxCenterY = boxY1 + (boxHeight / 2)
	
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
	
	box = [labelIndex, normalizedBoxCenterX, normalizedBoxCenterY, normalizedBoxWidth, normalizedBoxHeight]
	
	return box
	

#I'll run this when saving the annotation file or when deleting a box.  When just adding a single box, I'll run addAnnotationFileBox() which opens the file in append mode.
def setAnnotationFileBoxes(inputDirectory, imageFilename, imageWidth, imageHeight, boxes, labels):
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	with open(annotationFileFullpath, "w") as annotationFile:
		for box in boxes:
			box = calculateNormalizedBoxNumbers(box[0], box[1], box[2], box[3], box[4], imageWidth, imageHeight, labels)
			line = getBoxWriteLine(box)
			annotationFile.write(line)


#TODO:  There's a "bug" where this function is getting / storing float values with higher precision than I'm getting later
#when retrieving the boxes from file.  This results in the removeBox function chain not properly matching the floats with each other when they should be exactly equal...
def addAnnotationFileBox(inputDirectory, imageFilename, imageWidth, imageHeight, box, labels):
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	box = calculateNormalizedBoxNumbers(box[0], box[1], box[2], box[3], box[4], imageWidth, imageHeight, labels)
	line = getBoxWriteLine(box)
	with open(annotationFileFullpath, "a") as annotationFile:
		annotationFile.write(line)


def removeBoxFromFile(inputDirectory, imageFilename, imageWidth, imageHeight, box, labels):
	#Convert the box to normalized data
	#Get the annotation file, copy all the data, iterate through all the lines, remove the line that matches the normalized box data line and exit
	print("in removeBoxFromFile")
	normalizedBox = calculateNormalizedBoxNumbers(box[0], box[1], box[2], box[3], box[4], imageWidth, imageHeight, labels)
	rawBox = getBoxWriteLine(normalizedBox)
	rawBoxes = getRawBoxesFromAnnotationFile(inputDirectory, imageFilename, imageWidth, imageHeight)
	
	boxLines = []
	print("box to match for deletion:")
	print(rawBox + "\n")
	for boxLine in rawBoxes:
		if boxLine + "\n" != rawBox:
			boxLines.append(boxLine + "\n")
			print("Not matched: " + boxLine + "\n")
		else:
			print("Matched: " + boxLine + "\n")
	
	setRawBoxesToAnnotationFile(inputDirectory, imageFilename, imageWidth, imageHeight, boxLines)
	
	return


def removeBoxFromBoxesList(box, boxes):
	#print("in removeBox, we have " + str(len(boxes)) + " boxes in the memory list")
	boxesToRemove = []
	for tempBox in boxes:
		#sets are kind of neat
		if len(box) == len(set(box).intersection(tempBox)):
			boxesToRemove.append(tempBox)
	
	for tempBox in boxesToRemove:
		boxes.remove(tempBox)
		#Woood...woood...a good woody word...gooone....gooone...goooone.  Gone.
	
	#print("leaving removeBox, we have " + str(len(boxes)) + " boxes in the memory list")
	return boxes


def isItFlatRectangle(x1, y1, x2, y2):
	if y2 - y1 == 0 or x2 - x1 == 0:
		#print("y2 - y1: " + str(y2) + " - " + str(y1) + " = " + str(y2 - y1))
		#print("x2 - x1: " + str(x2) + " - " + str(x1) + " = " + str(x2 - x1))
		#Absolutely NO flat rectangles - no point!  There needs to be pixels in them thar hills for YOLO to do anything with them.
		print("failed the flat rectangle test!")
		return True
	elif y2 - y1 == 0 and x2 - x1 == 0:
		print("failed the flat rectangle test!")
		return True
		#For those of you who love to clickity click without moving the mouse, winter's coming, lol (yes I know I don't need this one, but it's funny)
	else:
		return False

def calculateDistanceBetweenPoints(x1, y1, x2, y2):
	if isItFlatRectangle(x1, y1, x2, y2):
		return 0
	else:
		return math.sqrt(((y2 - y1) * (y2 - y1)) + ((x2 - x1) * (x2 - x1)))  #just the formula for distance between two points written out long form for a computer


def isPointInsideBox(x1, y1, boxX1, boxX2, boxY1, boxY2):
	#Very simple check - checks whether either of the x, y coordinates are outside the range of the box on their axis
	if x1 < boxX1 and x1 > boxX2:
		return False
	if y1 < boxY1 and y1 > boxY2:
		return False
	
	return True


def removeBox(x1, y1, inputDirectory,imageFilename, imageWidth, imageHeight, boxes, labels):
	#Find the boxes where boxX1 <= x1 and boxX2 >= x1 and boxY1 <= y1 and boxY2 >= y1
	#If there are multiple boxes (you can be inside multiple boxes), find the box where the boxX1 & boxY1 are the closest to x1, y1.
	#	Remove that box.  If there are multiple equidistant box upper left corners, then test for the closest lower right corner and remove that one...
	boxMatches = []
	for box in boxes:
		test = isPointInsideBox(x1, y1, box[1], box[2], box[3], box[4])
		if  test != False:
			distanceToTopLeftCorner = calculateDistanceBetweenPoints(x1, y1, box[1], box[2])
			distanceToBottomRightCorner = calculateDistanceBetweenPoints(x1, y1, box[3], box[4])
			boxMatch = [distanceToTopLeftCorner, distanceToBottomRightCorner, box]
			boxMatches.append(boxMatch)
		else:
			print("There are no points inside any boxes")
	
	print("There are " + str(len(boxMatches)) + " boxMatches!")
	
	if len(boxMatches) == 0:
		print("No box found to delete - press 'd' with the mouse cursor inside a box to delete it")
		return boxes
	
	elif len(boxMatches) == 1:
		removeBoxFromFile(inputDirectory, imageFilename, imageWidth, imageHeight, boxMatches[0][2], labels)
	
	elif len(boxMatches) > 1:
		#If there are somehow (!!) multiple boxes with the lowest values a matching distance, proceed to test distance between each boxX1, boxY1 and x1, y1
		#If there are twins where those distances match and are the lowest values, they are duplicate boxes and are going bye bye
		#https://docs.python.org/3/howto/sorting.html --> operator, itemgetter -> allows for sorting by multiple elements... itemgetter
		matches = sorted(boxMatches, key=itemgetter(0, 1)) #by default they will be ascending, starting with the lowest values...itemgetter(0) for instance references to boxMatches[0]
		#print(matches)
		
		#I'm going to be lazy here - you can delete up to two at once:
		firstMatchDistanceTopLeft = matches[0][0]
		firstMatchDistanceBottomRight = matches[0][1]
		secondMatchDistanceTopLeft = matches[1][0]
		secondMatchDistanceBottomRight = matches[1][1]
		if firstMatchDistanceTopLeft == secondMatchDistanceTopLeft and firstMatchDistanceBottomRight == secondMatchDistanceBottomRight:
			#Sink both their battleships!  Walk the plank!
			print("implement this never to be seen edge case")
			removeBoxFromFile(inputDirectory, imageFilename, imageWidth, imageHeight, matches[1][2], labels)

		removeBoxFromFile(inputDirectory, imageFilename, imageWidth, imageHeight, matches[0][2], labels)
		
	#Now to update the boxes list in memory so the deleted boxes don't keep getting displayed
	boxes = getBoxesFromAnnotationFile(inputDirectory, imageFilename, imageWidth, imageHeight, labels)
	return boxes

#Make sure that the values never get messed up by making negative rectangle widths and heights
def adjustXYvalues(boxX1, boxY1, boxX2, boxY2):
	#   IV    I			Cartesian Coordinate system
	#   III   II
	
	if boxX2 > boxX1 and boxY2 < boxY1:	#1st sector.
		#ex:	x1, y1:  0, 0
		#	x2, y2:  5, -5
		#new 	x1, y1:  0, -5		y1 <--> y2...no changes to x1 or x2
		#new	x2, y2:  5, 0
		tempY1 = boxY1
		boxY1 = boxY2
		boxY2 = tempY1
	if boxY2 > boxY1 and boxX2 < boxX1:   	#3rd sector.
		#ex:  	x1, y1:  0, 0		
		#	x2, y2: -5, 5
		#new	x1, y1: -5, 0		x1 <--> x2...switch x's, no change to y's.
		#new	x2, y2:  0, 5
		tempX1 = boxX1
		boxX1 = boxX2
		boxX2 = tempX1
	if boxX2 < boxX1 and boxY2 < boxY1:   	#4th sector.
		#ex:	x1, y1:  0, 0
		#	x2, y2: -5, -5
		#new	x1, y1: -5, -5		They both get switched out by the looks of it.
		#new	x2, y2:  0, 0
		tempX1 = boxX1
		boxX1 = boxX2
		boxX2 = tempX1
	#Otherwise, if it's in the 2nd sector (II), that's how it would work normally without adjustments.
		
		tempY1 = boxY1
		boxY1 = boxY2
		boxY2 = tempY1
	
	return boxX1, boxY1, boxX2, boxY2


#Convenience method for drawing rectangles on a pygame surface.
def drawRectangle(surface, lineColorToDraw, lineDrawWidth, boxX1, boxY1, boxX2, boxY2, label, myfont):
	#pygame.draw.rect(surface or array, rgb color in format (r, g, b), (x1, y1, rectangle width, rectangle height))
	rectangleWidth = boxX2 - boxX1
	rectangleHeight = boxY2 - boxY1
			
	#print("Drawing rectangle:  (x1, y1, width, height): (" + str(boxX1) + ", " + str(boxY1) + ", " + str(rectangleWidth) + ", " + str(rectangleHeight) + ")")
	if rectangleWidth > 0 and rectangleHeight > 0:
		pygame.draw.rect(surface, lineColorToDraw, (boxX1, boxY1, rectangleWidth, rectangleHeight), lineDrawWidth)
	#if rectangleWidth <= 0:
		#print("rectangleWidth <= 0")
	#if rectangleHeight <= 0:
		#print("rectangleHeight <= 0")
	
	#TODO blit the label - do the above with lines, make the top line have enough space in between in the middle for the fonted label
	return surface
	
	
#https://stackoverflow.com/questions/6444548/how-do-i-get-the-picture-size-with-pil
#Could also do these with cv2:  https://python-code.dev/articles/110664770  #images would be numpy arrays in this case, could be important for optimizing (if needed later)
#(note:  the drawLoop already seems to run pretty dang fast and this isn't a super heavy app, optimization may not be at all required)
def getImage(inputDirectory, imageFilename):
	image = Image.open(os.path.join(inputDirectory, imageFilename))
	imageWidth, imageHeight = image.size
	return image, imageWidth, imageHeight


def prepNextDataset(filenamesList, inputDirectory, filenamesListOffset, labels, labelIndex):
	boxes = []
	image, imageWidth, imageHeight = None, None, None
	
	if len(filenamesList) > filenamesListOffset:
		imageFilename = filenamesList[filenamesListOffset]
		image, imageWidth, imageHeight = getImage(inputDirectory, imageFilename)
	else:
		print("You've finished annotating all your available images, exiting.")
		exit()
		
	boxes = getBoxesFromAnnotationFile(inputDirectory, imageFilename, imageWidth, imageHeight, labels) #just in case there are already annotations for this image...
	imageCleanSurface = pygame.image.load(imageFilename)
	
	window = pygame.display.set_mode((imageWidth, imageHeight))
	window.fill((0, 0, 0))
	
	label = labels[labelIndex]
	pygame.display.set_caption('Pygame labeler. Current label: ' + label + ", image: " + imageFilename)
	
	return imageFilename, image, imageWidth, imageHeight, boxes, imageCleanSurface, window, None, None, None, None


#TODO:  Make this method much smaller later, once it's working, refactor out the draw stuff again
#TODO:  MAJOR code cleanup here
def drawLoop(filenamesList, inputDirectory, labels):
	pygame.init()
	
	red = (255, 0, 0)
	rectangleLineWidth = 5
	myfont = pygame.font.SysFont("monospace", 10)
	
	running = True
	filenamesListOffset = 0
	labelIndex = 0
	label = labels[labelIndex]
	counter = 0
	showCount = False
	
	imageFilename, image, imageWidth, imageHeight, boxes, imageCleanSurface, window, boxX1, boxY1, boxX2, boxY2 = prepNextDataset(filenamesList, inputDirectory, filenamesListOffset, labels, labelIndex)

	while running and image is not None:
		if showCount:		#an indicator for how fast the drawLoop while is running
			print("Frame: " + str(counter))
			counter += 1
		#Just being paranoid here about possible pygame window repositions by the user
		size = pygame.display.Info() #x, y, width, height
		displayWidth = size.current_w
		displayHeight = size.current_h
		if displayWidth != imageWidth:
			print("Strange - size[2] from pygame.display.Info() is not the same as the image.size[2] (imageWidth) gotten from getImage()!! - debugging needed.")
		if displayHeight != imageHeight:
			print("Strange - size[3] from pygame.display.Info() is not the same as the image.size[3] (imageHeight) gotten from getImage()!! - debugging needed.")

		for event in pygame.event.get():
		
			if event.type == pygame.QUIT:
				running = False

			#https://stackoverflow.com/questions/10990137/pygame-mouse-clicking-detection
			if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_focused():
				#print("received mouse click")
			
				if event.button == 1:  # left click
				
					pos = pygame.mouse.get_pos()
						
					if boxX1 is not None and boxX2 == None:
						#print("received left click X2: " + str(pos[0]) + ", " + str(pos[1]))
					
						boxX2 = pos[0]
						boxY2 = pos[1]
						
						#Adjusts for box tracking values when the mouse cursor goes in different directions
						boxX1, boxY1, boxX2, boxY2 = adjustXYvalues(boxX1, boxY1, boxX2, boxY2)
						
						#Don't allow single point or flat rectangles
						if isItFlatRectangle(boxX1, boxY1, boxX2, boxY2) != True:
							#print("passed isFlatRectangle test")
							rectWidth = boxX2 - boxX1
							rectHeight = boxY2 - boxY1

							boxList = [label, boxX1, boxY1, boxX2, boxY2]  #Now it's a list of lists, so more debugging down the method chain will be required
							addAnnotationFileBox(inputDirectory, imageFilename, imageWidth, imageHeight, boxList, labels)
							boxes.append(boxList)
						
							boxX1, boxY1, boxX2, boxY2 = None, None, None, None    #Clear out the tracking values for the next rectangle
					
					elif boxX1 == None:     #If there are no tracking points when left-clicked, this sets X1, Y1 up and the draw loop starts drawing a rect to the mouse pointer
						#print("Received left click: " + str(pos[0]) + ", " + str(pos[1]))
						boxX1 = pos[0]
						boxY1 = pos[1]
						

				#if event.button == 2:  # middle-click    #TODO:  Add this later and test/debug
				#	removeNearestBox()  #Actually, I'm having second thoughts - this is too close an action to the scroll wheel to change labels

				if event.button == 3:  # right-click --> clear the set box positions
					boxX1, boxY1, boxX2, boxY2 = None, None, None, None

				if event.button == 4:  # scroll-up
					#Change label previous (if not already #1)
					if labelIndex != 0:    #You can't go back from 0.  If you see -1 in the annotation file for the class, then there's a bug.
						labelIndex -= 1
						label = labels[labelIndex]
						pygame.display.set_caption('Pygame labeler. Current label: ' + label + ", image: " + imageFilename)
						print("Changed label to " + label + ", label index: " + str(labelIndex))
					else:
						print("You can't go back in labels any more, you are at the first one.")

				if event.button == 5:  # scroll-down
					#Change label next (if not at end)
					if len(labels) > labelIndex + 1:
						labelIndex += 1
						label = labels[labelIndex]
						pygame.display.set_caption('Pygame labeler. Current label: ' + label + ", image: " + imageFilename)
						print("Changed label to " + label + ", label index: " + str(labelIndex))
					else:
						print("You cannot go forward through labels any more, you are at the last one.")

			#handle keyboard button presses:
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_q:
					print("Goodbye!")
					exit("q key pressed, quitting.")
				if event.key == pygame.K_s:
					filenamesListOffset += 1
					imageFilename, image, imageWidth, imageHeight, boxes, imageCleanSurface, window, boxX1, boxY1, boxX2, boxY2 = prepNextDataset(filenamesList, inputDirectory, filenamesListOffset, labels, labelIndex)
					
				if event.key == pygame.K_d:
					pos = pygame.mouse.get_pos()
					#Now we're going headhunting for a box to eliminate
					boxes = removeBox(pos[0], pos[1], inputDirectory, imageFilename, imageWidth, imageHeight, boxes, labels)
		
		
		#Do the display updates here
		window.fill((0, 0, 0))
		window.blit(imageCleanSurface, (0, 0))
		
		#Create a new surface with a copy of the original image so we don't mess that up while drawing temporary (dynamic) boxes
		#Also, just in case we need to remove boxes, the original / clean image will be necessary for that
		
		#data = pygame.image.tostring(imageCleanSurface, 'RGBA')
		scratchimage = pygame.image.tostring(imageCleanSurface, 'RGBA')
		surfaceSize = imageCleanSurface.get_size()
		scratchSurface = pygame.image.fromstring(scratchimage, surfaceSize, 'RGBA', False)
		
		#Draw the dynamic box lines (to show the user where a box will be placed once they left-click once and before they left-click again to place it.
		if boxX1 is not None and boxY1 is not None and boxX2 == None and boxY2 == None:			
			pos = pygame.mouse.get_pos()
			tempX1 = boxX1
			tempY1 = boxY1
			mouseX = pos[0]
			mouseY = pos[1]
			tempX1, tempY1, mouseX, mouseY = adjustXYvalues(tempX1, tempY1, mouseX, mouseY)
			scratchSurface = drawRectangle(scratchSurface, red, rectangleLineWidth, tempX1, tempY1, mouseX, mouseY, label, myfont)

		if len(boxes) > 0:
			for box in boxes:
				scratchSurface = drawRectangle(scratchSurface, red, rectangleLineWidth, box[1], box[2], box[3], box[4], box[0], myfont)
				window.blit(scratchSurface, (0, 0))

		window.blit(scratchSurface, (0, 0))  #Only need one of these (though I'm not sure, may need separate ones for the font operations)
		
		pygame.display.flip()

	pygame.quit()
	

def main():
	inputDirectory = Path(getInputDirectory())

	filenamesList = getInputFilenames(inputDirectory)

	labels = getLabels(inputDirectory, "labels.txt")

	if len(filenamesList) > 0:
		drawLoop(filenamesList, inputDirectory, labels)

	else:
		print("Sorry, the input directory is empty of recognized image files.")

if __name__ == "__main__":
	main()
