import os, sys, time, re

from base64 import b64encode
from requests import exceptions

from InformaCamModels.source import Source
from InformaCamModels.submission import Submission
from conf import sync, sync_sleep, log_root, j3m, scripts_home

def watch(only_sources=False, only_submissions=False, only_imports=False):
	"""For each subscribed repository, this class sends new media to our Data API.
	
	"""
	clients = []
	mode = None

	if only_submissions:
		mode = "submissions"
	elif only_sources:
		mode = "sources"

	print "running watch... (mode=%s)" % mode
	
	for sync_type in sync:
		if sync_type == "drive":
			if not only_imports:
				from InformaCamData.drive_client import DriveClient	
				clients.append(DriveClient(mode=mode))
		elif sync_type == "globaleaks":
			if not only_imports:
				from InformaCamData.globaleaks_client import GlobaleaksClient
				clients.append(GlobaleaksClient(mode=mode))
		elif sync_type == "import":
			from InformaCamData.import_client import ImportClient
			clients.append(ImportClient(mode=mode))
	
	for client in clients:
		if not client.usable:
			continue
			
		for asset in client.listAssets(omit_absorbed=True):		
			mime_type = client.getAssetMimeType(asset)		
			if not mime_type in client.mime_types.itervalues():
				continue
			
			if mime_type == client.mime_types['zip']:
				if only_submissions:
					continue
				
				data = {
					'_id' : client.getFileNameHash(asset),
					'file_name' : client.getFileName(asset),
					'package_content' : b64encode(client.pullFile(asset)).rstrip("="),
					'sync_source' : sync_type
				}
				print "%s is a source" % data['file_name']
				
				try:
					source = Source(inflate=data)
				except exceptions.ConnectionError as e:
					print e
					sys.exit(0)
					
				if hasattr(source, "invalid"):
					print source.invalid
					continue
				
			else:
				if only_sources:
					continue
				
				data = {
					'_id' : client.getFileNameHash(asset),
					'file_name' : client.getFileName(asset),
					'mime_type' : mime_type,
					'package_content' : b64encode(client.pullFile(asset)).rstrip("="),
					'sync_source' : sync_type
				}
				print "%s is a submission" % data['file_name']
				
				if data['file_name'][-4:] != ".%s" % client.mime_type_map[mime_type]:
					data['file_name'] = "%s.%s" % (
						data['file_name'], 
						client.mime_type_map[mime_type]
					)
				
				try:
					submission = Submission(inflate=data)
				except exceptions.ConnectionError as e:
					print e
					sys.exit(0)
					
				if hasattr(submission, "invalid"):
					print submission.invalid
					continue

			client.absorb(asset)
			client.lockFile(asset)
		client.updateLog()

if __name__ == "__main__":
	#watch(only_sources=True)
	watch(only_submissions=True)
