from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def requestDecrypt(task):
	task_tag = "DECRYPTING"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
		
	media = UnveillanceDocument(_id=task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	if not media.addFile(task.pgp_file, None, sync=True):
		print "COULD NOT SYNC FILE %s" % task.pgp_file
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	task.update_file = "%s.decrypted" % task.pgp_file
	task.on_update = "Documents.evaluate_file.evaluateFile"
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag