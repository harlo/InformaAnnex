from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def notarize_media(uv_task):
	task_tag = "NOTARIZING MEDIA"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "notarizing media for doc at %s" % uv_task.doc_id
	uv_task.setStatus(302)
		
	from lib.Worker.Models.ic_media import InformaCamMedia
	
	media = InformaCamMedia(_id=uv_task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	if not media.notarize():
		print "COULD NOT NOTARIZE MEDIA"
		print "\n\n************** %s [WARN] ******************\n" % task_tag
	else:
		media.addCompletedTask(uv_task.task_path)

	uv_task.routeNext()
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag

