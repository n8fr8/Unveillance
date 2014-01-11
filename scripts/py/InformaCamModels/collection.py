import os

from asset import Asset

class Collection(Asset):
	def __init__(self, inflate=None, _id=None, reindex=False):
		if _id is None:
			if inflate is None:
				return
			
			inflate = self.massageData(inflate)
		
		# submissions, sensor_captures
		super(Collection, self).__init__(inflate=inflate, _id=_id, river="collections")
	
	def massageData(self, inflate):

		
		try:
			sensor_captures = inflate['sensor_captures']
			del inflate['sensor_captures']
			
			for sensor_capture in sensor_captures:
				print sensor_capture
				
					
				# copy over to /data
		except KeyError as e:
			print e
			pass
		
		return inflate