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
#2.  Put all image file names into a list
#3.  Check to see how many image types I can reasonably support with pygame.
#4.  Load first image and enter loop:
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
	

def getLabels(inputDirectory, labelFileName):
	labels = None
	with open(os.path.join(inputDirectory, labelFileName)) as f:
		labels = f.read().splitlines()
	return labels


#The annotation file for a given image will have the same filename, except the prefix will be .txt  (so there will be a separate annotation file for each image that holds all the label box details)
#The format for each line in the file is classNumber boxCenterX boxCenterY boxWidth boxHeight  --> these are all normalized (between 0 and 1, as a percentage of totalX, totalY, totalWidth, totalHeight
#For instance, to find the boxCenterX, you'd first get the X of the box's center in the image, then do boxCenterX = boxCenterX / imageTotalX
#Another example, to find the total box width, first find the box width (x2 - x1), then box normalized width = (box width) / (image width)
def getBoxesFromAnnotationFile(inputDirectory, imageFileName):
	inputDirectory = Path(inputDirectory)
	filename, extension = os.path.splitext(imageFileName)  #get the image extension off the image file name
	
	annotationFilename = filename + ".txt" #the image annotation file has the same first part of the name but the extension is ".txt" instead of the image extension.

	annotationFileFullpath = inputDirectory / annotationFilename
	
	boxes = []
	with open(annotationFileFullpath, "r") as annotationFile:
		for line in annotationFile:
			boxes.append(line.rstrip())   #append to the boxes list without the "\n" line breaks
	
	return boxes
	
	
def drawBoxesOnImage(image, boxes, labels):
	# Draw the image to window
	# Draw the boxes and put the label on its top line in a font
	#https://stackoverflow.com/questions/10077644/how-to-display-text-with-font-and-color-using-pygame


def drawTempBoxOnImage(image, boxes, labels):
	drawBoxesOnImage(image, boxes, labels)
	#https://www.pygame.org/docs/ref/mouse.html#pygame.mouse.get_pos
	x, y = pygame.mouse.get_pos()

def addBoxToImageAnnotationFile(label_index, x1, y1, x2, y2, imageWidth, imageHeight, imageFileName):
	width = x2 - x1
	height = y2 - y1
	center_x = x1 + width / 2   #LOL - I'm not sure I'm going the right way on these...my boxes might be screwed up
	center_y = y1 + height / 2

	#https://blog.paperspace.com/train-yolov5-custom-data/
	#One row per object
	#Each row is class x_center y_center width height format.
	#Box coordinates must be normalized by the dimensions of the image (i.e. have values between 0 and 1)
	#Class numbers are zero-indexed (start from 0).
	normalizedCenterX = width 
	normalizedCenterY = height / imageHeight
	normalizedWidth = width / imageWidth
	normalizedHeight = height / imageHeight

	line = label_index + " " + normalizedCenterX + " " + normalizedCenterY + " " + normalizedWidth + " " + normalizedHeight + "\n"

	with open(os.path.join(inputDirectory, imageFileName), 'a') as f:   #open the file in append mode
		f.write(line)

def removeBoxFromImageAnnotationFile(label_index, x1, y1, x2, y2, imageWidth, imageHeight, imageFileName):
	#TODO


def drawLoop(filenamesList, inputDirectory, labels):
	pygame.init()
	#Clear the screen and paste the first image
        #https://gamedevacademy.org/pygame-background-image-tutorial-complete-guide/
	label_index = 0
	label = labels[label_index]
	running = True
	while running:
		for image in filenamesList:
			#https://stackoverflow.com/questions/6444548/how-do-i-get-the-picture-size-with-pil
			#Could also do these with cv2:  https://python-code.dev/articles/110664770  #images will be numpy arrays then
			image = Image.open(os.path.join('inputDirectory', filenamesList[0]))
			if image:
				width, height = image.size
				#https://stackoverflow.com/questions/4135928/pygame-display-position
				game_dislay = pygame.display.set_mode((width, height))
				window.fill((0, 0, 0))

				thisImage = True
				x1 = None #tempBoxUpperLeftX
				y1 = None #tempBoxUpperLeftY
				x2 = None #tempBoxLowerRightX
				y2 = None #tempBoxLowerRightY

				while thisImage and running:
					size = pygame.display.Info() #x, y, width, height

					for event in pygame.event.get():
						if event.type == pygame.QUIT:
							running = False

						#https://stackoverflow.com/questions/10990137/pygame-mouse-clicking-detection
						if event.type == pygame.MOUSEBUTTONDOWN:

							if event.button == 1:  # left click
								pos = pygame.mouse.get_pos() # (x, y)
								#A backup might be:  https://stackoverflow.com/questions/25848951/python-get-mouse-x-y-position-on-click
								if tempBoxTopLeftX == None:
									x1 = pos[0]  #tempBoxUpperLeftX
									y1 = pos[1]  #tempBoxUpperLeftY
								else:
									x2 = pos[0]  #tempBoxLowerRightX
									y2 = pos[1]  #tempBoxLowerRightY

									addBoxToImageAnnotationFile(x1, y1, x2, y2, label)

							if event.button == 2:  # middle-click
								removeNearestBox()

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

						if event.type == pygame

						if x1 not None:
							pos = pygame.mouse.get_pos()
							drawBoxesOnImage()
							drawTempBoxOnImage(x1, y1, pos[0], pos[1], label)

					game.display.blit(image, (0, 0))
					pygame.display.update()

	pygame.quit()

def main():
	inputDirectory = Path(getInputDirectory())

	filenamesList = getInputFilenames(inputDirectory)

	labels = getLabels(inputDirectory, "labels.txt")

	if filenamesList.len > 0:
		drawLoop(filenamesList, inputDirectory)

	else:
		print("Sorry, the input directory is empty of recognized image files.")

if __name__ == "__main__":
	main()
