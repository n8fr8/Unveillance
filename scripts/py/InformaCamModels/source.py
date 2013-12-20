import gnupg, json, os, re

from asset import Asset

from vars import invalidate
from conf import gnupg_home, assets_root

from InformaCamUtils.funcs import ShellReader

class Source(Asset):
	def __init__(self, inflate=None, _id=None, reindex=False):
		package_content = None
		if _id is None:
			if inflate is None:
				return
			
			if not reindex:
				package_content = inflate['package_content']
				del inflate['package_content']
				
		super(Source, self).__init__(inflate=inflate, _id=_id, river="sources", extra_fields=['fingerprint', 'baseImage'])
		
		if hasattr(self, 'asset_path'):
			pass
		else:
			if not reindex:
				super(Source, self).makeDir(os.path.join("%ssources" % assets_root, self._id))
			
		if package_content is not None:
			if self.addFile(self.file_name, package_content):
				self.importAssets(self.file_name)
		else:
			if reindex:
				self.importAssets(self.file_name, reindex=True)
				
	
	def importAssets(self, asset_name, reindex=False):
		if not reindex:
			ShellReader([
				"unzip", 
				"%s/%s" % (self.asset_path, asset_name), 
				"-d", 
				self.asset_path
			])
		
		self.importKey(os.path.join(self.asset_path, "publicKey"))
		
		# all the base images
		self.baseImage = []
		for root, dirs, files in os.walk(self.asset_path):
			for file in files:
				is_base_image = re.match(r'^baseImage[_\d{1,2}]*$', str(file))
				if is_base_image:
					self.baseImage.append("%s/%s" % (self.asset_path, str(file)))
		
		c = open(os.path.join(self.asset_path, "credentials") , 'rb')
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
		print path_to_key
		gpg = gnupg.GPG(homedir=gnupg_home)
		
		key = open(path_to_key)
		key_data = key.read()
		key.close()
		
		import_result = gpg.import_keys(key_data)
		
		packet_res = gpg.list_packets(key_data).data.split("\n")
		for line in packet_res:
			if re.match(r'^:signature packet:', line):
				key_id = line[-16:]
				print key_id
				break

		key_result = [key for key in gpg.list_keys() if key['keyid'] == key_id]
		if len(key_result) != 1:
			return False
		else:
			fingerprint = key_result[0]['fingerprint']

		if fingerprint is not None:
			self.fingerprint = fingerprint.lower()
			print self.fingerprint
			self.save()
			
			# get all submissions with this fingerprint
			
			# revalidate their j3ms
			
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