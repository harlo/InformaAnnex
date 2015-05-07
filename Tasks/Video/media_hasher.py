from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def get_video_hash(uv_task):
	task_tag = "VIDEO HASHER"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "getting video hash for doc at %s" % uv_task.doc_id
	uv_task.setStatus(302)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	video = UnveillanceDocument(_id=uv_task.doc_id)
	if video is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	if not video.get_video_hash():
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	video.addCompletedTask(uv_task.task_path)

	uv_task.routeNext()
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag

	

