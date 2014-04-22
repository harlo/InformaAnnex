from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def unzipAndEvaluateArchive(task):
	task_tag = "UNZIPPING FILE"
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
	
	zip = media.getAsset(task.file_name, return_only="path")
	print zip
	
	'''
		could be either a source or a j3mlog
	'''
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag

@celery_app.task
def audioConvert(task):
	task_tag = "CONVERTING SOME AUDIO"
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
	
	audio = media.getAsset(task.src_file, return_only="path")
	if audio is None:
		print "SOURCE FILE IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	from subprocess import Popen
	cmd = ["ffmpeg", "-y", "-i", audio, "-vn", "-acodec", "mp2", 
		"-ar", "22050", "-f", task.formats[1], 
		audio.replace(".%s" % task.formats[0], ".%s" % task.formats[1])]

	p = Popen(cmd)
	p.wait()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag