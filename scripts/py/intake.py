import os, sys, time, re

from daemon import runner
from base64 import b64encode

from InformaCamModels.source import Source
from InformaCamModels.submission import Submission
from conf import sync, sync_sleep, assets_root, j3m, scripts_home

def watch(only_sources=False):
	"""For each subscribed repository, this class sends new media to our Data API.
	
	"""
	print "running watch..."
	clients = []
	for sync_type in sync:
		if sync_type == "drive":
			from InformaCamData.drive_client import DriveClient	
			clients.append(DriveClient())
		elif sync_type == "globaleaks":
			from InformaCamData.globaleaks_client import GlobaleaksClient
			clients.append(GlobaleaksClient())
	
	for client in clients:
		for asset in client.listAssets(omit_absorbed=True):		
			mime_type = client.getAssetMimeType(asset)		
			if not mime_type in client.mime_types.itervalues():
				continue
			
			data = {
				'_id' : client.getFileNameHash(asset),
				'file_name' : client.getFileName(asset),
				'mime_type' : mime_type,
				'package_content' : b64encode(client.pullFile(asset)).rstrip("=")
			}
			
			if mime_type == client.mime_types['zip']:
				del data['mime_type']
				print "it is a source"
				
				source = Source(inflate=data)
				if hasattr(source, "invalid"):
					print source.invalid
					continue
				
			elif mime_type == client.mime_types['j3m']:
				if only_sources:
					continue
					
				del data['mime_type']
				print "it is a j3m"
								
				j3m = J3M(inflate=data)
				if hasattr(j3m, "invalid"):
					print source.invalid
					continue
				
			else:
				if only_sources:
					continue

				if data['file_name'][-4:] != ".%s" % client.mime_type_map[mime_type]:
					data['file_name'] = "%s.%s" % (
						data['file_name'], 
						client.mime_type_map[mime_type]
					)
				print "it is a sub: %s" % data['file_name']
				
				submission = Submission(inflate=data)
				if hasattr(submission, "invalid"):
					print submission.invalid
					continue

			client.absorb(asset)
			client.lockFile(asset)