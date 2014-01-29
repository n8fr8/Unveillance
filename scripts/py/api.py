import signal, sys, copy, urllib2, logging, os, json
from base64 import b64encode

import tornado.ioloop
import tornado.web
import tornado.httpserver

from vars import scripts_home, mime_types, public, invalidate, submissions_dump, api as api_prefs, import_directory
from conf import log_root

from InformaCamModels.source import Source as ICSource
from InformaCamModels.submission import Submission as ICSubmission
from InformaCamModels.collection import Collection as ICCollection
from InformaCamUtils.funcs import parseRequest, parseArguments, passesParameterFilter, gzipAsset
from InformaCamUtils.elasticsearch import Elasticsearch

def terminationHandler(signal, frame):
	sys.exit(0)

class Res():
	def __init__(self):
		self.result = 403
	
	def emit(self):
		return self.__dict__

class GenerateICTD(tornado.web.RequestHandler):
	def get(self):
		self.finish(json.dumps(ictd))

class Ping(tornado.web.RequestHandler):
	def get(self):
		res = Res()
		res.result = 200
		self.write(res.emit())

class Collections(tornado.web.RequestHandler):
	def get(self):
		res = Res()
		q = False
		
		clauses = []
		op = None
		
		print urllib2.unquote(self.request.query)
		for k,v in parseRequest(urllib2.unquote(self.request.query)).iteritems():
			if k == "operator":
				op = v
			else:
				clauses.append({
					"field" : k,
					k : v
				})
		
		el = Elasticsearch(river="collections")
		
		if len(clauses) == 1:
			q = el.query({"clauses" : clauses})
		elif len(clauses) == 0:
			q = el.query({
				"clauses": [
					{
						"field" : "get_all",
						"get_all" : False
					}
				]
			})
		else:
			if op is None: op = "and"
			q = el.query({
				"operator" : op,
				"clauses" : clauses
			})

		if q is not False:
			res.data = q
			res.result = 200

		self.finish(res.emit())

class Collection(tornado.web.RequestHandler):
	def initialize(self, _id):
		self._id = _id
		
	def get(self, _id):
		res = Res()
		
		if passesParameterFilter(_id):
			collection = ICCollection(_id=_id)
			
			if not hasattr(collection, "invalid"):
				res.data = collection.emit()
				
				if hasattr(collection, 'j3m'):
					res.data['primary_j3m'] = collection.j3m.emit()
				else:
					print "NO primary j3m?"

				res.result = 200
			else:
				res.reason = collection.invalid
				
		self.finish(res.emit())
		
class Submissions(tornado.web.RequestHandler):
	def get(self):
		res = Res()
		q = False
		
		clauses = []
		op = None
		
		print urllib2.unquote(self.request.query)
		for k,v in parseRequest(urllib2.unquote(self.request.query)).iteritems():
			if k == "operator":
				op = v
			else:
				clauses.append({
					"field" : k,
					k : v
				})
		
		el = Elasticsearch(river="j3m")
		#el = Elasticsearch(river="j3m,submissions")
		
		if len(clauses) == 1:
			q = el.query({"clauses" : clauses})
		elif len(clauses) == 0:
			q = el.query({
				"clauses": [
					{
						"field" : "get_all",
						"get_all" : False
					}
				]
			})
		else:
			if op is None: op = "and"
			q = el.query({
				"operator" : op,
				"clauses" : clauses
			})

		if q is not False:
			res.data = q
			res.result = 200

		self.finish(res.emit())
	
class Submission(tornado.web.RequestHandler):
	def initialize(self, _id):
		self._id = _id
		
	def get(self, _id):
		res = Res()
		
		if passesParameterFilter(_id):
			submission = ICSubmission(_id=_id)
			
			if not hasattr(submission, "invalid"):
				res.data = submission.emit()
				res.result = 200
			else:
				res.reason = submission.invalid
				
		self.finish(res.emit())
		
	def post(self, _id):
		res = Res()
		
		if passesParameterFilter(_id):
			submission = ICSubmission(_id=_id)
			
			if not hasattr(submission, "invalid"):
				for k,v in parseRequest(self.request.body).iteritems():
					if k not in submission.locked_fields:
						setattr(source, k, v)
				
				if submission.save():
					res.data = submission.emit()
					res.result = 200
			
		self.finish(res.emit())
		
class Sources(tornado.web.RequestHandler):
	def get(self):
		res = Res()
		q = False
		
		clauses = []
		op = None
		
		print urllib2.unquote(self.request.query)
		for k,v in parseRequest(urllib2.unquote(self.request.query)).iteritems():
			if k == "operator":
				op = v
			else:
				clauses.append({
					"field" : k,
					k : v
				})
		
		el = Elasticsearch(river="sources")
		
		if len(clauses) == 1:
			q = el.query({"clauses" : clauses})
		elif len(clauses) == 0:
			q = el.query({
				"clauses": [
					{
						"field" : "get_all",
						"get_all" : False
					}
				]
			})
		else:
			if op is None: op = "and"
			q = el.query({
				"operator" : op,
				"clauses" : clauses
			})

		if q is not False:
			res.data = q
			res.result = 200

		self.finish(res.emit())
	
class Source(tornado.web.RequestHandler):
	def initialize(self, _id):
		self._id = _id
		
	def get(self, _id):
		res = Res()
		
		if passesParameterFilter(_id):
			source = ICSource(_id=_id)
			print len(_id)
			
			if not hasattr(source, "invalid"):
				res.data = source.emit()
				res.result = 200
			else:
				res.reason = source.invalid
				
		self.finish(res.emit())
	
	def post(self, _id):
		res = Res()
		
		if passesParameterFilter(_id):
			source = ICSource(_id=_id)
			
			for k,v in parseRequest(self.request.body).iteritems():
				if k not in source.locked_fields:
					setattr(source, k, v)
			
			if source.save():
				res.data = source.emit()
				res.result = 200
			
		self.finish(res.emit())

class MediaHandler(tornado.web.RequestHandler):
	def initialize(self, _id, resolution):
		self._id = _id
		self.resolution = resolution
	
	def get(self, _id, resolution):		
		submission = ICSubmission(_id=_id)
		
		if resolution == "thumb" and submission.mime_type == mime_types['video']:
			as_file_name = "%s.jpg" % submission.file_name[:-4]
		else:
			as_file_name = submission.file_name
		
		path = "%s%s/%s_%s" % (submissions_dump, _id, resolution, as_file_name)
		if resolution == "orig":
			path = "%s%s/%s" % (submissions_dump, _id, as_file_name)
		
		f = open(path, 'rb')
		if resolution != "thumb":
			self.set_header("Content-Type", submission.mime_type)
		else:
			self.set_header("Content-Type", mime_types['image'])
		self.finish(f.read())
		f.close()
		
class J3MHandler(tornado.web.RequestHandler):
	def initialize(self, _id):
		self._id = _id
		
	def get(self, _id):
		submission = ICSubmission(_id=_id)
		try:
			self.finish(submission.j3m.emit())
		except:
			res = Res()
			res.reason = {
				'code' : invalidate['codes']['submission_invalid_j3m'],
				'message' : invalidate['reasons']['submission_invalid_j3m']
			}
			self.finish(res.emit())

class ImportHandler(tornado.web.RequestHandler):
	def post(self):
		logging.info("importing %s to %s" % (
			self.request.files['file'][0]['filename'], 
			import_directory['asset_root']
		))
		
		try:
			f = open(os.path.join(import_directory['asset_root'], self.request.files['file'][0]['filename']), 'wb+')
			f.write(self.request.files['file'][0]['body'])
			f.close()
			self.finish({'ok':True})
			return
		except IOError as e:
			logging.info(e)
			pass
			
		self.finish({'ok':False})

log_file = "%sapi_log.txt" % log_root
log_format = "%(asctime)s %(message)s"

routes = [
	(r"/", Ping),
	(r"/submissions/", Submissions),
	(r"/submission/([a-zA-Z0-9]{32})/", Submission, dict(_id=None)),
	(r"/sources/", Sources),
	(r"/source/([a-zA-Z0-9]{32})/", Source, dict(_id=None)),
	(r"/submission/([a-zA-Z0-9]{32})/media/(low|med|high|thumb|orig)/", MediaHandler, dict(_id=None, resolution=None)),
	(r"/submission/([a-zA-Z0-9]{32})/j3m/", J3MHandler, dict(_id=None)),
	(r"/collections/", Collections),
	(r"/collection/([a-zA-Z0-9]{32})/", Collection, dict(_id=None)),
	(r"/ictd/", GenerateICTD),
	(r"/import/", ImportHandler)
]

api = tornado.web.Application(routes)
signal.signal(signal.SIGINT, terminationHandler)

if __name__ == "__main__":
	logging.basicConfig(filename=log_file, format=log_format, level=logging.INFO)
	logging.info("API Started.")
	
	ictd = copy.deepcopy(public)
	ictd['publicKey'] = b64encode(gzipAsset(public['publicKey']))
	for f, form in enumerate(public['forms']):
		ictd['forms'][f] = b64encode(gzipAsset(form))

	server = tornado.httpserver.HTTPServer(api)
	server.bind(api_prefs['port'])
	server.start(api_prefs['num_processes'])
	
	tornado.ioloop.IOLoop.instance().start()