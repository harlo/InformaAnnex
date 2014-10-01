from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def verifySignature(task):
	task_tag = "VERIFYING SIGNATURE"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	sig = media.getAsset("j3m.sig", return_only="path")
	j3m = media.getAsset("j3m.json", return_only="path")
	
	if DEBUG: print "j3m path: %s, sig path: %s" % (j3m, sig)
	
	if sig is None or j3m is None:
		print "NO SIGNATURE or J3M"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	import gnupg
	from conf import getConfig
	
	try:
		gpg = gnupg.GPG(homedir=getConfig('gpg_homedir'))
	except Exception as e:
		print "ERROR INITING GPG"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	media.j3m_verified = False
	verified = gpg.verify_file(j3m, sig_file=sig)
	if DEBUG: print "verified fingerprint: %s" % verified.fingerprint
	
	if verified.fingerprint is not None:
		from json import loads
		
		supplied_fingerprint = str(loads(
			media.loadAsset("j3m.json"))['genealogy']['createdOnDevice'])
		
		if verified.fingerprint.upper() == supplied_fingerprint.upper():
			if DEBUG: print "SIGNATURE VALID for %s" % verified.fingerprint.upper()
			media.j3m_verified = True
	
	media.save()
	media.addCompletedTask(task.task_path)
	
	task_path = None
	
	if not hasattr(media, "j3m_id"):
		task_path = "J3M.massage_j3m.massageJ3M"
	else:
		task_path = "J3M.verify_visual_content.verifyVisualContent"
	
	if task_path is not None:
		from lib.Worker.Models.uv_task import UnveillanceTask
		new_task = UnveillanceTask(inflate={
			'task_path' : "J3M.massage_j3m.massageJ3M",
			'doc_id' : media._id,
			'queue' : task.queue})
		new_task.run()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag