import gnupg
from multiprocessing import Process

from conf import gnupg_home, mime_types
from funcs import ShellThreader
from InformaCamModels.submission import Submission

class J3Mifier():
	def __init__(self, submission):
		'''
		print "j3mifying %s" % submission.asset_path

		self.input = os.join.path(submission.asset_path, submission.file_name)
		self.output = submission.asset_path
		
		mime_type = submission.mime_type
		
		self.submission = submission
		'''
		
		print "j3mifying %s" % submission['asset_path']

		self.input = os.join.path(submission['asset_path'], submission['file_name'])
		self.output = submission['asset_path']
		
		mime_type = submission['mime_type']
		
		self.submission = submission
		
		if mime_type == mime_types['image']:
			self.j3m = self.getImageMetadata()
		elif mime_type == mime_types['video']:
			self.j3m = self.getVideoMetadata()
		elif mime_type == mime_types['j3m']:
			self.j3m = self.getJ3MMetadata()
		
		if self.j3m is not None:
			self.verifySignature()
			self.verifyVisualContent()
		
		'''
		self.evaluateCameraFingerprint(submission._id)
		self.evaluateUsageFingerprint(submission._id)
		'''
	
	def getImageMetadata(self):
		"""
			returns the j3m embedded in a .jpg
		"""
		print "getting image metadata"
		# run j3mparser.out
		
		# dump result into a file called [fname].j3m.orig
		
		p = Process(target=self.makeDerivativeImages)
		p.start()
		
		# json read that file and return object
		
		return None
	
	def getVideoMetadata(self):
		"""
			returns the j3m embedded in an .mkv
		"""
		print "getting video metadata"
		# run ffmpeg command
		
		# dump result into a file called [fname].j3m.orig
		
		p = Process(target=self.makeDerivativeVideos)
		p.start()
		
		# json read that file and return object
		return None
	
	def getJ3MMetadata(self):
		"""
			parses the j3m file
		"""
		print "parsing j3m data"
		# rename as [fname].orig
		
		# json read that file nd return object
		
		return None
	
	def makeDerivativeImages(self):
		print "making derivative images"
	
	def makeDerivativeVideos(self):
		print "making derivative videos"
	
	def verifySignature(self):
		print "verifying signature"
		
		'''
		try:
			signature = self.j3m['signature']
			del self.j3m['signature']

			data_clone = open(d_clone, 'wb+')
			data_clone.write(json.dumps(data_))
			data_clone.close()
												
			print signature
			gpg = gnupg.GPG(homedir=gnupg_home)
			verified = gpg.verify_file(StringIO(signature), d_clone)
			
			if verified.fingerprint is None:
				from conf import invalidate
				invalid = [
					invalidate['codes']['j3m_not_verified'],
					invalidate['reasons']['j3m_not_verified']
				]
				
			os.remove(d_clone)
		except KeyError as e:
			print e
			print "signature already parsed"
			pass
		
		if invalid is not None:
			print invalid
		
		try:
			inflate = self.massageData(json.loads(data))
			inflate['_id'] = hashlib.sha1(data).hexdigest()
		except ValueError as e:
			print e
			return
		'''
	
	def verifyVisualContent(self):
		print "verifying visual content"
	
	def evaluateCameraFingerprint(self, submission_id):
		print "verifying camera fingerprint"
	
	def evaluateUsageFingerprint(self, submission_id):
		print "verifying usage fingerprint"