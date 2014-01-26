import gnupg, sys, subprocess, copy, os, signal, fcntl, re, json, hashlib
from time import sleep, time
from multiprocessing import Process
from math import fabs
import xml.etree.ElementTree as ET

from vars import scripts_home, sync_sleep, api, import_directory, elasticsearch_home
from conf import gnupg_home, secret_key_path, log_root,  public_user, assets_root, forms, forms_root, conf_root

from InformaCamUtils.funcs import ShellThreader
from InformaCamUtils.elasticsearch import Elasticsearch
from intake import watch, reindex

files = {
	"daemon" : {
		"log" : "%sdaemon_log.txt" % log_root,
		"pid" : "%sdaemon_pid.txt" % log_root
	},
	"api" : {
		"log" : "%sapi_log.txt" % log_root,
		"pid" : "%sapi_pid.txt" % log_root,
		"runs_on" : api['port']
	},
	"elasticsearch" : {
		"log" : "%selasticsearch_log.txt" % log_root,
		"pid" : "%selasticsearch_pid.txt" % log_root,
		"runs_on" : 9200,
		"status" : "%selasticsearch_status.txt" % log_root
	}
}

time_since_last_fired = 0.0
time_since_last_update = 0.0
intake_status = 0

def daemonize(log_file, pid_file):
	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError, e:
		print e.errno
		sys.exit(1)
		
	os.chdir("/")
	os.setsid()
	os.umask(0)
	
	try:
		pid = os.fork()
		if pid > 0:
			f = open(pid_file, 'w')
			f.write(str(pid))
			f.close()
			
			sys.exit(0)
	except OSError, e:
		print e.errno
		sys.exit(1)
	
	si = file('/dev/null', 'r')
	so = file(log_file, 'a+')
	se = file(log_file, 'a+', 0)
	os.dup2(si.fileno(), sys.stdin.fileno())
	os.dup2(so.fileno(), sys.stdout.fileno())
	os.dup2(se.fileno(), sys.stderr.fileno())
	
def initElasticsearch():
	elasticsearch = Elasticsearch()
	elasticsearch.createIndex(reindex=True)
	
def initFiles():
	subprocess.Popen(["mkdir","%ssources" % assets_root])
	subprocess.Popen(["mkdir","%ssubmissions" % assets_root])		
	subprocess.Popen(["mkdir","%stmp" % assets_root])
	subprocess.Popen(["mkdir","%scollections" % assets_root])
	subprocess.Popen(["touch","%sreindex.txt" % log_root])
	
	for file, vals in files.iteritems():
		subprocess.Popen(["touch",vals['pid']])
		subprocess.Popen(["touch",vals['log']])
		try:
			subprocess.Popen(["touch",vals['status']])
		except KeyError as e:
			pass
	
	subprocess.Popen(["touch", import_directory['absorbed_log']])
	
	from conf import globaleaks
	subprocess.Popen(["touch", globaleaks['absorbed_log']])
	
	import json
	start_gl_from = {
		"sources" : 1381017600,
		"submissions" : 1381017600
	}

	f = open(globaleaks['absorbed_log'], 'w+')
	f.write(json.dumps(start_gl_from))
	f.close()
	
	from conf import drive
	subprocess.Popen(["touch", drive['absorbed_log']])
	
	from vars import j3m
	try:
		with open(os.path.join(j3m['root'], "j3mparser.out")):
			print "(j3m parser already compiled.  skipping make...)"
			pass
	except IOError as e:
		old_dir = os.getcwd()
		os.chdir(os.path.join(j3m['root'],"jpeg-redaction","lib"))
		
		p = subprocess.Popen(["make"])
		p.wait()
	
		p = subprocess.Popen([
			"g++", "-L", os.path.join(j3m['root'], "jpeg-redaction","lib"),
			"-lredact", "jpeg.cpp", "jpeg_decoder.cpp", 
			"jpeg_marker.cpp", "debug_flag.cpp", "byte_swapping.cpp", 
			"iptc.cpp", "tiff_ifd.cpp", "tiff_tag.cpp", 
			"j3mparser.cpp", "-o", "../../j3mparser.out"
		])
		p.wait()
	
		os.chdir(old_dir)

def initForms():
	jr_sentinel = "jr:itext('"
	parse = {"forms" : []}

	for form in forms:
		xmldoc = ET.parse(form)
		root = xmldoc.getroot()
		translation = None
	
		mapping = {
			"mapping" : [],
			"audio_form_data" : []
		}
	
		# actual text mapping for objects is in the head (root[0]) at head.model.itext.translation
		for el in root[0][1]:
			if re.match(r'{.*}itext', el.tag):
				translation = el[0]
	
		# bindings are described in body (root[1]) at body
		for model_item in root[1]:
			map = None
			# if tag is select, select1, or upload
			if re.match(r'{.*}(select|select1)', model_item.tag):
				# get the binding by drilling down
				map = {}
				tag = model_item.attrib['bind']
				bindings = []
				for mi in model_item:
					if re.match(r'{.*}item', mi.tag):
						key = None
						value = None
						for kvp in mi:
							if re.match(r'{.*}label', kvp.tag):
								key = kvp.attrib['ref'][len(jr_sentinel):-2]
							elif re.match(r'{.*}value', kvp.tag):
								value = kvp.text
								for t in translation:
									if key == t.attrib['id']:
										key = t[0].text
										break

						if key is not None and value is not None:
							bindings.append({ value : key })
				map[tag] = bindings
					
			elif re.match(r'{.*}upload', model_item.tag):
				mapping['audio_form_data'].append(model_item.attrib['bind'])
		
			if map is not None:
				mapping['mapping'].append(map)

		if len(mapping['mapping']) == 0:
			del mapping['mapping']
	
		if len(mapping['audio_form_data']) == 0:
			del mapping['audio_form_data']
			
		if len(mapping.keys()) != 0:
			# get the namespace for this form from head (root[0]) head.title
			for el in root[0]:
				if re.match(r'{.*}title', el.tag):
					mapping['namespace'] = el.text
					break
		
			parse['forms'].append(mapping)
			print mapping
	
	print parse
	m = open(os.path.join(forms_root, "forms.json"), 'wb+')
	m.write(json.dumps(parse))
	m.close()

def startElasticsearch():
	daemonize(files['elasticsearch']['log'], files['elasticsearch']['pid'])
	
	p = subprocess.Popen(['%sbin/elasticsearch' % elasticsearch_home, '-f', '-Des.max-open-files=true','-Des.config=%sels_config.yml' % conf_root], stdout=subprocess.PIPE, close_fds=True)
	data = p.stdout.readline()

	while data:
		print data
		if re.match(r'.*started$', data):
			print "STARTED: %s" % data
			f = open(files['elasticsearch']['status'], 'wb+')
			f.write("True")
			f.close()
			sleep(1)
			break
			
		data = p.stdout.readline()
	p.stdout.close()
	
	while True:
		pass

def startAPI():
	daemonize(files['api']['log'], files['api']['pid'])
	p = subprocess.Popen(["python","%sapi.py" % scripts_home['python']])
	
	while True:
		pass

def watchHandler(sigint, frame):
	global time_since_last_fired
	print fabs(time_since_last_fired - time())
	time_since_last_fired = time()

def startIntake():
	daemonize(files['daemon']['log'],files['daemon']['pid'])
	
	signal.signal(signal.SIGIO, watchHandler)
	f = os.open(import_directory['asset_root'], os.O_RDONLY)
	fcntl.fcntl(f, fcntl.F_SETSIG, 0)
	
	global intake_status
	global time_since_last_fired
	global time_since_last_update
	
	while True:
		if intake_status == 0:
			if time_since_last_fired > 0.0 and fabs(time_since_last_fired - time()) >= 1:
				intake_status = 1
				watch(only_imports=True, only_sources=True)
				watch(only_imports=True, only_submissions=True)
				intake_status = 0
				time_since_last_fired = 0.0
			else:
				if fabs(time_since_last_update - time()) >= (sync_sleep * 60):
					intake_status = 1
					watch(only_sources=True)
					watch(only_submissions=True)
					intake_status = 0
					time_since_last_update = time()

		sleep(1)

if __name__ == "__main__":
	if len(sys.argv) != 2:
		sys.exit("Unveillance usage: install, start, stop, or reindex (-i, -r, -s, or -x)")

	mode = -1
	if sys.argv[1] == "-r" or sys.argv[1] == "start":
		mode = 2
	elif sys.argv[1] == "-s" or sys.argv[1] == "stop":
		mode = 3
	elif sys.argv[1] == "-x" or sys.argv[1] == "reindex":
		mode = 4
	elif sys.argv[1] == "-i" or sys.argv[1] == "install":
		mode = 1
	else:
		sys.exit("Unveillance usage: install, start, stop, or reindex (-i, -r, -s, or -x)")

	if mode == 1:
		print "Setting up the Unveillance package\n"
	elif mode == 2:
		print "Starting up Unveillance\n"
	elif mode == 3:
		print "Stopping Unveillance\n"
		
		for file, vals in files.iteritems():
			current_pid = False
			
			try:
				f = open(vals['pid'], 'r')
				
				try:
					current_pid = int(f.read().strip())
				except ValueError as e:
					print "No pid for %s" % file
					continue

				f.close()
			except IOError as e:
				print "no such PID file yet"
				pass
			
			print "shutting down %s..." % file
			try:
				proc = ShellThreader(['lsof','-t','-i:%d' % vals['runs_on']])
				proc.start()
				proc.join()
				for pid in proc.output:
					#print pid
					subprocess.Popen(['kill', pid])

			except KeyError as e:
				pass
				
			try:
				f = open(vals['status'], 'wb+')
				f.write("False")
				f.close()
			except KeyError as e:
				pass
			
			print "done.\n"
					
			if current_pid:
				try:
					os.kill(current_pid, signal.SIGTERM)
				except OSError as e:
					print "\t%s" % e
					print "\tDaemon \"%s\" was already stopped.\n" % file
		
		print "Goodbye!\n\n"
		sys.exit(0)
	elif mode == 4:
		print "Reevaluating forms\n"
		initForms()
		sleep(2)
		
		print "Reindexing Unveillance Data\n"
		reindex()
		sleep(2)		
		
		print "Done.\n"
		sys.exit(0)
		
	print "Starting up your database..."
	if mode == 1:
		try:
			with open("%sbin/elasticsearch" % elasticsearch_home):
				print "(elasticsearch already downloaded.  skipping download...)"
				pass
		except IOError as e:
			el_suffix = "-0.90.6"
			download = "https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch%s.zip" % el_suffix
			package_path = os.path.abspath(os.path.join(elasticsearch_home, os.pardir))
			cmds = [
				["wget", "-O", "%s%s.zip" % (elasticsearch_home[:-1], el_suffix), download],
				["unzip", "-d", package_path, "-o", "%s%s.zip" % (elasticsearch_home[:-1], el_suffix)],
				["mv", "%s%s" %(elasticsearch_home[:-1], el_suffix), elasticsearch_home],
				["rm", "%s%s.zip" % (elasticsearch_home[:-1], el_suffix)]
			]

			for cmd in cmds:
				el_install = ShellThreader(cmd)
				el_install.start()
				el_install.join()
				
	print "please wait..."
	
	p = Process(target=startElasticsearch)
	p.start()
	
	elasticsearch_started = False
	while not elasticsearch_started:
		try:
			f = open(files['elasticsearch']['status'], 'rb')
			if f.read().strip() == "True":
				elasticsearch_started = True
			f.close()
		except IOError as e:
			pass
		
		sleep(5)
		
	print "done.\n"
	
	if mode == 1:
		print "Installing your secret key..."
		gpg = gnupg.GPG(homedir=gnupg_home)	
		sec = open(secret_key_path, 'rb')
		import_key = gpg.import_keys(sec.read())
		sec.close()
		print "done.\n"
	
		print "Initializing databases..."		
		initElasticsearch()
		print "done.\n"
		
		print "Processing files..."
		initFiles()
		sleep(2)
		
		print "Evaluating forms..."
		initForms()
		sleep(2)
		
		print "Getting Keys..."
		watch(only_sources=True)
	
	print "Starting intake daemon..."
	p = Process(target=startIntake)
	p.start()
	print "done.\n"
	
	print "Starting web client.."
	p = Process(target=startAPI)
	p.start()
	print "done.\n"
	
	print "Welcome to Unveillance.\n\n"