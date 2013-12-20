import magic, os, sys
from informacam_data_client import InformaCamDataClient

from vars import import_directory, scripts_home

sys.path.insert(0, "%sInformaCamUtils" % scripts_home['python'])
from funcs import ShellThreader

class ImportClient(InformaCamDataClient):
	def __init__(self, mode=None):
		super(ImportClient, self).__init__(import_directory['absorbed_log'], mode=mode)
		try:
			os.chdir(import_directory['asset_root'])
		except OSError as e:
			print e
			self.usable = False
		
	def getAssetMimeType(self, fileId):
		super(ImportClient, self).getAssetMimeType(fileId)
		
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
	
	def getFileName(self, file):
		super(ImportClient, self).getFileName(file)

		return file
		
	def validateMediaObject(self, fileId, returnType=False):
		super(ImportClient, self).validateMediaObject(fileId,returnType)
		
		input = os.path.join(os.getcwd(), fileId)
		output = "%s.log" % input[:-3]
				
		ffmpeg_thread = ShellThreader([
			"fab",
			"-f",
			os.path.join("%sInformaCamData" % scripts_home['python'],"ffmpeg_helper.py"),
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
	
	def listAssets(self, omit_absorbed=False):
		super(ImportClient, self).listAssets(omit_absorbed)
		
		assets = []
		new_time = 0
		for root, dirs, files in os.walk(import_directory['asset_root']):
			for file in files:
				s = os.stat(os.path.join(os.getcwd(), file))
				if s.st_ctime > self.last_update_for_mode:
					self.last_update_for_mode = s.st_ctime
				
				if omit_absorbed and self.isAbsorbed(os.path.join(os.getcwd(), file)):
					continue
				
				assets.append(file)
		
		return assets
	
	def pullFile(self, file):
		super(ImportClient, self).pullFile(file)
		
		file = os.path.join(os.getcwd(), file)
		f = open(file, 'rb')
		content = f.read()
		f.close()
		
		return content
			
	def isAbsorbed(self, file):
		super(ImportClient, self).isAbsorbed(file)
		
		s = os.stat(file)
		if s.st_ctime <= self.absorbedByInformaCam[self.mode]:
			return True
		
		return False
	
	def lockFile(self, file):
		super(ImportClient, self).lockFile(file)
		os.remove(file)
	
	def updateLog(self):
		super(ImportClient, self).updateLog(import_directory['absorbed_log'])