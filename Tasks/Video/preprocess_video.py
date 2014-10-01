from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def makeDerivatives(task):
	task_tag = "PREPROCESSING VIDEO"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.ic_video import InformaCamVideo
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	video = InformaCamVideo(_id=task.doc_id)
	if video is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
		
	asset_path = video.addAsset(None, "j3m_raw.txt")
	
	if asset_path is None:
		print "COULD NOT MAKE ASSET"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	was_encrypted = False
	obscura_marker_found = False
	
	import os
	from subprocess import Popen
	
	from lib.Core.Utils.funcs import b64decode
	from conf import ANNEX_DIR
	
	p = Popen(["ffmpeg", "-y", "-dump_attachment:t", asset_path, "-i",
		os.path.join(ANNEX_DIR, video.file_name)])
	p.wait()
	
	un_b64 = b64decode(video.loadAsset("j3m_raw.txt"))
	
	if un_b64 is not None:
		from lib.Worker.Utils.funcs import getFileType
		from vars import MIME_TYPES, MIME_TYPE_MAP

		obscura_marker_found = True
				
		un_b64_mime_type = getFileType(un_b64, as_buffer=True)
		if un_b64_mime_type in [MIME_TYPES['pgp'], MIME_TYPES['gzip']]:
			
			asset_path = "j3m_raw.%s" % MIME_TYPE_MAP[un_b64_mime_type]
			video.addAsset(un_b64, asset_path)
			
			new_task = { 'doc_id' : video._id, 'queue' : task.queue }
			task_path = None
				
			if un_b64_mime_type == MIME_TYPES['pgp']:
				task_path = "PGP.request_decrypt.requestDecrypt"
				new_task['pgp_file'] = asset_path
				
				was_encrypted = True				
				
			elif un_b64_mime_type == MIME_TYPES['gzip']:
				task_path = "J3M.j3mify.j3mify"
				video.addAsset(None, "j3m_raw.gz", tags=[ASSET_TAGS['OB_M']],
					description="j3m data extracted from mkv stream")

			video.addCompletedTask(task.task_path)

			if task_path is not None:
				new_task['task_path'] = task_path					
				new_task = UnveillanceTask(inflate=new_task)
				new_task.run()
	
	# TODO: how to compile metadata with ffmpeg?
	'''	
	new_task = UnveillanceTask(inflate={
		'task_path' : "Documents.compile_metadata.compileMetadata",
		'doc_id' : video._id,
		'queue' : task.queue,
		'md_rx' : '%s\s+%s\s+\d+x\d+\s+.+\s+\((.*)\)',
		'md_namespace' : "FFmpeg",
		'md_extras' : {
			'was_encrypted' : 1.0 if was_encrypted else 0.0,
			'has_j3m' : 1.0 if obscura_marker_found else 0.0
		},
		'md_file' : "file_metadata.txt"
	})
	new_task.run()
	'''
	
	from vars import UPLOAD_RESTRICTION

	try:
		upload_restriction = video.getFileMetadata('uv_restriction')
	except Exception as e:
		print "could not get metadata for uv_restriction"
		print e

	if upload_restriction is None or upload_restriction == UPLOAD_RESTRICTION['no_restriction']:
		new_task = UnveillanceTask(inflate={
			'task_path' : "Video.make_derivatives.makeDerivatives",
			'doc_id' : video._id,
			'queue' : task.queue
		})
		new_task.run()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag