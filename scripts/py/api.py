import signal, sys, copy
from base64 import b64encode

import tornado.ioloop
import tornado.web
import tornado.httpserver

from conf import scripts_home, public, invalidate, submissions_dump, api as api_prefs
from InformaCamModels.source import Source as ICSource
from InformaCamModels.submission import Submission as ICSubmission
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
		res = Res()
		res.result = 200
		res.data = ictd
		
		self.write(res.emit())

class Ping(tornado.web.RequestHandler):
	def get(self):
		res = Res()
		res.result = 200
		self.write(res.emit())
		
class Submissions(tornado.web.RequestHandler):
	def get(self):
		res = Res()
		q = False
		el = Elasticsearch(river="submissions")
		
		if(len(self.request.query) > 3):
			clauses = []
			op = None
			
			for k,v in parseRequest(self.request.query).iteritems():
				if k != "operator":
					clauses.append({
						"field" : k,
						k : v
					})
				else:
					op = v
				
			if len(clauses) > 1:
				if op is None: op = "and"
				q = el.query({
					"operator" : op,
					"clauses" : clauses
				})
			else:
				q = el.query({"clauses" : clauses})
		else:
			q = el.query({
				"clauses": [
					{
						"field" : "get_all",
						"type" : "submission"
					}
				]
			})
			
		if q is not False:
			res.data = q
			res.result = 200

		self.write(res.emit())
	
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
				
		self.write(res.emit())
		
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
			
		self.write(res.emit())
		
class Sources(tornado.web.RequestHandler):
	def get(self):
		res = Res()
		q = False
		el = Elasticsearch(river="sources")
		
		if(len(self.request.query) > 3):
			clauses = []
			op = None
			
			for k,v in parseRequest(self.request.query).iteritems():
				if k != "operator":
					clauses.append({
						"field" : k,
						k : v
					})
				else:
					op = v
				
			if len(clauses) > 1:
				if op is None: op = "and"
				q = el.query({
					"operator" : op,
					"clauses" : clauses
				})
			else:
				q = el.query({"clauses" : clauses})
			
		else:
			q = el.query({
				"clauses": [
					{
						"field" : "get_all",
						"type" : "source"
					}
				]
			})
			
		if q is not False:
			res.data = q
			res.result = 200

		self.write(res.emit())
	
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
				
		self.write(res.emit())
	
	def post(self, _id):
		res = Res()
		
		if passesParameterFilter(_id):
			source = ICSource(_id=_id)
			
			if not hasattr(source, "invalid"):
				for k,v in parseRequest(self.request.body).iteritems():
					if k not in source.locked_fields:
						setattr(source, k, v)
				
				if source.save():
					res.data = source.emit()
					res.result = 200
			
		self.write(res.emit())

class MediaHandler(tornado.web.RequestHandler):
	def initialize(self, _id, resolution):
		self._id = _id
		self.resolution = resolution
	
	def get(self, _id, resolution):		
		submission = ICSubmission(_id=_id)
		if hasattr(submission, "invalid"):
			res = Res()
			res.reason = submission.invalid
			self.write(res.emit())
		else:
			path = "%s%s/%s_%s" % (
				submissions_dump, 
				_id, 
				resolution, 
				submission.file_name
			)
			
			f = open(path, 'rb')
			self.write(f.read())
			f.close()
		
class J3MHandler(tornado.web.RequestHandler):
	def initialize(self, _id):
		self._id = _id
		
	def get(self, _id):
		submission = ICSubmission(_id=_id)

		if hasattr(submission, "invalid"):
			res = Res()
			res.reason = submission.invalid
			self.write(res.emit())
		else:
			path = "%s%s/%s" % (
				submissions_dump, 
				_id, 
				"%s.json" % submission.file_name[:-3]
			)
			
			f = open(path, 'rb')
			self.write(f.read())
			f.close()	

routes = [
	(r"/", Ping),
	(r"/submissions/", Submissions),
	(r"/submission/([a-zA-Z0-9]{32})/", Submission, dict(_id=None)),
	(r"/sources/", Sources),
	(r"/source/([a-zA-Z0-9]{32})/", Source, dict(_id=None)),
	(r"/submission/([a-zA-Z0-9]{32})/media/(low|med|high|thumb)/", MediaHandler, dict(_id=None, resolution=None)),
	(r"/submission/([a-zA-Z0-9]{32})/j3m/", J3MHandler, dict(_id=None)),
	(r"/ictd/", GenerateICTD)
]

api = tornado.web.Application(routes)
signal.signal(signal.SIGINT, terminationHandler)

if __name__ == "__main__":
	ictd = copy.deepcopy(public)
	ictd['publicKey'] = b64encode(gzipAsset(public['publicKey']))
	for f, form in enumerate(public['forms']):
		ictd['forms'][f] = b64encode(gzipAsset(form))

	server = tornado.httpserver.HTTPServer(api)
	server.bind(api_prefs['port'])
	server.start(api_prefs['num_processes'])
	
	tornado.ioloop.IOLoop.instance().start()	