from conf import main_dir, import_root, log_root, assets_root, conf_root, organization_name, organization_details, organization_fingerprint, repositories, public_key_path, forms

scripts_home = {
	"python" : "%sscripts/py/" % main_dir
}

elasticsearch_home = "%spackages/elasticsearch/" % main_dir

j3m = {
	"root" : "%spackages/j3m/" % main_dir
}

import_directory = {
	"asset_root" : import_root,
	"absorbed_log" : "%sabsorbedByInformaCam_import.txt" % log_root
}

sync_sleep = 2	# minutes
validity_buffer = {
	'location' : (5 * 60 * 1000), # 5 minutes
	'stale_data' : ((((60 * 1000) * 60) * 24) * 30) # 30 days
}

submissions_dump = "%ssubmissions/" % assets_root


api = {
	'port' : 8080,
	'num_processes' : 20
}

invalidate = {
	'codes' : {
		'asset_non_existent': 801,
		'source_invalid_pgp_key' : 902,
		'source_invalid_public_credentials' : 903,
		'source_missing_pgp_key' : 905,
		'submission_invalid_image' : 900,
		'submission_invalid_video' : 901,
		'submission_invalid_j3m' : 904,
		'submission_undefined' : 906,
		'access_denied' : 800,
		'unindexible' : 700,
		'j3m_not_verified' : 907
	},
	'reasons' : {
		'asset_non_existent': "The requested asset does not exist",
		'source_invalid_pgp_key' : "The pgp key is invalid or corrupted",
		'source_missing_pgp_key' : "This source has no PGP key in the keyring",
		'source_invalid_public_credentials' : "One or more of the public credentials files are invalid or corrupted",
		'submission_invalid_image' : "The image is invalid or corrupted",
		'submission_invalid_video' : "The video is invalid or corrupted",
		'submission_invalid_j3m' : "The j3m for this submission is invalid or missing",
		'submission_undefined' : "The derivative has no defined submission",
		'access_denied' : "The user is attempting to access an asset beyond its permissions.",
		'unindexible' : "This asset could not be indexed by elasticsearch",
		'j3m_not_verified' : "This J3M is not verified"
	}
}

public = {
	"organizationName" : organization_name,
	"organizationDetails" : organization_details,
	"organizationFingerprint" : organization_fingerprint,
	"repositories": repositories,
	"publicKey": public_key_path,
	"forms": forms
}

mime_types = {
        'j3m': "text/plain",
        'zip' : "application/zip",
        'image' : "image/jpeg",
        'video' : "video/x-matroska",
        'wildcard' : "application/octet-stream",
        'pgp' : "application/pgp",
        'gzip' : "application/x-gzip",
        '3gp' : 'video/3gpp',
		'j3mlog' : "informacam/log"
}

mime_type_map = {
        'text/plain': "json",
        'application/zip': "zip",
        'image/jpeg': "jpg",
        'video/x-matroska': "mkv",
        'application/octet-stream': 'wildcard',
        'application/pgp' : 'pgp',
        'application/x-gzip' : 'gzip',
        'video/3gpp' : '3gp',
		'informacam/log' : 'j3mlog'
}
