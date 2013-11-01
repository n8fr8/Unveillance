from fabric.api import *

def init(host, user, key_filename):
	env.hosts = [host]
	env.user = user
	env.key_filename = key_filename
	env.password = ""
	env.port = 22

def listAssets(host=None, user=None, key_filename=None, asset_root=None):
	init(host, user, key_filename)
	
	run("sudo ls %s" % asset_root)
	
def pullFile(host=None, user=None, key_filename=None, asset_root=None, file=None, asset_dump=None, local_dump=None):
	init(host, user, key_filename)
		
	run("sudo cp %s%s ." % (asset_root, file))
	run("sudo chown %(usr)s:%(usr)s %(file)s" % {'usr':user, 'file':file})
	local("scp -i %s %s/%s %s" % (key_filename, asset_dump, file, local_dump))
	run("sudo rm %s" % file)
	
	