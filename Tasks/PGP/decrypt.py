from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def decrypt(task):
	print "\n\n************** DECRYPTING [START] ******************\n"
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** DECRYPTING [ERROR] ******************\n"
		return
	
	task.finish()
	print "\n\n************** DECRYPTING [END] ******************\n"