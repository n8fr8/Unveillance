import os, sys, hashlib, json, base64

from asset import Asset
from conf import log_root, audio_form-data

class J3M(Asset):
	def __init__(self, path_to_j3m=None, _id=None, inflate=None):		
		if _id is None and path_to_j3m is not None:
			j = open(path_to_j3m, 'rb')
			try:
				data = json.loads(j.read())
				j.close()
			except KeyError as e:
				print e
				j.close()
				return

			inflate = self.massageData(data)
			inflate['_id'] = self.generateId(data)
			if inflate['_id'] is None:
				return
		
		super(J3M, self).__init__(inflate=inflate, _id=_id, river="j3m")

		if path_to_j3m is not None:
			self.asset_path = os.path.dirname(os.path.realpath(path_to_j3m))
			self.file_name = os.path.basename(path_to_j3m)
			self.save()
			print self._id
		else:
			print "no path to j3m?"

	def generateId(self, data):
		try:
			return hashlib.md5(json.dumps(data)).hexdigest()
		except:
			print "ERROR MAKING ID HASH"

		return None
		
	def massageData(self, data):
		try:
			data['public_hash'] = hashlib.sha1(
				"".join([
					data['genealogy']['createdOnDevice'],
					"".join(data['genealogy']['hashes'])
				])
			).hexdigest()
			
		except KeyError as e:
			pass
			
		try:
			loc = data['data']['exif']['location']
			data['data']['exif']['location'] = [loc[1], loc[0]]
		except KeyError as e:
			pass
		
		try:
			if type(data['data']['sensorCapture']) is list:
				pass
		except KeyError as e:
			return data
		
		for playback in data['data']['sensorCapture']:
			try:
				gps = str(playback['sensorPlayback']['gps_coords'])[1:-1].split(",")
				playback['sensorPlayback']['gps_coords'] = [
					float(gps[1]),
					float(gps[0])
				]
			except KeyError as e:
				pass
				
			try:
				for (i,b) in enumerate(playback['sensorPlayback']['visibleWifiNetworks']):
					playback['sensorPlayback']['visibleWifiNetworks'][i]['bt_hash'] = hashlib.sha1(b['bssid']).hexdigest()
			except KeyError as e:
				pass
		
		try:
			for (i, a) in enumerate(data['data']['userAppendedData']):
				for f in a['associatedForms']:
					for k, v in f['answerData']:
						if k in audio_form_data:
							# un b64
							# ungzip into audio file
							# append proper extension for mime type
							print "AUDIO FORM!"
		except KeyError as e:
			print e
			pass
				
		return data
