from asset import Asset
from j3m import J3M
from conf import assets_root, j3m, scripts_home, invalidate
import os, sys

class Submission(Asset):
	def __init__(self, inflate=None, _id=None):
		package_content = None
		if _id is None:
			if inflate is None:
				return
				
			package_content = inflate['package_content']
			del inflate['package_content']
				
		super(Submission, self).__init__(inflate=inflate, _id=_id, river="submissions", extra_omits=['j3m'], extra_fields=['j3m_id','mime_type'])
		
		if hasattr(self, "invalid"):
			return
		
		if hasattr(self, 'asset_path'):
			pass
		else:
			super(Submission, self).makeDir(os.path.join("%ssubmissions" % assets_root, self._id))
		
		if package_content is not None:
			if self.addFile(self.file_name, package_content) and self.importAssets(self.file_name):
				self.j3m = J3M(_id=self.j3m_id)
				print self.j3m.emit()
				self.save()
			
	def setMimeType(self, mime_type):
		self.mime_type = mime_type
		self.save()
			
	def importAssets(self, file_name):		
		# should fork here?
		sys.path.insert(0, os.path.join(scripts_home['python'], "InformaCamUtils"))
		from funcs import ShellThreader
	
		j3m_thread = ShellThreader([
			"java", "-cp", j3m['classpath'],
			"framework.MediaProcessor", "%s/%s" % (self.asset_path, self.file_name),
			"%s/" % self.asset_path, "-d"
		], op_dir=j3m['root'])
		j3m_thread.start()
		j3m_thread.join()
		
		
		j3m_ = J3M(path_to_j3m=os.path.join(self.asset_path, "%sjson" % self.file_name[:-3]))
		try:
			self.j3m_id = j3m_._id
			self.save()
				
			return True
		except AttributeError as e:
			self.invalidate(
				invalidate['codes']['submission_invalid_j3m'],
				invalidate['reasons']['submission_invalid_j3m']
			)
			return False