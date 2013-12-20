import os, sys, hashlib, json, base64

from asset import Asset

from vars import mime_types
from conf import assets_root, forms_root

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

			inflate = self.massageData(data, path_to_j3m)
			inflate['_id'] = self.generateId(data)
			if inflate['_id'] is None:
				return
		
		super(J3M, self).__init__(inflate=inflate, _id=_id, river="j3m")

		if path_to_j3m is not None:
			self.asset_path = os.path.dirname(os.path.realpath(path_to_j3m))
			self.file_name = os.path.basename(path_to_j3m)
			self.save()
			print self._id

	def generateId(self, data):
		try:
			return hashlib.md5(json.dumps(data)).hexdigest()
		except:
			print "ERROR MAKING ID HASH"

		return None
		
	def massageData(self, data, path_to_j3m):
		from base64 import b64decode
		import magic
		from InformaCamUtils.funcs import unGzipAsset, ShellThreader
		
		base = path_to_j3m[:-4]		
		
		try:
			data['public_hash'] = hashlib.sha1(
				"".join([
					data['genealogy']['createdOnDevice'],
					"".join(data['genealogy']['hashes'])
				])
			).hexdigest()
			
		except KeyError as e:
			print e
			pass
			
		try:
			loc = data['data']['exif']['location']
			data['data']['exif']['location'] = [loc[1], loc[0]]
		except KeyError as e:
			print e
			pass
		
		try:
			if type(data['data']['sensorCapture']) is list:
				pass
		except KeyError as e:
			return data
		
		for playback in data['data']['sensorCapture']:
			try:
				gps = str(playback['sensorPlayback']['gps_coords'])[1:-1].split(",")
				#print "sensorPlayback.gps_coords %s" % gps 
				playback['sensorPlayback']['gps_coords'] = [
					float(gps[1]),
					float(gps[0])
				]
			except KeyError as e:
				pass
			
			try:
				gps = str(playback['sensorPlayback']['regionLocationData']['gps_coords'])[1:-1].split(",")
				#print "sensorPlayback.regionLocationData.gps_coords %s" % gps 
				playback['sensorPlayback']['regionLocationData']['gps_coords'] = [
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
			f = open(os.path.join(forms_root, "forms.json"), 'rb')
			form_manifest = json.loads(f.read())
			f.close()
		
			try:
				for udata in data['data']['userAppendedData']:
					for aForms in udata['associatedForms']:
						for f in form_manifest['forms']:
							if f['namespace'] == aForms['namespace']:
								try:
									for mapping in f['mapping']:
										try:
											group = mapping.keys()[0]
											key = aForms['answerData'][group].split(" ")
							
											for m in mapping[group]:
												if m.keys()[0] in key:
													key[key.index(m.keys()[0])] = m[m.keys()[0]]
											aForms['answerData'][group] = " ".join(key)
										except KeyError as e:
											print e
											pass
								except KeyError as e:
									pass
						
								try:
									idx = 0
									for audio in f['audio_form_data']:
										try:
											audio_data = aForms['answerData'][audio]
											audio_base = "%s_audio_%d" % (base, idx)
											idx += 1

											zip = open("%s.3gp.gzip" % audio_base, 'wb+')
											unb64 = None
											try:
												unb64 = b64decode(audio_data)
											except TypeError as e:
												try:
													audio_data += "="  * ((4 - len(v) % 4) % 4)
													unb64 = b64decode(audio_data)
												except TypeError as e:
													print e
						
											if unb64 is None:
												zip.close()
												continue
							
											zip.write(unb64)
											zip.close()
						
											m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
											try:
												file_type = m.id_filename("%s.3gp.gzip" % audio_base)
												print "FILE TYPE: %s" % file_type
												m.close()
							
												if file_type != mime_types['gzip']:
													continue
											except:
												m.close()
												continue
						
											_3gp = open("%s.3gp" % audio_base, 'wb+')
											_3gp.write(unGzipAsset("%s.3gp.gzip" % audio_base))
											_3gp.close()
						
											m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
											try:
												file_type = m.id_filename("%s.3gp" % audio_base)
												print "AUDIO TYPE: %s" % file_type
												m.close()
							
												if file_type != mime_types['3gp']:
													continue
							
											except:
												m.close()
												continue
						
											ffmpeg = ShellThreader([
												"ffmpeg", "-y", "-i", "%s.3gp" % audio_base, 
												"-vn", "-acodec", "mp2", "-ar", "22050", 
												"-f", "wav", "%s.wav" % audio_base
											])
											ffmpeg.start()
											ffmpeg.join()
						
											aForms['answerData'][audio] = "%s.wav" % audio_base
										except KeyError as e:
											print e
											pass
								except KeyError as e:
									pass
			except KeyError as e:
				print e
				pass
		except IOError as e:
			print e
			pass
			
		return data