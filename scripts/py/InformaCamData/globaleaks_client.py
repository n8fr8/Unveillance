import magic, os, json, sys, re, time
from math import fabs

from informacam_data_client import InformaCamDataClient
from conf import globaleaks, scripts_home

sys.path.insert(0, "%sInformaCamUtils" % scripts_home['python'])
from funcs import ShellReader, ShellThreader

class GlobaleaksClient(InformaCamDataClient):
	def __init__(self):
		super(GlobaleaksClient, self).__init__()
		
		os.chdir("%sInformaCamData" % scripts_home['python'])
		try:
			f = open(globaleaks['absorbed_log'], 'rb')			
			self.absorbedByInformaCam = int(f.read().strip())
			f.close()
		except:
			self.absorbedByInformaCam = 0
	
	def sshToHost(self, function, extras=None):
		args = [
			"host=%s" % globaleaks['host'],
			"user=%s" % globaleaks['user'],
			"key_filename=%s" % globaleaks['identity_file'],
			"asset_root=%s" % globaleaks['asset_root']
		]
		
		if extras is not None:
			args = args + extras
			
		ssh_thread = ShellThreader([
			"fab",
			"-f",
			os.path.join(os.getcwd(), "ssh_helper.py"),
			"%s:%s" % (function, ",".join(args))
		])
		
		ssh_thread.start()
		return ssh_thread
	
	def getAssetMimeType(self, fileId):
		if fileId.find("gpg_encrypted-") >= 0:
			# delete file locally
			return None
			
		fileId = fileId.replace(" ", "")
		if fileId == "":
			return None
			
		super(GlobaleaksClient, self).getAssetMimeType(fileId)
		
		self.sshToHost('pullFile', extras=[
			"file=%s" % fileId,
			"asset_dump=%s@%s:/home/%s" % (
				globaleaks['user'], 
				globaleaks['host'], 
				globaleaks['user']
			),
			"local_dump=%s" % os.getcwd()
		]).join()
		
		m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
		try:
			mime_type = m.id_filename(os.path.join(os.getcwd(), fileId))
			print "FILE MIME TYPE: %s" % mime_type
		except:
			print "error here getting mime type"
			return None
		m.close()
		
		if mime_type == self.mime_types['wildcard']:
			mime_type = self.validateMediaObject(fileId, returnType=True)
		
		return mime_type
				
	def validateMediaObject(self, fileId, returnType=False):
		fileId = fileId.replace(" ", "")
		super(GlobaleaksClient, self).validateMediaObject(fileId,returnType)
		
		input = os.path.join(os.getcwd(), fileId)
		output = "%s.log" % input[:-3]
				
		ffmpeg_thread = ShellThreader([
			"fab",
			"-f",
			os.path.join(os.getcwd(),"ffmpeg_helper.py"),
			"getInfo:input=%s,output=%s" % (input, output)
		])
		ffmpeg_thread.start()
		ffmpeg_thread.join()
		
		isValid = False
		mime_type_found = None
		input_0 = None
		input_0_sentinel = "Input #0, "
		
		for line in open(output, 'r'):
			input_0_location = line.find(input_0_sentinel)
			
			if input_0_location >= 0:
				input_0 = line[(input_0_location + len(input_0_sentinel)):]
				print input_0
				if input_0.find("matroska") >= 0:
					isValid = True
					mime_type_found = self.mime_types['video']
					break
				elif input_0.find("image2") >= 0:
					isValid = True
					mime_type_found = self.mime_types['image']
					break
				
		os.remove(output)
		
		if not returnType:
			return isValid
		else:
			return mime_type_found
		
	def mapMimeTypeToExtension(self, mime_type):
		super(GlobaleaksClient, self).mapMimeTypeToExtension(mime_type)
		
		return self.mime_type_map[mime_type]
		
	def getFile(self, fileId):
		fileId = fileId.replace(" ", "")
		super(GlobaleaksClient, self).getFile(fileId)
		
		# does nothing, really
		return fileId
		
	def pullFile(self, file):
		file = file.replace(" ", "")
		super(GlobaleaksClient, self).pullFile(file)
		# already pulled.
		
		file = os.path.join(os.getcwd(), file)
		f = open(file, 'rb')
		content = f.read()
		f.close()
		
		return content
		
	def lockFile(self, file):
		super(GlobaleaksClient, self).lockFile(file)
		
		file = os.path.join(os.getcwd(), file)
		ShellReader(['rm', file])
		
	def listAssets(self, omit_absorbed=False):
		super(GlobaleaksClient, self).listAssets(omit_absorbed)
		
		assets = []
		sentinel = "[%s] out: " % globaleaks['host']
		
		asset_thread = self.sshToHost('listAssets')
		asset_thread.join()
		
		for line in asset_thread.output:
			l_match = re.search(re.escape(sentinel), line)
			if l_match is not None:
				line = line.replace(sentinel, '').split(" ")
				line[:] = [word for word in line if word != '']
				
				if line[-1] == "." or line[-1] == "..":
					continue
				
				if re.match(r'^gpg_encrypted-.*', line[-1]):
					continue
				
				date_str = " ".join(line[-4:-2])
				date_admitted = time.strptime(date_str, "%Y-%m-%d %H:%M:%S")
				
				if omit_absorbed and self.isAbsorbed(time.mktime(date_admitted)):
					continue
						
				assets.append(file)

		self.absorbedByInformaCam = time.time()
		f = open(globaleaks['absorbed_log'], 'wb+')
		f.write(self.absorbedByInformaCam)
		f.close()
		
		return assets
		
	def isAbsorbed(self, date_admitted):
		if date_admitted < self.absorbedByInformaCam
		 	return True
		
		return False

	def absorb(self, file):
		super(GlobaleaksClient, self).absorb(file)
		
	def getFileName(self, file):
		super(GlobaleaksClient, self).getFileName(file)

		return file
	
	def getFileNameHash(self, file):
		return super(GlobaleaksClient, self).getFileNameHash(file)
