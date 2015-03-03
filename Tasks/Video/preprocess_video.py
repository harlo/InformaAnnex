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

	if not os.path.exists(j3m_attachment):
		print "FFMPEG COULD NOT DO THE THING"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	from lib.Worker.Utils.funcs import getFileType
	from vars import MIME_TYPES, MIME_TYPE_MAP

	next_tasks = []
	inflate = {}

	j3m_content = video.loadAsset("j3m_raw.txt")
	print j3m_content

	j3m_content_mime_type = getFileType(j3m_content, as_buffer=True)

	if j3m_content_mime_type not in [MIME_TYPES['pgp'], MIME_TYPES['gzip']]:
		j3m_content = b64decode(j3m_content)
		if j3m_content is not None:
			j3m_content_mime_type = getFileType(j3m_content, as_buffer=True)

	if j3m_content_mime_type in [MIME_TYPES['pgp'], MIME_TYPES['gzip']]:
		asset_path = "j3m_raw.%s" % MIME_TYPE_MAP[j3m_content_mime_type]
		video.addAsset(j3m_content, asset_path)
						
		if j3m_content_mime_type == MIME_TYPES['pgp']:
			next_tasks.append("PGP.request_decrypt.requestDecrypt")
			inflate['pgp_file'] = asset_path			
		elif j3m_content_mime_type == MIME_TYPES['gzip']:
			next_tasks.append("J3M.j3mify.j3mify")
			video.addAsset(None, "j3m_raw.gz", tags=[ASSET_TAGS['OB_M']],
				description="j3m data extracted from mkv stream")

		video.addCompletedTask(uv_task.task_path)

	from vars import UPLOAD_RESTRICTION

	try:
		upload_restriction = video.getFileMetadata('uv_restriction')
	except Exception as e:
		print "could not get metadata for uv_restriction"
		print e

	if upload_restriction is None or upload_restriction == UPLOAD_RESTRICTION['no_restriction']:
		next_tasks.append("Video.make_derivatives.makeDerivatives")
	
	if len(next_tasks) > 0:
		uv_task.put_next(next_tasks)
		uv_task.routeNext(inflate=inflate)
	
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag