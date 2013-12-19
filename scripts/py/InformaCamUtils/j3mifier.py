import os, base64, gzip, magic, json, gnupg, subprocess, re, sys, threading
from multiprocessing import Process

from conf import gnupg_home, mime_types, scripts_home, main_dir, j3m as j3m_root
from conf import gnupg_pword, scripts_home
from funcs import ShellThreader, unGzipAsset
from InformaCamModels.submission import Submission
from InformaCamModels.j3m import J3M

resolutions = [
	{"low_" : [0.5,0.5]},
	{"med_" : [0.75,0.75]}
]

def verifySignature(input):
	print "verifying signature"
	gpg = gnupg.GPG(homedir=gnupg_home)
	verified = gpg.verify_file("%s.j3m" % input[:-4], sig_file="%s.j3m.sig" % input[:-4])

	print "verified fingerprint: %s" % verified.fingerprint
	if verified.fingerprint is None:
		return False

	j = open("%s.j3m" % input[:-4], 'rb')
	j3m_data = j.read()
	j.close()

	supplied_fingerprint = str(json.loads(j3m_data)['genealogy']['createdOnDevice'])
	print "supplied fingerprint: %s" % supplied_fingerprint
	if verified.fingerprint.upper() == supplied_fingerprint.upper():
		print "Signature valid for %s" % verified.fingerprint.upper()
		return True

	return False

def compareHash(client_hash, server_hash):
	if len(client_hash) != 32:
		return False
	
	if client_hash == server_hash:
		return True
	
	return False

def verifyVisualContent(input, mime_type):
	print "verifying visual content"
	j = open("%s.j3m" % input[:-4], 'rb')
	supplied_hashes = json.loads(j.read())['genealogy']['hashes']
	j.close()

	if mime_type == mime_types['image']:
		verify = subprocess.call([
			"java", "-jar",
			"%s/packages/JavaMediaHasher/dist/JavaMediaHasher.jar" % main_dir,
			input
		], stdout = open("%s.md5.txt" % input[:-4], 'a+'))
			
		md5 = open("%s.md5.txt" % input[:-4], 'rb')
		verified_hash = md5.read();
	else:
		verify = ShellThreader([
			"ffmpeg", "-y", "-i", input,
			"-acodec", "copy", "-f", "md5", 
			"%s.md5.txt" % input[:-4]
		])
		
		verify.start()
		verify.join()
	
		md5 = open("%s.md5.txt" % input[:-4], 'rb')
		verified_hash = md5.read().replace("MD5=", "")
		md5.close()
	
	print "comparing supplied %s hash with %s" % (supplied_hashes, verified_hash)
	
	if type(supplied_hashes) is list:
		for hash in supplied_hashes:
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
		
	def run(self):
		print "j3mifying %s" % self.submission.asset_path		
		mime_type = self.submission.mime_type
		ok = False
		if mime_type == mime_types['image']:
			ok = self.getImageMetadata()
		elif mime_type == mime_types['video']:
			ok = self.getVideoMetadata()
		elif mime_type == mime_types['j3m']:
			os.rename(self.input, "%s.txt.b64" % self.input[:-4])
			self.input = "%s.txt.b64" % self.input[:-4]
			ok = self.getJ3MMetadata()
		
		if ok:
			self.submission.j3m_verified = verifySignature(self.input)
			self.submission.media_verified = verifyVisualContent(self.input, mime_type)

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
		p = subprocess.Popen(j3mparser_cmd, stdout=file("%s.txt" % self.input[:-4], "a+"))
		p.wait()

		f = open("%s.txt" % self.input[:-4], 'rb')
		txt = open("%s.txt.b64" % self.input[:-4], 'a+')
		tiff = open("%s.tiff.txt" % self.input[:-4], 'a+')
		
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
			"%s.txt.b64" % self.input[:-4], 
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
		b64 = open("%s.txt.b64" % self.input[:-4])
		txt = open("%s.txt.unb64" % self.input[:-4], 'wb+')
		
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
				print "could not unB64 this file (%s.txt.b64)" % self.input[:-4]
				txt.close()
				b64.close()
				return False
				
		txt.close()
		b64.close()

		m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
		try:
			file_type = m.id_filename("%s.txt.unb64" % self.input[:-4])
			print "DOC TYPE: %s" % file_type
			m.close()

			# if file is either PGP or GZIP
			if file_type != mime_types['pgp'] and file_type != mime_types['gzip']:
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
					"--output", "%s.j3m.gz" % self.input[:-4], 
					"--decrypt", "%s.txt.unb64" % self.input[:-4],
				]
				gpg_thread = ShellThreader(gpg_cmd)
				gpg_thread.start()
				gpg_thread.join()
				print gpg_thread.output

				# check to see if this new output is a gzip
				gpg_check = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
				try:
					file_type = gpg_check.id_filename("%s.j3m.gz" % self.input[:-4])
					print "NEW DOC TYPE: %s" % file_type
				except:
					print "STILL FAILED TO DECRYPT"
					gpg_check.close()
					return False

				gpg_check.close()
				if file_type != mime_types['gzip']:
					return False
			elif file_type == mime_types['gzip']:
				# this was already a gzip; skip
				print "THIS WAS ALREADY A GZIP: %s.txt.unb64" % self.input[:-4]
				os.rename("%s.txt.unb64" % self.input[:-4], "%s.j3m.gz" % self.input[:-4])
			

		except:
			m.close()
			return False

		# un gzip [fname].j3m.gz and save as [fname].j3m.orig
		j3m = open("%s.j3m.orig" % self.input[:-4], 'wb+')
		j3m.write(unGzipAsset("%s.j3m.gz" % self.input[:-4]))
		j3m.close()

		# if [fname].j3m.orig is text/plain and is json-readable
		m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
		try:
			file_type = m.id_filename("%s.j3m.orig" % self.input[:-4])
			m.close()
		except:
			m.close()
			return False

		if file_type != mime_types['j3m']:
			return False

		f = open("%s.j3m.orig" % self.input[:-4], 'rb')
		j3m_data = f.read()
		f.close()
		
		# extract signature as [fname].json.sig
		try:
			j3m_sig = json.loads(j3m_data)['signature']
		except KeyError as e:
			return False
		
		f = open("%s.j3m.sig" % self.input[:-4], 'wb+')
		f.write(j3m_sig)
		f.close()

		# save to [fname].j3m
		front_sentinel = "{\"j3m\":"
		back_sentinel = ",\"signature\":"
		extracted_j3m = j3m_data[len(front_sentinel) : j3m_data.index(back_sentinel)]


		f = open("%s.j3m" % self.input[:-4], 'wb+')
		f.write(extracted_j3m)
		f.close()

		j3m_asset = J3M(path_to_j3m="%s.j3m" % self.input[:-4])
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
			"%s.mp4" % self.input[:-4]
		]
		ffmpeg = ShellThreader(ffmpeg_cmd)
		ffmpeg.start()
		ffmpeg.join()

		hires_cmd = [
			"cp", "%s.mp4" % self.input[:-4],
			os.path.join(self.output, "high_%s.mp4" % self.file_name[:-4])
		]
		hires = ShellThreader(hires_cmd)
		hires.start()
		hires.join()
		print hires_cmd

		ogv_cmd = [
			"ffmpeg2theora", "%s.mp4" % os.path.join(self.output, "high_%s" % self.file_name[:-4])
		]
		print ogv_cmd
		ogv = ShellThreader(ogv_cmd)
		ogv.start()
		ogv.join()

		for resolution in resolutions:
			label = resolution.keys()[0]

			ffmpeg_cmd = [
				"ffmpeg", "-y", "-i", "%s.mp4" % self.input[:-4],
				"-filter:v", "scale=%d:%d" % (resolution[label][0], resolution[label][1]),
				"-acodec", "copy", "%s.mp4" % os.path.join(self.output, "%s%s" % (label, self.file_name))[:-4]
			]
			ffmpeg = ShellThreader(ffmpeg_cmd)
			ffmpeg.start()
			ffmpeg.join()

			ogv_cmd = [
				"ffmpeg2theora", "%s.mp4" % os.path.join(self.output, "%s%s" % (label, self.file_name))[:-4]
			]
			ogv = ShellThreader(ogv_cmd)
			ogv.start()
			ogv.join()


		ffmpeg_cmd = [
			"ffmpeg", "-y", "-i", "%s.mp4" % self.input[:-4],
			"-f", "image2", "-ss", "0.342", "-vframes", "1",
			os.path.join(self.output, "thumb_%s.jpg" % self.file_name[:-4])
		]
		ffmpeg = ShellThreader(ffmpeg_cmd)
		ffmpeg.start()
		ffmpeg.join()
	
	def evaluateCameraFingerprint(self, submission_id):
		print "verifying camera fingerprint"
	
	def evaluateUsageFingerprint(self, submission_id):
		print "verifying usage fingerprint"
