# pygameYOLOlabeler
Uses pygame to create a simple interface to quickly put boxes on objects in images - creates annotation files for YOLO neural net training (the boxes on images do not modify the original image files, they are stored in annotation files).

I am writing this currently without LLM help (old style), so it'll be a bit slower going.  As of 24 Sep 2024, I have most of the major bugs I noticed ironed out.  There may still be lurking bugs (especially in the removeBlock function chain that removes the labelling squares (I called them blocks) from memory and the annotation file.

To use:
The easiest way I find to use this is to copy the following files into a directory (and have a movie ready that you want to annotate from):
labels.txt, yourMovie.mp4, splitvid.py, pygamelabeler.py

Make a python virtual environment:
"/python -m venv ."
Activate the virtual environment so all the installs you do will be kept there:
"source bin/activate"  (slightly different on non-*nix operating systems)

Install the dependencies needed to run the two scripts (splitvid.py & pygamelabeler.py):
"pip install opencv-python"
"pip install pillow"
"pip install pygame"

Open splitvid.py and change the name of the movie to the one you're going to use.  And the number of frames you want to extract (typically movies are something like 30 frames per second, so you may have problems if you try to extract a whole multi-hour long movie to jpg files).

Open labels.txt and make sure it has the class types (labels) you want in it.  They are comma separated.

run "python splitvid.py" - the number of frames you specified will be extracted and placed in individually / sequentially numbered jpeg files (.jpg) in the current directory.

Finally, run pygamelabeler.py without arguments (it'll automatically use the current directory as the input directory and grab any images with the file name extensions coded in (which includes .jpg).
"python pygamelabeler.py"

Everything else should be automatic for you as you annotate the images using the interface window that pops up.  Any further questions, try reading the help, other comments at the top, or for in depth questions, check out the code and all the comments on that (extremely in depth questions might be answered by reading the commits).
