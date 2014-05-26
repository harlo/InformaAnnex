from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def importKey(task):
	task_tag = "IMPORTING KEY"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.ic_source import InformaCamSource
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	source = InformaCamSource(_id=task.doc_id)
	if source is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	pgp_key = source.getAssetsByTagName(ASSET_TAGS['PGP_KEY'])
	if pgp_key is None:
		print "NO PGP KEY HERE."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	import gnupg, re
	gpg = gnupg.GPG(homedir=getConfig(''))
	
	import_result = gpg.import_keys(pgp_key)
	packet_result = gpg.list_packets(pgp_key).data.split("\n")
	for line in packet_result:
		if re.match(r'^:signature packet:', line):
			key_id = line[-16:]
			if DEBUG: print "FOUND KEY ID: %s" % key_id
			break
	
	key_result = [key for key in gpg.list_keys() if key['keyid'] == key_id]
	if len(key_result) != 1:
		print "NO, COULD NOT FIND A MATCHING KEY"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	fingerprint = key_result[0]['fingerprint']
	if fingerprint is None:
		print "THIS FINGERPRINT IS FUCKING NULL WHAT DO YOU THINK THIS IS?"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	source.fingerprint = fingerprint
	source.save()
	
	from lib.Worker.Models.uv_task import UnveillanceTask
	next_task = UnveillanceTask(inflate={
		'task_path' : "Source.reverify_media.reverifyMedia",
		'queue' : task.queue,
		'doc_id' : source._id
	})
	next_task.run()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag