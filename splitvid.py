#https://stackoverflow.com/questions/33311153/python-extracting-and-saving-video-frames
#Works for me :)
import cv2
vidcap = cv2.VideoCapture('skywatching.mp4')
success,image = vidcap.read()
count = 0
while success and count < 2001:   #mp4 videos seem to usually have 30 frames per second...
  cv2.imwrite("frame%d.jpg" % count, image)     # save frame as JPEG file      
  success,image = vidcap.read()
  print('Read a new frame: ', success)
  count += 1
