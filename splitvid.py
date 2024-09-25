#https://stackoverflow.com/questions/33311153/python-extracting-and-saving-video-frames
#Works for me :)  --> I modified starting at the code given in the above link.
import cv2  #pip install opencv-python
vidcap = cv2.VideoCapture('skywatching.mp4')
success,image = vidcap.read()
framesPerSecond = vidcap.get(cv2.CAP_PROP_FPS)
print("FPS: " + str(framesPerSecond))  #Only works for videos, won't work for webcams or other live cameras - for that use python's time class and count frames you get in a second.
count = 0
secondsInMinute = 60
skipBetweenFrames = framesPerSecond * secondsInMinute  #with the modulo operation below, this will have it only retrieve one frame per minute
skipFromStart = 360000
stop = 361806
totalFramesRead = 0
while success and count <= stop:
	if count > skipFromStart and (count == 0 or count % skipBetweenFrames == 0):   #the 'or' is necessary to prevent count % modNum from happening when count is 0 -> divide by zero error
		vidcap.set(cv2.CAP_PROP_POS_FRAMES, count-1)
		cv2.imwrite("frame%d.jpg" % count, image)     # save frame as JPEG file
		success,image = vidcap.read()
		print('Read a new frame: ' + str(success))
		if success:
			totalFramesRead += 1
	count += 1
print("Read " + str(totalFramesRead) + " frames")
