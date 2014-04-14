from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def requestDecrypt(task):
	print "\n\n************** DECRYPTING [START] ******************\n"
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
		
	media = UnveillanceDocument(_id=task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** DECRYPTING [ERROR] ******************\n"
		return
	
	if not media.addFile(task.pgp_file, None, sync=True):
		print "COULD NOT SYNC FILE %s" % task.pgp_file
		print "\n\n************** DECRYPTING [ERROR] ******************\n"
		return
	
	task.finish()
	print "\n\n************** DECRYPTING [END] ******************\n"