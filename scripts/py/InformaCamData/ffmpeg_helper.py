from fabric.api import *

def getInfo(input=None, output=None):
	print input
	print output
	local("ffmpeg -i %s > %s 2>&1" % (input, output))