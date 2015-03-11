from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def preprocessVideo(uv_task):
	task_tag = "PREPROCESSING VIDEO"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % uv_task.doc_id
	uv_task.setStatus(302)
		
	from lib.Worker.Models.ic_video import InformaCamVideo
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	video = InformaCamVideo(_id=uv_task.doc_id)
	if video is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
		
	asset_path = video.addAsset(None, "j3m_raw.txt")
	
	if asset_path is None:
		print "COULD NOT MAKE ASSET"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
	
	was_encrypted = False
	obscura_marker_found = False
	
	import os
	from fabric.api import settings, local
	
	from lib.Core.Utils.funcs import b64decode
	from conf import ANNEX_DIR
	
	j3m_attachment = os.path.join(ANNEX_DIR, asset_path)
	cmd = ["ffmpeg", "-y", "-dump_attachment:t", j3m_attachment, "-i",
		os.path.join(ANNEX_DIR, video.file_name)]

	with settings(warn_only=True):
		ffmpeg = local(" ".join(cmd))

	from vars import UPLOAD_RESTRICTION

	if os.path.exists(j3m_attachment):
		uv_task.put_next("J3M.locate_j3m.locate_j3m")

		try:
			upload_restriction = video.getFileMetadata('uv_restriction')
		except Exception as e:
			print "could not get metadata for uv_restriction"
			print e
		
	else:
		print "NO IC J3M TEXT FOUND???"
		print "\n\n************** %s [WARN] ******************\n" % task_tag
		upload_restriction = UPLOAD_RESTRICTION['for_local_use_only']
	
	if upload_restriction is None or upload_restriction == UPLOAD_RESTRICTION['no_restriction']:
		uv_task.put_next("Video.make_derivatives.makeDerivatives")
	
	video.addCompletedTask(uv_task.task_path)	
	
	uv_task.routeNext()
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag