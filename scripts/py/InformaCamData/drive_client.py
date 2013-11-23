import httplib2, json, datetime
from time import sleep, strptime, mktime

from oauth2client.client import SignedJwtAssertionCredentials
from oauth2client.client import OAuth2WebServerFlow
from apiclient import errors
from apiclient.discovery import build

from informacam_data_client import InformaCamDataClient
from conf import drive

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
		
		'''
		get all sharedToMe
		'''
		q = {'q' : 'sharedWithMe'}
		files = self.service.files().list(**q).execute()
		for f in files['items']:
			if f['mimeType'] in self.mime_types.itervalues() and f['mimeType'] != self.mime_types['folder']:
					
				try:
					clone = self.service.files().copy(
						fileId=f['id'],
						body={'title':f['title']}
					).execute()
					sleep(2)
				except errors.HttpError as e:
					print e
					continue
				
				try:
					clone = self.service.children().insert(
						folderId=drive['asset_root'], 
						body={'id':clone['id']}
					).execute()
					sleep(2)
				except errors.HttpError as e:
					print e
					continue
					
				try:
					print self.service.files().delete(
						fileId=f['id']
					).execute()
					sleep(2)
				except errors.HttpError as e:
					print e
					continue

		files = self.service.children().list(folderId=drive['asset_root']).execute()
		for f in files['items']:
			f = self.getFile(f['id'])
			# google is 5 hours ahead of Eastern btw
			time_delta = datetime.timedelta(hours=-5)
			
			date_str = " ".join(f['createdDate'].split("T")).split(".")[0]
			created_date = datetime.datetime(*strptime(date_str, "%Y-%m-%d %H:%M:%S")[:6])
			created_date = created_date + time_delta
			
			new_time = mktime(created_date.timetuple())
			if new_time > self.last_update_for_mode:
				self.last_update_for_mode = new_time
			
			if omit_absorbed and self.isAbsorbed(new_time):
				continue
				
			assets.append(f['id'])
		
		return assets
		
	def isAbsorbed(self, date_created):
		if date_created <= self.absorbedByInformaCam[self.mode]:
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