import time, base64, copy, sys, os

__metaclass__ = type

emit_omits = ['emit_omits','es', 'locked_fields']
locked_fields = ['asset_path', 'file_name', 'date_admitted', 'sync_source']

class Asset():
	def __init__(self, inflate=None, _id=None, extra_omits=None, extra_fields=None, river=None):
		from vars import invalidate, scripts_home
		from conf import public_user
		from InformaCamUtils.elasticsearch import Elasticsearch

		self.es = Elasticsearch(river=river)
		
		self.emit_omits = copy.deepcopy(emit_omits)
		if extra_omits is not None:
			self.emit_omits.extend(extra_omits)
		
		self.locked_fields = copy.deepcopy(locked_fields)
		if extra_fields is not None:
			self.locked_fields.extend(extra_fields)
				
		if _id is None:
			if inflate is None:
				return

			try:
				self._id = inflate['_id']
				del inflate['_id']
				
				self.date_admitted = time.time() * 1000		#in milliseconds!
				self.inflate(inflate)
				if not self.es.index(self):
					self.invalid = {
						"error_code" : invalidate['codes']['unindexible'],
						"reason" : invalidate['reasons']['unindexible']
					}
					
					from conf import log_root
					f = open("%sreindex.txt" % log_root, "a+")
					f.write("%s\n" % self._id)
					f.close()
					
					print "SHIT:\n %s" % self.invalid
			except KeyError as e:
				print e
				return
			
		else:			
			asset = self.es.get(_id, river)
			if asset is not None:
				self._id = _id
				self.inflate(asset)
			else:
				self.invalid = {
					"error_code": invalidate['codes']['asset_non_existent'],
					"reason" : invalidate['reasons']['asset_non_existent']
				}
					
	def makeDir(self, path):
		from InformaCamUtils.funcs import ShellReader, AsTrueValue
		from conf import public_user

		ShellReader(["mkdir", path])
		
		self.asset_path = path
		self.save()
		
		ShellReader([
			"chown", 
			"-R", 
			"%(usr)s:%(usr)s" % {'usr' : public_user}, 
			self.asset_path
		])
		os.umask(022)
		
	def addFile(self, file_name, content):
		try:
			content = base64.b64decode(content)
		except TypeError:
			content += "=" * ((4 - len(content) % 4) % 4)
			content = base64.b64decode(content)
			
		file = open(os.path.join(self.asset_path, file_name), 'wb+')
		file.write(content)
		file.close()

		return True
		
	def importAssets(self, file_name):
		pass
	
	def save(self):
		return self.es.update(self)
		
	def invalidate(self, error_code, reason):
		self.invalid = {
			"error_code" : error_code,
			"reason" : reason
		}
		self.save()
		
	def delete(self, deleteAssets=False):
		self.es.delete(self)
		
		if deleteAssets and hasattr(self, 'asset_path'):
			from conf import assets_root
			pardir = os.path.abspath(os.path.join(self.asset_path, os.pardir))
			
			if pardir in [
				os.path.join(assets_root, "submissions"), 
				os.path.join(assets_root, "sources"),
				os.path.join(assets_root, "data")]:
				
				print "DELETING %s!" % self._id
				import shutil
				shutil.rmtree(self.asset_path)
		
	def emit(self, exclude=None):
		emit = {}
		for key, value in self.__dict__.iteritems():
			if not key in self.emit_omits:
				if type(value) is unicode:
					emit[key] = str(value)
				else:
					emit[key] = value
		
		if exclude is not None:
			for e in exclude:
				try:
					del emit[e]
				except KeyError as e:
					pass
		
		return emit
		
	def inflate(self, inflate):
		for key, value in inflate.iteritems():
			setattr(self, key, value)
