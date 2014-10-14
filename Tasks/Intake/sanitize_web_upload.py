from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def sanitizeWebUpload(uv_task):
	task_tag = "SANITIZE WEB UPLOAD"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % uv_task.doc_id
	uv_task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=uv_task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	media.from_web_upload = True
	media.notarizedSave(['from_web_upload'])

	# TODO: delete all assets except for j3ms and sigs
	
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag