from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def verifySignature(task):
	task_tag = "VERIFYING SIGNATURE"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(302)
		
	from lib.Worker.Models.ic_media import InformaCamMedia
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = InformaCamMedia(_id=task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return
	
	if not media.set_j3m_comp():
		print "COULD NOT SET MEDIA COMP"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return

	if not media.verify_signature():
		print "COULD NOT VERIFY SIG"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return
	
	media.addCompletedTask(task.task_path)
	
	task.routeNext()
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag