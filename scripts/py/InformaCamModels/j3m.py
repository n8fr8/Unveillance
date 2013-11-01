import os, sys, hashlib, json, base64

from asset import Asset
from conf import assets_root

class J3M(Asset):
	def __init__(self, path_to_j3m=None, inflate=None, _id=None):
		invalid = None
		file_name = None
		
		if _id is None:
			if path_to_j3m is not None:
				j = open(path_to_j3m, 'rb')
				data = j.read()
				j.close()
				
				file_paths = path_to_j3m.split("/")
				file_name = file_paths[len(file_paths) - 1]
				
			elif inflate is not None:
				print inflate
				
				from StringIO import StringIO
				import gzip
				
				data = inflate['package_content']				
				file_name = inflate['file_name']
	
				try:
					data = base64.b64decode(data)
				except TypeError:
					data += "=" * ((4 - len(data) % 4) % 4)
					data = base64.b64decode(data)
		
				data = gzip.GzipFile(fileobj=StringIO(data)).read()
				
			try:
				data_ = json.loads(data)
			except ValueError as e:
				print e
				return
			
			try:
				signature = data_['signature']
				del data_['signature']
				
				import gnupg
				from conf import gnupg_home

				d_clone = "%s/tmp/%s.json" % (assets_root, inflate['file_name'])

				data_clone = open(d_clone, 'wb+')
				data_clone.write(json.dumps(data_))
				data_clone.close()
													
				print signature
				gpg = gnupg.GPG(gnupghome=gnupg_home)
				verified = gpg.verify_file(StringIO(signature), d_clone)
				
				if verified.fingerprint is None:
					from conf import invalidate
					invalid = [
						invalidate['codes']['j3m_not_verified'],
						invalidate['reasons']['j3m_not_verified']
					]
					
				os.remove(d_clone)
			except KeyError as e:
				print e
				print "signature already parsed"
				pass
			
			print invalid
			
			try:
				inflate = self.massageData(json.loads(data))
				inflate['_id'] = hashlib.sha1(data).hexdigest()
			except ValueError as e:
				print e
				return
		
		super(J3M, self).__init__(inflate=inflate, _id=_id, river="j3m")
		
		if hasattr(self, 'asset_path'):
			pass
		else:
			if file_name is not None:
				self.file_name = file_name
				super(J3M, self).makeDir("%ssubmissions/%s" % (assets_root, self._id))
				super(J3M, self).addFile(
					file_name, 
					base64.b64encode(
						json.dumps(
							self.emit(
								exclude=[
									"asset_path", 
									"file_name", 
									"date_admitted", 
									"signature"
								]
							)
						)
					)
				)
				
				self.save()
		
		if invalid is not None:
			self.invalidate(invalid[0], invalid[1])
		
	def massageData(self, data):
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
				
		return data