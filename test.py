import argparse
import os
from os import walk
from pathlib import Path

def removeFile(filename, filepath):
	os.remove(filepath + "/" + filename)

def getInputDirectory():
	inputDirectory = None
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', default=os.getcwd())
	parser.add_argument('-d', '--docs', help='-d docs   Prints full help')
	args = parser.parse_args()

	if args.docs:
		print("will print full help")
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
	
def main():
	getInputDirectory()

if __name__ == "__main__":
	main()
