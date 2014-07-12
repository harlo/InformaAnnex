from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def importKey(task):
	task_tag = "IMPORTING KEY"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "importing gpg key for %s" % task.doc_id
	task.setStatus(412)
	
	import os
	from conf import DEBUG, ANNEX_DIR
	from vars import ASSET_TAGS
	
	source = None
	
	if hasattr(task, "doc_id"):
		from lib.Worker.Models.ic_source import InformaCamSource
	
		source = InformaCamSource(_id=task.doc_id)
		if source is None:
			print "DOC IS NONE"
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			return
	
		try:
			pgp_key = source.getAssetsByTagName(ASSET_TAGS['PGP_KEY'])[0]
		except Exception as e:
			print "NO PGP KEY FOR SOURCE: %s" % e
			pgp_key = os.path.join(ANNEX_DIR, source.base_path, "publicKey")
			print "trying to use %s instead" % pgp_key
			
			if not os.path.exists(pgp_key):
				print "STILL COULD NOT FIND A PGP KEY AT %s" % pgp_key
				print "\n\n************** %s [ERROR] ******************\n" % task_tag
				return
			
	elif hasattr(task, "pgp_file"):
		pgp_key = task.pgp_file

	if pgp_key is None:
		print "NO PGP KEY HERE."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	import gnupg, re
	from conf import getConfig
	gpg = gnupg.GPG(homedir=getConfig('gpg_homedir'))
	
	print "NOW IMPORTING PGP KEY"
	with open(pgp_key, 'rb') as PGP_KEY:	
		import_result = gpg.import_keys(PGP_KEY.read())
		if DEBUG: print import_result.results
	
	try:
		fingerprint = import_result.results[0]['fingerprint']
	except Exception as e:
		print "THIS FINGERPRINT IS FUCKING NULL WHAT DO YOU THINK THIS IS?"
		print e
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	if source is not None:
		from vars import MIME_TYPES

		source.fingerprint = fingerprint
		source.original_mime_type = source.mime_type
		source.mime_type = MIME_TYPES['pgp']	
		source.save()
	
		'''
		from lib.Worker.Models.uv_task import UnveillanceTask
		next_task = UnveillanceTask(inflate={
			'task_path' : "Source.reverify_media.reverifyMedia",
			'queue' : task.queue,
			'doc_id' : source._id
		})
		next_task.run()
		'''
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag