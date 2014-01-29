import os

from asset import Asset
from j3m import J3M

class Collection(Asset):
	def __init__(self, inflate=None, _id=None, reindex=False):
		if _id is None:
			if inflate is None:
				return
			
			inflate = self.massageData(inflate)
		
		super(Collection, self).__init__(inflate=inflate, _id=_id, river="collections", extra_omits=['j3m'])
		
		if hasattr(self, "j3m_id") and self.j3m_id is not None:
			self.j3m = J3M(_id=self.j3m_id)
	
	def massageData(self, inflate):
		try:
			submissions = inflate['attached_media']
			from submission import Submission
			
			contributors = []
			for s in submissions:
				submission = Submission(_id=s)
				print submission.emit()
				
				contributors.append(
					submission.j3m.genealogy['createdOnDevice'])
			
			inflate['contributors'] = list(set(contributors))
			
		except KeyError as e:
			print e
			pass
		
		return inflate