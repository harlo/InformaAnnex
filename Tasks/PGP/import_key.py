from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def importKey(task):
	task_tag = "IMPORTING KEY"
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
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag