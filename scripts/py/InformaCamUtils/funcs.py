import sys, subprocess, os, cStringIO, re, json, math, operator
import gzip, threading, hashlib

from Crypto.Cipher import AES
from Crypto import Random

from vars import api

R = 6372.8	#km

class ShellThreader(threading.Thread):
	"""Do a shell call in a new thread.  ShellThreader.output contains its result.

	arguments:
	* cmd (list)
	* op_dir (str) _optional_
	"""
	def __init__(self, cmd, op_dir=None):
		threading.Thread.__init__(self)
		self.cmd = cmd
		
		if op_dir is not None:
			self.return_dir = os.getcwd()
			os.chdir(op_dir)
		
	def run(self):
		self.output = ShellReader(self.cmd)
		if hasattr(self, 'return_dir'):
			os.chdir(self.return_dir)
			
class ExternalApiThreader(threading.Thread):
	def __init__(self, url, data=None, post=False, cookiejar=None, send_cookie=None):
		threading.Thread.__init__(self)
		self.url = url
		self.data = data
		self.post = post
		self.cookiejar = cookiejar
		self.send_cookie = send_cookie
		
	def run(self):
		self.output = callExternalApi(self.url, data=self.data, post=self.post, cookiejar=self.cookiejar, send_cookie=self.send_cookie)

def gzipAsset(path_to_file):
	_out = cStringIO.StringIO()
	_in = open(path_to_file)
	
	z = gzip.GzipFile(fileobj=_out, mode='w')
	z.write(_in.read())
	
	z.close()
	_in.close()
	
	return _out.getvalue()

def unGzipAsset(path_to_file):
	_in = open(path_to_file, 'rb')
	content = _in.read()
	_in.close()

	return gzip.GzipFile(fileobj=cStringIO.StringIO(content)).read()



def callExternalApi(url, data=None, post=False, cookiejar=None, send_cookie=None):	
	buf = cStringIO.StringIO()
	d = []
	dataString = None
	
	c = pycurl.Curl()
	
	c.setopt(c.VERBOSE, False)
	c.setopt(c.WRITEFUNCTION, buf.write)
	
	if data is not None:	# data is a dict
		for key, value in data.iteritems():
			d.append("%s=%s" % (key, value))
		dataString = "&".join(d)
		
		if not post:
			url = "%s?%s" % (url, dataString)
		else:
			if type(dataString) is unicode:
				dataString = str(unUnicode(dataString))
				
			c.setopt(c.POSTFIELDS, dataString)
			
	if cookiejar is not None:
		c.setopt(c.COOKIEJAR, cookiejar)
		
	if send_cookie is not None:
		c.setopt(c.COOKIE, send_cookie)
		
	print "CALLING API ON %s" % url	
	c.setopt(c.URL, url)
	c.perform()
	
	res = buf.getvalue()
	buf.close()
	
	return str(res)

def callApi(url, data=None, post=False):
	url = "http://localhost:%d/%s/" % (api['port'], url)
	
	buf = cStringIO.StringIO()
	d = []
	dataString = None
	
	c = pycurl.Curl()
	
	c.setopt(c.VERBOSE, False)
	c.setopt(c.WRITEFUNCTION, buf.write)
	
	if data is not None:	# data is a dict
		for key, value in data.iteritems():
			d.append("%s=%s" % (key, value))
		dataString = "&".join(d)
		
		if not post:
			url = "%s?%s" % (url, dataString)
		else:
			c.setopt(c.POSTFIELDS, dataString)
		
	print "CALLING API ON %s" % url	
	c.setopt(c.URL, url)
	c.perform()
	
	res = buf.getvalue()
	buf.close()
	
	return json.loads(str(res))
		
def saveRawFile(destination, content):
	file = open(destination, 'w+')
	file.write(content)
	file.close()
	return True

def passesParameterFilter(req):
	# looking for pipes
	match = re.search(r'\s*\|\s*.+', req)
	if match:
		print "found a pipe:\n%s" % match.group()
		return False

	# looking for two periods and slashes "\..\"
	match = re.search(r'\.\./', req)
	if match:
		print "found a file inclusion attempt:\n%s" % match.group()
		return False

	# looking for XSS using broken element tags (i.e. <svg/onload=alert(1)>
	match = re.search(r'<\s*\w+/\s*.+=.*\s*>', req)
	if match:
		print "found an XSS attempt using broken element tag:\n%s" % match.group()	
		return False

	return True

def parseRequest(request_string):
	try:
		if passesParameterFilter(request_string):
			return json.loads(request_string)
		else:
			return None
	except ValueError as e:
		pass

	params = dict()
	for kvp in [word for word in request_string.split("&") if word != ""]:
		k = kvp.split("=")[0]
		
		v = kvp.split("=")[1]
		if passesParameterFilter(k) and passesParameterFilter(v):
			params[k] = AsTrueValue(v)	# this might catch on arrays; please check!

	return params

def parseArguments(arguments):
	params = dict()

	for key in arguments:
		if not passesParameterFilter(key):
			return None

		for k in arguments[key]: 
			params[key] = []
			if k[0] is "[" and k[-1] is "]":				
				for value_ in str(k[1:-1]).split("],["):
					arr = []
					for value in value_.split(","):
						if passesParameterFilter(value):
							arr.append(AsTrueValue(value))

					params[key].append(arr)
			else:
				for value in k.split(","):
					if passesParameterFilter(value):
						params[key].append(AsTrueValue(value))

	print "%s transformed to %s" % (arguments, params)
	return params

def AsTrueValue(str_value):
	try:
		if str_value.startswith("[") and str_value.endswith("]"):
			vals = []
			for v_ in str(str_value[1:-1]).split(","):
				vals.append(AsTrueValue(v_))

			return vals
		if str_value.startswith("{") and str_value.endswith("}"):
			return json.loads(str_value)
		if str_value == "0":
			return int(0)
		if str_value == "true":
			return True
		if str_value == "false":
			return False
		if type(str_value) is unicode:
			return unicode.join(u'\n', map(unicode, str_value))
	except AttributeError:
		pass
	
	try:
		if int(str_value):
			return int(str_value)
	except ValueError:
		pass
		
	try:
		if float(str_value):
			return float(str_value)	
	except ValueError:
		pass
		
	return str_value

def GetTrueValue(str_value):
	str_value = str(str_value)
	if str_value.startswith("[") and str_value.endswith("]"):
		return 'list'
	if str_value == "0":
		return 'int'
	if str_value == "true" or str_value == "false":
		return 'bool'
	try:
		if int(str_value):
			return 'int'
	except ValueError as e:
		#print "GET TRUE VALUE ERROR: %s so i returned i try float " % e
		pass
		
	try:
		if float(str_value):
			return 'float'
	except ValueError as e:
		#print "GET TRUE VALUE ERROR: %s so i returned i return str " % e
		pass
		
	return 'str'
	
def unUnicode(data):
		return AsTrueValue(unicode.join(u'\n', map(unicode, data)))
		
def ShellReader(cmd, omitNewLine = True, do_print=True):
	#print "CMD: %s" % cmd

	data_read = []
	ex = subprocess.Popen(
		cmd,
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		close_fds=True
	)
	(stdout, stdin) = (ex.stdout, ex.stdin)
	data = stdout.readline()
	while data:
		#print data

		if omitNewLine is True and (data.find("\n") or data.find("\r")):
			data_read.append(data[:-1])
		else:	
			data_read.append(data)

		data = stdout.readline()

	stdout.close()
	stdin.close()

	return data_read
	
def makeBoundingBox(lat, lon, radius):
	"""Returns a bounding box of specified radius around given lat/lon point.
	
	arguments:
	* lat (float)
	* long (float)
	* radius (int)
	"""
	
	print "making a bounding box for [%f,%f] (radius = %d km)" % (lat, lon, radius)
	
	d_lat = radius/R
	d_lon = math.asin(math.sin(d_lat)/math.cos(math.radians(lat)))
	
	d_lat, d_lon = math.degrees(d_lat), math.degrees(d_lon)
	
	original_box = [lat, lon, lat, lon]
	offsets = []
	offsets.extend(map(math.radians, (lon - d_lon, lon + d_lon)))
	offsets.extend(map(math.radians, (lat - d_lat, lat + d_lat)))
	
	return map(operator.add, original_box, offsets)

def haversine(lat_lon_1, lat_lon_2):
	"""Returns the haversine distance between to lat/lon points.
	
	arguments:
	* lat_lon_1 (dict {latitude=float, longitude=float})
	* lat_lon_2 (dict {latitude=float, longitude=float})
	"""
	
	d_lat = math.radians(lat_lon_2['latitude'] - lat_lon_1['latitude'])
	d_lon = math.radians(lat_lon_2['longitude'] - lat_lon_1['longitude'])
	lat_1 = math.radians(lat_lon_1['latitude'])
	lat_2 = math.radians(lat_lon_2['latitude'])
	
	a = math.sin(d_lat/2) * math.sin(d_lat/2) + math.sin(d_lon/2) * math.sin(d_lon/2) * math.cos(lat_1) * math.cos(lat_2)
	c = 2 * math.asin(math.sqrt(a))
	
	print "haversine distance: %d km" % (R * c)
	return R * c
	
def isWithinRange(range, target):
	return range[0] <= target <= range[1]
	
def isNearby(lat_lon_1, lat_lon_2, radius):
	return haversine(lat_lon_1, lat_lon_2) <= radius