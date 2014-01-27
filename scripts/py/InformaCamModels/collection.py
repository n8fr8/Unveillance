import os

from asset import Asset

class Collection(Asset):
	def __init__(self, inflate=None, _id=None, reindex=False):
		if _id is None:
			if inflate is None:
				return
			
			inflate = self.massageData(inflate)
		
		super(Collection, self).__init__(inflate=inflate, _id=_id, river="collections")
	
	def massageData(self, inflate):
		try:
			submissions = inflate['submissions']
			from submission import Submission
			
			inflate['contributors'] = []
			for s in submissions:
				submission = Submission(_id=s)
				inflate['contributors'].append(
					submission.j3m.genealogy['createdOnDevice'])
				
		except KeyError as e:
			print e
			pass
		
		return inflate