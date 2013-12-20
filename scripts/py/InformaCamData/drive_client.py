import httplib2, json, datetime
from time import sleep, strptime, mktime, time

from oauth2client.client import SignedJwtAssertionCredentials
from oauth2client.client import OAuth2WebServerFlow
from apiclient import errors
from apiclient.discovery import build

from informacam_data_client import InformaCamDataClient
from conf import drive, mime_types

scopes = [
	'https://www.googleapis.com/auth/drive',
	'https://www.googleapis.com/auth/drive.file'
]

class DriveClient(InformaCamDataClient):
	def __init__(self, mode=None):
		super(DriveClient, self).__init__(drive['absorbed_log'], mode=mode)
		
		f = file(drive['p12'], 'rb')
		key = f.read()
		f.close
		
		conf = super(DriveClient, self).loadConf(drive['client_secrets'])

		self.credentials = SignedJwtAssertionCredentials(
			conf['web']['client_email'],
			key,
			scopes
		)
		
		http = httplib2.Http()
		self.http = self.credentials.authorize(http)
		self.service = build('drive', 'v2', http = self.http)
		
		self.mime_types['folder'] = "application/vnd.google-apps.folder"
		self.mime_types['file'] = "application/vnd.google-apps.file"
		
		try:
			files = self.service.children().list(folderId=drive['asset_root']).execute()
			self.files_manifest = []
			for f in files['items']:
				self.files_manifest.append(self.getFile(f['id']))

			print "files absorbed: %d" % len(self.files_manifest)

		except errors.httpError as e:
			print e
		
		
	def getAssetMimeType(self, fileId):
		super(DriveClient, self).getAssetMimeType(fileId)
		
		return self.getFile(fileId)['mimeType']
		
	def mapMimeTypeToExtension(self, mime_type):
		super(DriveClient, self).mapMimeTypeToExtension(mime_type)
		
		return self.mime_type_map[mime_type]
		
	def validateMediaObject(self, fileId):
		super(DriveClient, self).validateMediaObject(fileId)
		
		return True
		
	def getFile(self, fileId):
		super(DriveClient, self).getFile(fileId)
		
		try:
			return self.service.files().get(fileId=fileId).execute()
		except errors.HttpError, error:
			return None
			
	def pullFile(self, file):	
		if type(file) is str or type(file) is unicode:
			return self.pullFile(self.getFile(file))
			
		super(DriveClient, self).pullFile(file)
		
		url = file.get('downloadUrl')
		if url:
			response, content = self.service._http.request(url)
			if response.status == 200:
				return content
			else:
				return None
				
	def lockFile(self, file):
		if type(file) is str or type(file) is unicode:
			return self.lockFile(self.getFile(file))
			
		super(DriveClient, self).lockFile(file)
		# transfer ownership to server
		# remove anyone permission
		
		
	def listAssets(self, omit_absorbed=False):
		super(DriveClient, self).listAssets(omit_absorbed)
		
		assets = []
		new_time = 0
		files = None
		
		'''
		get all sharedToMe
		'''
		q = {'q' : 'sharedWithMe'}
		try:
			files = self.service.files().list(**q).execute()
		except errors.HttpError as e:
			print e
			return False
		
		print self.mime_types
		for f in files['items']:
			print f['mimeType']
			if f['mimeType'] in self.mime_types.itervalues() and f['mimeType'] != self.mime_types['folder']:
			
				# if is absorbed already,
				if omit_absorbed and self.isAbsorbed(f['id'], f['mimeType']):
					continue
					
				try:
					clone = self.service.files().copy(
						fileId=f['id'],
						body={'title':f['id']}
					).execute()
					self.files_manifest.append(clone)
					print "copied over %s" % clone['id']
					sleep(2)
				except errors.HttpError as e:
					print e
					continue
				
				try:
					clone = self.service.children().insert(
						folderId=drive['asset_root'], 
						body={'id':clone['id']}
					).execute()
					print "registered %s" % clone['id']
					sleep(2)
				except errors.HttpError as e:
					print e
					continue
					
				try:
					print self.service.files().delete(
						fileId=f['id']
					).execute()
					print "deleted original file over %s" % f['id']
					sleep(2)
				except errors.HttpError as e:
					print e
					continue
				
				assets.append(clone['id'])
		
		self.last_update_for_mode = time() * 1000
		return assets
		
	def isAbsorbed(self, file_name, mime_type):
		# actually, if hash is already a file name
		if self.mode == "sources":
			if mime_type != mime_types['zip']:
				return True
		elif self.mode == "submissions":
			if mime_type == mime_types['zip']:
				return True
		
		for f in self.files_manifest:
			if f['title'] == file_name:
				return True
			
		return False
		
	def absorb(self, file):
		if type(file) is str or type(file) is unicode:
			return self.absorb(self.getFile(file))
		
		super(DriveClient, self).absorb(file)
		
		absorb = {
			'key' : drive['absorbed_flag'],
			'value' : True,
			'visibility' : 'PUBLIC'
		}
		 
		return self.service.properties().insert(fileId=file['id'], body=absorb).execute()
		
	def getFileName(self, file):
		if type(file) is str or type(file) is unicode:
			return self.getFileName(self.getFile(file))
		
		super(DriveClient, self).getFileName(file['title'])
			
		return str(file['title'])
		
	def getFileNameHash(self, file):
		if type(file) is str or type(file) is unicode:
			return self.getFileNameHash(self.getFile(file))
			
		name_base = file['id']	
		return super(DriveClient, self).getFileNameHash(name_base)
	
	def updateLog(self):
		super(DriveClient, self).updateLog(drive['absorbed_log'])