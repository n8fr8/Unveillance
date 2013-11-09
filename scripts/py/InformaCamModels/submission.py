import os, sys

from asset import Asset
from j3m import J3M
from conf import assets_root, j3m, scripts_home, invalidate

class Submission(Asset):
	def __init__(self, inflate=None, _id=None):
		package_content = None
		if _id is None:
			if inflate is None:
				return
				
			package_content = inflate['package_content']
			del inflate['package_content']
				
		super(Submission, self).__init__(inflate=inflate, _id=_id, river="submissions", extra_omits=['j3m'], extra_fields=['mime_type'])
	
		if hasattr(self, 'asset_path'):
			pass
		else:
			super(Submission, self).makeDir(os.path.join("%ssubmissions" % assets_root, self._id))
		
		if package_content is not None:
			if self.addFile(self.file_name, package_content):
				self.importAssets(self.file_name)
			
	def setMimeType(self, mime_type):
		self.mime_type = mime_type
		self.save()
			
	def importAssets(self, file_name):		
		sys.path.insert(0, os.path.join(scripts_home['python'], "InformaCamUtils"))
		from InformaCamUtils.j3mifier import J3Mifier

		J3Mifier(self)
		return True