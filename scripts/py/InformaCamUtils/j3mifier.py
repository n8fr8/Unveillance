import os, base64, gzip, magic, json, gnupg, subprocess, re, sys, threading
from multiprocessing import Process

from vars import mime_types, scripts_home, j3m as j3m_root
from conf import gnupg_home, gnupg_pword, main_dir

from funcs import ShellThreader, unGzipAsset
from InformaCamModels.submission import Submission
from InformaCamModels.j3m import J3M

resolutions = [
	{"low_" : [0.5,0.5]},
	{"med_" : [0.75,0.75]}
]

def verifySignature(input, ext_index):
	print "verifying signature"
	gpg = gnupg.GPG(homedir=gnupg_home)
	verified = gpg.verify_file("%s.j3m" % input[:ext_index], sig_file="%s.j3m.sig" % input[:ext_index])

	print "verified fingerprint: %s" % verified.fingerprint
	if verified.fingerprint is None:
		return False

	j = open("%s.j3m" % input[:ext_index], 'rb')
	j3m_data = j.read()
	j.close()

	supplied_fingerprint = str(json.loads(j3m_data)['genealogy']['createdOnDevice'])
	print "supplied fingerprint: %s" % supplied_fingerprint
	if verified.fingerprint.upper() == supplied_fingerprint.upper():
		print "Signature valid for %s" % verified.fingerprint.upper()
		return True

	return False

def compareHash(client_hash, server_hash):	
	if type(client_hash) is unicode:
		client_hash = str(client_hash)
	
	if client_hash == server_hash:
		return True
	
	return False

def verifyVisualContent(input, ext_index, mime_type):
	print "verifying visual content"
	j = open("%s.j3m" % input[:ext_index], 'rb')
	supplied_hashes = json.loads(j.read())['genealogy']['hashes']
	j.close()

	if mime_type == mime_types['image']:
		verify = subprocess.call([
			"java", "-jar",
			"%s/packages/JavaMediaHasher/dist/JavaMediaHasher.jar" % main_dir,
			input
		], stdout = open("%s.md5.txt" % input[:ext_index], 'wb+'))
			
		md5 = open("%s.md5.txt" % input[:ext_index], 'rb')
		verified_hash = md5.read().strip();
	else:
		verify = ShellThreader([
			"ffmpeg", "-y", "-i", input,
			"-vcodec", "copy","-an", "-f", "md5", 
			"%s.md5.txt" % input[:ext_index]
		])
		
		verify.start()
		verify.join()
	
		md5 = open("%s.md5.txt" % input[:ext_index], 'rb')
		verified_hash = md5.read().strip().replace("MD5=", "")
		md5.close()
	
	print "comparing supplied %s hash with %s" % (supplied_hashes, verified_hash)
	
	if type(supplied_hashes) is list:
		print "list of hashes..."
		for hash in supplied_hashes:
			print hash
			if compareHash(hash, verified_hash):
				return True
	else:
		return compareHash(supplied_hashes, verified_hash)
	
	return False

class J3Mifier(threading.Thread):
	def __init__(self, submission, reindex=False):
		threading.Thread.__init__(self)
		
		self.input = os.path.join(submission.asset_path, submission.file_name)
		self.output = submission.asset_path
		self.file_name = submission.file_name
		self.submission = submission
		self.on_reindex = reindex
		
		from funcs import getBespokeFileExtension
		file_name_segments = getBespokeFileExtension(self.input)
		print file_name_segments
		if file_name_segments is not None:
			self.ext_index = -1 * (len(file_name_segments[-1]) + 1)
		else:
			self.ext_index = -4
		
		print "EXT INDEX: %d" % self.ext_index
		
	def run(self):
		print "j3mifying %s" % self.submission.asset_path		
		mime_type = self.submission.mime_type
		ok = False
		if mime_type == mime_types['image']:
			ok = self.getImageMetadata()
		elif mime_type == mime_types['video']:
			ok = self.getVideoMetadata()
		elif mime_type in [mime_types['j3mlog'], mime_types['j3m']]:	
			os.rename(self.input, "%s.txt.b64" % self.input[:self.ext_index])
			#self.input = "%s.txt.b64" % self.input[:self.ext_index]			
			ok = self.getJ3MMetadata()
			return
		
		if ok:
			self.submission.j3m_verified = verifySignature(self.input, self.ext_index)
			self.submission.media_verified = verifyVisualContent(self.input, self.ext_index, mime_type)

		self.submission.save()
		
		self.evaluateCameraFingerprint(self.submission._id)
		self.evaluateUsageFingerprint(self.submission._id)
	
	def getImageMetadata(self):
		"""
			returns the j3m embedded in a .jpg
		"""
		print "getting image metadata"
		# run j3mparser.out to [fname].txt
		j3mparser_cmd = [
			"%sj3mparser.out" % j3m_root['root'],
			self.input
		]
		print j3mparser_cmd
		p = subprocess.Popen(j3mparser_cmd, stdout=file("%s.txt" % self.input[:self.ext_index], "a+"))
		p.wait()

		f = open("%s.txt" % self.input[:self.ext_index], 'rb')
		txt = open("%s.txt.b64" % self.input[:self.ext_index], 'a+')
		tiff = open("%s.tiff.txt" % self.input[:self.ext_index], 'a+')
		
		"""
			because some versions of informacam will include the original exif,
			let's stash this info somewhere else, because it's great data
		"""
		obscura_marker_found = False
		
		for line in f:
			if re.match(r'^file: .*', line):
				continue
			if re.match(r'^Got obscura marker.*', line):
				obscura_marker_found = True
				continue
			if re.match(r'^Generic APPn ffe0 loaded.*', line):
				continue
			if re.match(r'^Component.*', line):
				continue
			if re.match(r'^Didn\'t find .*', line):
				continue
			
			if obscura_marker_found:
				txt.write(line)
			else:
				tiff.write(line)
				
		f.close()
		txt.close()
		tiff.close()

		if self.getJ3MMetadata():
			if not self.on_reindex:
				p = Process(target=self.makeDerivativeImages)
				p.start()
			return True
				
		return False
	
	def getVideoMetadata(self):
		"""
			returns the j3m embedded in an .mkv
		"""
		print "getting video metadata"
		
		# run ffmpeg command to dump result into a file called [fname].txt.b64
		ffmpeg_cmd = [
			"ffmpeg", "-y", "-dump_attachment:t", 
			"%s.txt.b64" % self.input[:self.ext_index], 
			"-i", self.input
		]
		ffmpeg = ShellThreader(ffmpeg_cmd)
		ffmpeg.start()
		ffmpeg.join()

		if self.getJ3MMetadata():
			if not self.on_reindex:
				p = Process(target=self.makeDerivativeVideos)
				p.start()
				
			return True
		
		# json read that file and return object
		return False
	
	def getJ3MMetadata(self):
		"""
			parses the j3m file
		"""
		print "parsing j3m data"
		
		# un b64 [fname].txt.b64 and save as [fname].txt.unb64
		b64 = open("%s.txt.b64" % self.input[:self.ext_index])
		txt = open("%s.txt.unb64" % self.input[:self.ext_index], 'wb+')
		
		content = b64.read()
		try:
			txt.write(base64.b64decode(content))
		except TypeError as e:
			print e
			print "...so trying to decode again (brute-force padding)"
			try:
				content += "=" * ((4 - len(content) % 4) % 4)
				txt.write(base64.b64decode(content))
			except TypeError as e:
				print e
				print "could not unB64 this file (%s.txt.b64)" % self.input[:self.ext_index]
				txt.close()
				b64.close()
				return False
				
		txt.close()
		b64.close()

		m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
		try:
			file_type = m.id_filename("%s.txt.unb64" % self.input[:self.ext_index])
			print "DOC TYPE: %s" % file_type
			m.close()

			# if file is either JSON, PGP or GZIP
			accepted_mime_types = [
				mime_types['pgp'], mime_types['gzip']
			]
			
			if file_type not in accepted_mime_types:
				print "NOT SUPPORTED FILE TYPE"
				return False
			
			if file_type == mime_types['pgp']:
				print "ATTEMPTING TO DECRYPT BLOB"
				pwd = open(gnupg_pword, 'rb')
				passphrase = pwd.read().strip()
				pwd.close()
				print "read pwd"

				gpg_cmd = [
					"gpg", "--no-tty", "--passphrase", passphrase,
					"--output", "%s.j3m.gz" % self.input[:self.ext_index], 
					"--decrypt", "%s.txt.unb64" % self.input[:self.ext_index],
				]
				gpg_thread = ShellThreader(gpg_cmd)
				gpg_thread.start()
				gpg_thread.join()
				print gpg_thread.output

				# check to see if this new output is a gzip
				gpg_check = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
				try:
					file_type = gpg_check.id_filename("%s.j3m.gz" % self.input[:self.ext_index])
					print "NEW DOC TYPE: %s" % file_type
				except:
					print "STILL FAILED TO DECRYPT"
					gpg_check.close()
					return False

				gpg_check.close()
				if file_type not in [mime_types['gzip'], mime_types['zip']]:
					print "NO, this is still wrong."
					return False
				
				if file_type == mime_types['zip']:
					# it is a j3m log!
					print "WE HAVE A J3M LOG!"
					os.rename(
						"%s.j3m.gz" % self.input[:self.ext_index], 
						"%s.j3m.zip" % self.input[:self.ext_index])
					self.submission.file_name = "%s.j3m.zip" % self.submission.file_name[:self.ext_index]
						
					from j3mlogger import J3MLogger
					J3MLogger(self.submission)
					return
				
			elif file_type == mime_types['gzip']:
				# this was already a gzip; skip
				print "THIS WAS ALREADY A GZIP: %s.txt.unb64" % self.input[:self.ext_index]
				os.rename("%s.txt.unb64" % self.input[:self.ext_index], "%s.j3m.gz" % self.input[:self.ext_index])
			

		except:
			m.close()
			return False

		# un gzip [fname].j3m.gz and save as [fname].j3m.orig
		j3m = open("%s.j3m.orig" % self.input[:self.ext_index], 'wb+')
		j3m.write(unGzipAsset("%s.j3m.gz" % self.input[:self.ext_index]))
		j3m.close()

		# if [fname].j3m.orig is text/plain and is json-readable
		m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
		try:
			file_type = m.id_filename("%s.j3m.orig" % self.input[:self.ext_index])
			m.close()
		except:
			m.close()
			return False

		if file_type != mime_types['j3m']:
			return False

		f = open("%s.j3m.orig" % self.input[:self.ext_index], 'rb')
		j3m_data = f.read()
		f.close()
		
		# extract signature as [fname].json.sig
		try:
			j3m_sig = json.loads(j3m_data)['signature']
		except KeyError as e:
			return False
		
		f = open("%s.j3m.sig" % self.input[:self.ext_index], 'wb+')
		f.write(j3m_sig)
		f.close()

		# save to [fname].j3m
		front_sentinel = "{\"j3m\":"
		back_sentinel = ",\"signature\":"

		# this must be the LAST INSTANCE OF signature, btw.
		print "FINDING BACK SENTINEL at position %d" % j3m_data.rindex(back_sentinel)
		extracted_j3m = j3m_data[len(front_sentinel) : j3m_data.rindex(back_sentinel)]

		f = open("%s.j3m" % self.input[:self.ext_index], 'wb+')
		f.write(extracted_j3m)
		f.close()

		j3m_asset = J3M(path_to_j3m="%s.j3m" % self.input[:self.ext_index])
		self.submission.j3m_id = j3m_asset._id
		self.submission.save()
		return True
	
	def makeDerivativeImages(self):
		print "making derivative images"

		hires_cmd = [
			"ffmpeg", "-y", "-i", self.input,
			os.path.join(self.output, "high_%s" % self.file_name)
		]
		hires = ShellThreader(hires_cmd)
		hires.start()
		hires.join()

		resolutions.append({'thumb_' : [0.15, 0.15]})
		for resolution in resolutions:
			label = resolution.keys()[0]

			ffmpeg_cmd = [
				"ffmpeg", "-y", "-i", self.input,
				"-vf", "scale=iw*%.3f:ih*%.3f" % (resolution[label][0], resolution[label][1]),
				os.path.join(self.output, "%s%s" % (label, self.file_name))
			]

			print ffmpeg_cmd
			ffmpeg = ShellThreader(ffmpeg_cmd)
			ffmpeg.start()
			ffmpeg.join()
	
	def makeDerivativeVideos(self):
		print "making derivative videos"

		ffmpeg_cmd = [
			"ffmpeg", "-y", "-i", self.input,
			"-vcodec", "copy", "-acodec", "copy",
			"%s.mp4" % self.input[:self.ext_index]
		]
		ffmpeg = ShellThreader(ffmpeg_cmd)
		ffmpeg.start()
		ffmpeg.join()

		hires_cmd = [
			"cp", "%s.mp4" % self.input[:self.ext_index],
			os.path.join(self.output, "high_%s.mp4" % self.file_name[:self.ext_index])
		]
		hires = ShellThreader(hires_cmd)
		hires.start()
		hires.join()
		print hires_cmd

		ogv_cmd = [
			"ffmpeg2theora", "%s.mp4" % os.path.join(self.output, "high_%s" % self.file_name[:self.ext_index])
		]
		print ogv_cmd
		ogv = ShellThreader(ogv_cmd)
		ogv.start()
		ogv.join()

		for resolution in resolutions:
			label = resolution.keys()[0]

			ffmpeg_cmd = [
				"ffmpeg", "-y", "-i", "%s.mp4" % self.input[:self.ext_index],
				"-filter:v", "scale=%d:%d" % (resolution[label][0], resolution[label][1]),
				"-acodec", "copy", "%s.mp4" % os.path.join(self.output, "%s%s" % (label, self.file_name))[:self.ext_index]
			]
			ffmpeg = ShellThreader(ffmpeg_cmd)
			ffmpeg.start()
			ffmpeg.join()

			ogv_cmd = [
				"ffmpeg2theora", "%s.mp4" % os.path.join(self.output, "%s%s" % (label, self.file_name))[:self.ext_index]
			]
			ogv = ShellThreader(ogv_cmd)
			ogv.start()
			ogv.join()


		ffmpeg_cmd = [
			"ffmpeg", "-y", "-i", "%s.mp4" % self.input[:self.ext_index],
			"-f", "image2", "-ss", "0.342", "-vframes", "1",
			os.path.join(self.output, "thumb_%s.jpg" % self.file_name[:self.ext_index])
		]
		ffmpeg = ShellThreader(ffmpeg_cmd)
		ffmpeg.start()
		ffmpeg.join()
	
	def evaluateCameraFingerprint(self, submission_id):
		print "verifying camera fingerprint"
	
	def evaluateUsageFingerprint(self, submission_id):
		print "verifying usage fingerprint"
