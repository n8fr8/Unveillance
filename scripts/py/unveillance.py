import gnupg, sys, subprocess, copy, os, signal
from time import sleep
from multiprocessing import Process

from conf import gnupg_home, elasticsearch_home, secret_key_path, scripts_home, assets_root, sync_sleep, public_user, api
from InformaCamUtils.funcs import ShellThreader
from InformaCamUtils.elasticsearch import Elasticsearch
from intake import watch

files = {
	"daemon" : {
		"log" : "%sdaemon_log.txt" % assets_root,
		"pid" : "%sdaemon_pid.txt" % assets_root
	},
	"api" : {
		"log" : "%sapi_log.txt" % assets_root,
		"pid" : "%sapi_pid.txt" % assets_root,
		"runs_on" : api['port']
	},
	"elasticsearch" : {
		"log" : "%selasticsearch_log.txt" % assets_root,
		"pid" : "%selasticsearch_pid.txt" % assets_root,
		"runs_on" : 9200
	}
}

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
	se = file('/dev/null', 'a+', 0)
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
	
	for file, vals in files.iteritems():
		subprocess.Popen(["touch",vals['pid']])
		subprocess.Popen(["touch",vals['log']])
	
	from conf import globaleaks
	subprocess.Popen(["touch", globaleaks['absorbed_log']])
	
	from conf import j3m
	subprocess.Popen(["chmod", "+x", "%sj3mparser/j3mparser.out" % j3m['root']])

def startElasticsearch():
	daemonize(files['elasticsearch']['log'], files['elasticsearch']['pid'])
	p = subprocess.Popen(['%sbin/elasticsearch' % elasticsearch_home, '-f'])
	
	while True:
		pass

def startAPI():
	daemonize(files['api']['log'], files['api']['pid'])
	p = subprocess.Popen(["python","%sapi.py" % scripts_home['python']])
	
	while True:
		pass

def startIntake():
	daemonize(files['daemon']['log'],files['daemon']['pid'])
	
	while True:
		watch()
		sleep(sync_sleep * 60)

if __name__ == "__main__":
	if len(sys.argv) != 2:
		sys.exit("Unveillance usage: install, run, or stop (-i, -r, or -s)")

	mode = 1
	if sys.argv[1] == "-r" or sys.argv[1] == "run":
		mode = 2
	elif sys.argv[1] == "-s" or sys.argv[1] == "stop":
		mode = 3

	if mode == 1:
		print "Setting up the Unveillance package\n"
	elif mode == 2:
		print "Starting up Unveillance\n"
	elif mode == 3:
		print "Stopping Unveillance\n"
		
		for file, vals in files.iteritems():
			f = open(vals['pid'], 'r')
			current_pid = int(f.read().strip())
			f.close()
			
			print "shutting down %s..." % file
			try:
				proc = ShellThreader(['lsof','-t','-i:%d' % vals['runs_on']])
				proc.start()
				proc.join()
				for pid in proc.output:
					subprocess.Popen(['kill', pid])

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
		
	print "Starting up your database..."
	if mode == 1:
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
	sleep(15)
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
	
	print "Processing new keys..."
	#watch(only_sources=True)
	print "done.\n"
	
	print "Starting intake daemon..."
	p = Process(target=startIntake)
	p.start()
	print "done.\n"
	
	print "Starting web client.."
	p = Process(target=startAPI)
	p.start()
		print "done.\n"
	
	print "Welcome to Unveillance.\n\n"
	