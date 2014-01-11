import re, json, os, magic
from base64 import b64encode

from funcs import ShellThreader, getMimeTypeFromFile, hashString
from vars import mime_types, mime_type_map

class J3MLogger():
	def __init__(self, submission):
		from InformaCamModels.submission import Submission
		from InformaCamModels.collection import Collection
		
		# unzip
		self.asset_path = submission.asset_path.replace("/submissions/","/collections/")
		try:
			os.makedirs(self.asset_path)
		except OSError as e:
			print e
		
		print submission.emit()
		unzip = ShellThreader([
			"unzip", 
			"%s/%s" % (submission.asset_path, submission.file_name),
			"-d", self.asset_path
		])
		unzip.start()
		unzip.join()
		print unzip.output
		
		'''		
		unzip_output = ['Archive:  /home/ubuntu/assets/submissions/ff4d54bbbceb4ca95106d85e2f38e8e9/0B_D7fbraOf5HeXpDV0VCM0dRQVk.j3mlog', '  inflating: /home/ubuntu/assets/collections/ff4d54bbbceb4ca95106d85e2f38e8e9/log.j3m  ', '  inflating: /home/ubuntu/assets/collections/ff4d54bbbceb4ca95106d85e2f38e8e9/1387543600423_selfie-1943498071.jpg  ', '  inflating: /home/ubuntu/assets/collections/ff4d54bbbceb4ca95106d85e2f38e8e9/informaCaches/fa2f38e4faa783c7049641f600b4d308  ', '  inflating: /home/ubuntu/assets/collections/ff4d54bbbceb4ca95106d85e2f38e8e9/1387543600401_selfie-82254992.jpg  ']
		'''

		assets = []
		
		media = []
		sensor_captures = []
		j3m_verified = False
		
		rx = r'\s*inflating: (.*)'
		for line in unzip.output:
		#for line in unzip_output:
			asset_match = re.findall(rx, line)
			if len(asset_match) == 1:
				assets.append(asset_match[0].strip())
				
		r_j3m = r'.*/log.j3m'
		r_caches = r'.*/informaCaches/.*'
		
		for asset in assets:
			j3m_match = re.match(r_j3m, asset)
			if j3m_match is not None:
				print "J3M: %s" % asset
				j3m_verified = self.validateManifest()
				
			cache_match = re.match(r_caches, asset)
			if cache_match is not None:
				print "ADD CACHE: %s" %  asset
				sensor_captures.append(asset)
			
			else:
				mime_type = getMimeTypeFromFile(asset)
				print mime_type
				if mime_type in [mime_types['image'], mime_types['video']]:
					print "HERE IS A NEW SUB:%s" % asset
					
					f = open(asset, 'rb')
					data = {
						'_id' : hashString(asset),
						'file_name' : os.path.basename(asset),
						'mime_type' : mime_type,
						'package_content' : b64encode(f.read()).rstrip("="),
						'sync_source' : submission.sync_source
					}
					f.close()
					
					if data['file_name'][-4:] != ".%s" % mime_type_map[mime_type]:
						data['file_name'] = "%s.%s" % (
							data['file_name'], mime_type_map[mime_type])
					
					try:
						new_submission = Submission(inflate=data)
						media.append(new_submission._id)
					except exceptions.ConnectionError as e:
						print e
						return
		
		'''
		if len(media) > 0:
			collection = Collection(inflate={
				'_id' : submission._id,
				'submissions' : media,
				'sensor_captures' : sensor_captures
			})
			
			print collection._id
			
		# delete self as submission
		submission.delete()
		'''
		
	def validateManifest(self):
		f = open(os.path.join(self.asset_path, "log.j3m"), 'rb')
		manifest_raw = f.read()
		f.close()
				
		# separate signature from manifest
		signature = os.path.join(self.asset_path, "log.j3m.sig")
		s = open(signature, 'wb+')
		s.write(json.loads(manifest_raw)['signature'])
		s.close()
		
		front_sentinel = "{\"j3m\":"
		back_sentinel = ",\"signature\":"
		manifest = os.path.join(self.asset_path, "log.j3m.manifest")
		m = open(manifest, 'wb+')
		m.write(manifest_raw[len(front_sentinel) : manifest_raw.index(back_sentinel)])
		m.close()
		
		# validate signature
		from InformaCamUtils.funcs import validateSignature
		return validateSignature(
			manifest, signature,
			json.loads(manifest_raw)['j3m']['genealogy']['createdOnDevice'])
	
	def addCache(self, asset):
		f = open(asset, 'rb')
		raw_data = f.read()
		f.close()
		
		print raw_data