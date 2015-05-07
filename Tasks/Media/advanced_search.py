from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def update_similar_media(uv_task):
	task_tag = "LOCATING SIMILAR MEDIA"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "similar images for doc at %s" % uv_task.doc_id
	uv_task.setStatus(302)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	media = UnveillanceDocument(_id=uv_task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	media.update_similar_media()
	media.addCompletedTask(uv_task.task_path)

	uv_task.routeNext()
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag



