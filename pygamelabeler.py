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


#Just give me values I can work with on screen:
def getBoxValuesFromStrings(box, imageWidth, imageHeight, labels):
	labelIndexStr, normalizedBoxCentroidXStr, normalizedBoxCentroidYStr, normalizedBoxWidthStr, normalizedBoxHeightStr = box.slit()
	label = labels[int(labelIndexStr)]
	normalizedBoxCentroidX = float(normalizedBoxCentroidXStr)
	normalizedBoxCentroidY = float(normalizedBoxCentroidYStr)
	normalizedBoxWidth = float(normalizedBoxWidthStr)
	normalizedBoxHeight = float(normalizedBoxHeightStr)
	
	box = [label, normalizedBoxCentroidX, normalizedBoxCentroidY, normalizedBoxWidth, normalizedBoxHeight]
	
	return box


def getImageBoxCoordinateFromNormalizedValues(box, imageWidth, imageHeight, labels):
	box = getBoxValuesFromStrings(box, imageWidth, imageHeight, labels)
	
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
	
	boxDataForDrawing = [label, boxX1, boxY1, boxX2, boxY2]
	
	return boxDataForDrawing
	

#See calculateNormalizedBoxNumbers for exact formatting instructions / how to calculate them.
def getBoxesFromAnnotationFile(inputDirectory, imageFilename, imageWidth, imageHeight, labels):
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	
	rawBoxes = []
	boxes = []
	try:
		with open(annotationFileFullpath, "r") as annotationFile:
			for line in annotationFile:
				boxes.append(line.rstrip())   #append to the boxes list without the "\n" line breaks
	
		for box in rawBoxes:
			boxForDrawing = getImageBoxCoordinateFromNormalizedValues(box, imageWidth, imageHeight, labels)
			boxes.append()
	except OSError as e:
		print("Annotation file does not exist yet, we'll make it later: " + str(annotationFileFullpath))

	return boxes


#This converts from a box in list format to a string so it can be written to an image annotation file.
def getBoxWriteLine(box):
	return box[0] + " " + box[1] + " " + box[2] + " " + box[3] + " " + box[4] + "\n"
	

#In the annotation files, all the boxes (one per line) are stored in normalized format in a space delimited string (with a line break '\n' at the end).
#In order to display the boxes over the image, I need their X1, Y1, X2, and Y2 values in image coords.
#I also need the values as separate elements in a list in order to be easily referenced.
def calculateNormalizedBoxNumbers(label, boxX1, boxY1, boxX2, boxY2, imageWidth, imageHeight, labels):

	labelIndex = labels.index(label)  #LOL, oof...I knew there was something easy  https://stackoverflow.com/questions/176918/how-to-find-the-index-for-a-given-item-in-a-list

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
	
	box = [labelIndex, normalizedCenterX, normalizedCenterY, normalizedWidth, normalizedHeight]
	
	return box
	

#I'll run this when saving the annotation file or when deleting a box.  When just adding a single box, I'll run addAnnotationFileBox() which opens the file in append mode.
def setAnnotationFileBoxes(inputDirectory, imageFilename, imageWidth, imageHeight, boxes, labels):
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	with open(annotationFileFullpath, "w") as annotationFile:
		for box in boxes:
			box = calculateNormalizedBoxNumbers(box[0], box[1], box[2], box[3], box[4], imageWidth, imageHeight, labels)
			line = getBoxWriteLine(box)
			annotationFile.write(line)


def addAnnotationFileBox(inputDirectory, imageFilename, imageWidth, imageHeight, box, labels):
	annotationFileFullpath = getAnnotationFileName(inputDirectory, imageFilename)
	box = calculateNormalizedBoxNumbers(box[0], box[1], box[2], box[3], box[4], imageWidth, imageHeight, labels)
	line = getBoxWriteLine(box)
	with open(annotationFileFullpath, "a") as annotationFile:
		annotationFile.write(line)


#I'm just going to put the draw method stuff in the main loop for now, hopefully I can keep it simple.
#def drawBoxOnWindow(label, x1, y1, x2, y2, myfont):
	# Draw the boxes and put the label on its top line in a font
	#https://stackoverflow.com/questions/10077644/how-to-display-text-with-font-and-color-using-pygame
	#https://www.geeksforgeeks.org/pygame-drawing-objects-and-shapes/
	
	#keep the image object as a reference, do a full window fill every time, and always write the image to the display, then boxes, then tempbox every time
	#pygame.draw.rect(window, (0, 0, 255), 			#well....that was easy...bet the fonts won't be nearly as easy when doing a bunch of them
        #         [x1, y1, x2, y2], 2)  #the last number is the thickness of the rectangle lines
        #Note, keeping this method for reference, though I'm putting it in the drawloop directly for now.  If I end up making icons or anything like that, I'll need to do something more complex.
        #I probably won't, the whole reason for making this was to have a lower level tool that's much simpler / more rugged.
        
        #https://stackoverflow.com/questions/25149892/how-to-get-the-width-of-text-using-pygame
        #text_width, text_height = self.font.size("txt")
        #textWidth, textHeight = myfont(label)
        #screen.blit(my_text, displayX, displayY)  #will put the font in starting at displayX, displayY


#This is entirely so that box lines will follow the mouse cursor / be visible between your first left-click and second left-click when creating a box.
#Remember, right-click to cancel box creation (before left-clicking the second time)
#def drawTempBoxOnImage(image, imageWidth, imageHeight, x1, y1, label, myfont):
	#image = drawBoxesOnImage(image, imageWidth, imageHeight, labels)  #going to move this call to the drawloop for now
	
	#Now draw a single temp box based on where the mouse cursor is:
	#https://www.pygame.org/docs/ref/mouse.html#pygame.mouse.get_pos
	#x2, y2 = pygame.mouse.get_pos() #get the mouse cursor position for the next step
	
	#I always want the x1 and y1 to be the upper left corner, so if order is switched, put them in the right order
	#Hmmm...if I click for the first time then go up and left, I'm messing up my drawloop variables...might need to think about this one...
	#TODO:  make it dynamically update order as the mouse position dictates ordering (for later...let's keep this simple)
	'''
	if x1 > x2:
		x1temp = x1
		x1 = x2
		x2 = x1temp
	if y1 < y2:
		y1temp = y1
		y1 = y2
		y2 = y1temp
	'''
	
	#drawBoxOnWindow(label, x1, y1, x2, y2, myfont)


#TODO:  I'll get this working later once I get the temp box displaying
#I'm not sure how I'm going to do so many label fonts yet - I'll probably need a separate list to keep track with positions, then
#blit them all to the screen at once since pygame doesn't blit to image files as far as I know and I want to keep the image files themselves clean anyway.
'''
def drawBoxes(image, boxes, labels):
	imageWidth, imageHeight = image.size
	for box in boxes:
		labelIndex = box[0]
		label = labels[labelIndex]
		image = drawBoxOnImage(drawBox[1], drawBox[2], drawBox[3], drawBox[4], label)
	return image
'''
	

#I'm going to test only progressing forward through boxes and images first, then I'll add box delete functionality
#def removeBoxFromBoxes(label_index, x1, y1, x2, y2, imageWidth, imageHeight, imageFileName):
	#TODO
	
	
#https://stackoverflow.com/questions/6444548/how-do-i-get-the-picture-size-with-pil
#Could also do these with cv2:  https://python-code.dev/articles/110664770  #images would be numpy arrays in this case, could be important for optimizing (if needed later)
def getImage(inputDirectory, imageFilename):
	image = Image.open(os.path.join(inputDirectory, imageFilename))
	imageWidth, imageHeight = image.size
	return image, imageWidth, imageHeight


#TODO:  Make this method much smaller later, once it's working, refactor out the draw stuff again
def drawLoop(filenamesList, inputDirectory, labels):
	pygame.init()
	#Clear the screen and paste the first image
        #https://gamedevacademy.org/pygame-background-image-tutorial-complete-guide/
	labelIndex = 0
	label = labels[labelIndex]
	running = True
	filenamesListOffset = 0
	imageFilename = filenamesList[filenamesListOffset]
	image, imageWidth, imageHeight = getImage(inputDirectory, imageFilename)
	boxes = getBoxesFromAnnotationFile(inputDirectory, imageFilename, imageWidth, imageHeight, labels) #just in case there are already annotations for this image...
	
	#https://stackoverflow.com/questions/4135928/pygame-display-position
	game_dislay = pygame.display.set_mode((imageWidth, imageHeight))
	window.fill((0, 0, 0))
	myfont = pygame.font.SysFont("monospace", 10)
	while running and image is not None:
		#Just being paranoid here about possible pygame window repositions by the user
		size = pygame.display.Info() #x, y, width, height
		imageTopLeftX = size[0]
		imageTopLeftY = size[1]
		if size[2] != imageWidth:
			print("Strange - size[2] from pygame.display.Info() is not the same as the image.size[2] (imageWidth) gotten from getImage()!! - debugging needed.")
		imageWidth = size[2]
		if size[3] != imageHeight:
			print("Strange - size[3] from pygame.display.Info() is not the same as the image.size[3] (imageHeight) gotten from getImage()!! - debugging needed.")
		imageHeight = size[3]
		
		boxX1 = None #tempBoxUpperLeftX
		boxY1 = None #tempBoxUpperLeftY
		boxX2 = None #tempBoxLowerRightX
		boxY2 = None #tempBoxLowerRightY

		#First get the temp boxes displaying and this thing running with no errors on start / drawLoop getting through while clicking the first time for a temp box.
		for event in pygame.event.get():
		
			if event.type == pygame.QUIT:
				running = False

			#https://stackoverflow.com/questions/10990137/pygame-mouse-clicking-detection
			if event.type == pygame.MOUSEBUTTONDOWN:
			
				if event.button == 1:  # left click
				
					pos = pygame.mouse.get_pos()
					
					#A backup might be:  https://stackoverflow.com/questions/25848951/python-get-mouse-x-y-position-on-click
					if boxX1 == None:
						
						boxX1 = pos[0] - imageTopLeftX  #tempBoxUpperLeftX   #TODO I'm not too sure about these lines yet...plenty of debugging ahead...
						boxY1 = pos[1] - imageTopLeftY #tempBoxUpperLeftY
						
					elif boxX1 is not None and boxX2 == None:
					
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
					if label_index != 0:    #You can't go back from 0.  If you see -1 in the annotation file for the class, then there's a bug.
						label_index -= 1
						label = labels[label_index]

				if event.button == 5:  # scroll-down
					#Change label next (if not at end)
					if labels.len > label_index + 1:
						label_index += 1
						label = labels[label_index]

			'''
			#handle keyboard button presses:
			if event.type == pygame. ??
				#first thing to handle here is 's' - save all the boxes to image annotation file, then load the next image
			'''
		
		#Do the display updates here
		game.display.blit(image, (0, 0))
		
		#Now draw the boxes, starting with the temp box (if any) over the display
		if boxX1 is not None and boxY1 is not None and boxX2 == None and boxY2 == None:
			#We're not saving this image, it's just for display, we build/draw the boxes on each loop, so if we get rid of any boxes, they'll go away on next time through the loop
			#image = drawTempBoxOnImage(image, imageWidth, imageHeight, boxX1, boxY1, label, myfont)
			x2, y2 = pygame.mouse.get_pos()
			#draw a red box from the marked X, Y to the mouse cursor position (X2, Y2)
			pygame.draw.rect(window, (255, 255, 0),
        		        [x1, y1, x2, y2], 2)
			
			#Note:  I need to blit the label on the top line (in the middle of the line between X1, Y1 and X2, Y1)
			#Note:  I might need to draw my own rect line by line so that I can put the font on the top line without the line going through it (so essentially I'd have two lines
			#for the top one)
		
		'''
		#TODO:  Do final debugging / get this working once the temp boxes are going
		#Draw all the boxes we've already set
		if len(boxes) > 0:
			#drawBoxesOnImage(image, boxes, labels)
			for box in boxes:
				pygame.draw.rect(window, (0, 0, 255), 			#well....that was easy...bet the fonts won't be nearly as easy when doing a bunch of them
                			[x1, y1, x2, y2], 2)  #the last number is the thickness of the rectangle lines
		'''
		
		#I might put all the font blitting here after making a full list of labels with image coords for display on top of the image.
		
		pygame.display.update()

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
