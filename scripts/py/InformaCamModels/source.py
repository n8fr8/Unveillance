from asset import Asset
from conf import gnupg_home, assets_root, invalidate
from InformaCamUtils.funcs import ShellReader

import gnupg, json, os, re

class Source(Asset):
	def __init__(self, inflate=None, _id=None):
		package_content = None
		if _id is None:
			if inflate is None:
				return
				
			package_content = inflate['package_content']
			del inflate['package_content']
				
		super(Source, self).__init__(inflate=inflate, _id=_id, river="sources", extra_fields=['fingerprint', 'baseImage'])
		
		if hasattr(self, "invalid"):
			return
		
		if hasattr(self, 'asset_path'):
			pass
		else:
			super(Source, self).makeDir("%ssources/%s" % (assets_root, self._id))
			
		if package_content is not None:
			if self.addFile(self.file_name, package_content):
				self.importAssets(self.file_name)
				
	
	def importAssets(self, asset_name):

		ShellReader([
			"unzip", 
			"%s/%s" % (self.asset_path, asset_name), 
			"-d", 
			self.asset_path
		])
		self.importKey("%s/publicKey" % self.asset_path)
		
		# all the base images
		self.baseImage = []
		for root, dirs, files in os.walk(self.asset_path):
			for file in files:
				is_base_image = re.match(r'^baseImage[_\d{1,2}]*$', str(file))
				if is_base_image:
					self.baseImage.append("%s/%s" % (self.asset_path, str(file)))
		
		c = open("%s/credentials" % self.asset_path, 'rb')
		credentials = json.loads(c.read())
		c.close()
		
		try:
			self.alias = credentials['alias']
		except:
			pass
			
		try:
			self.email = credentials['email']
		except:
			pass

		self.save()
		return True
	
	def importKey(self, path_to_key):
		gpg = gnupg.GPG(gnupghome=gnupg_home)
		
		key = open(path_to_key)
		import_result = gpg.import_keys(key.read())
		key.close()
				
		fingerprint = import_result.results[0]['fingerprint']

		if fingerprint is not None:
			self.fingerprint = fingerprint.lower()
			self.save()
			return True
		else:
			self.invalidate(
				invalidate['codes']['source_invalid_pgp_key'],
				invalidate['reasons']['source_invalid_pgp_key']
			)
			print "OOPS FINGERPRINT IS NONE"
			return False
	
	def getBaseImage(self):
		return self.baseImage