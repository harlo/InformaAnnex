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
	
	if zip is None:
		print "THERE IS NO ZIP HERE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	from fabric.api import *
	unzipped_files = local("unzip %s -d %s" % (zip, media.base_path))
	if DEBUG: print unzipped_files
	
	ZIPPED_ASSET_EXPECTED_NAMES = {
		'source' : [
			r"publicKey",
			r"baseImage_\d",
			r"credentials"
		],
		'j3mlog' : [
			r"log.j3m(?:\.json)?",
			r".+\.jpg",
			r".+\.mkv"
		]
	}
	
	next_task = { 
		'queue' : task.queue,
		'assets' : unzipped_files,
		'task_path' : None
	}
	
	import re
	for facet, names in ZIPPED_ASSET_EXPECTED_NAMES.iteritems():
		for file in unzipped_files:
			matches = [n for n in names if re.match(n, file)]
			if len(matches) > 0:
				if facet == "source":
					next_task.update({
						'task_path' : "Source.init_source.initSource"
					})
				elif facet == "j3mlog":
					next_task.update({
						'task_path' : "Log.unpack_j3mlog.unpackJ3MLog"
					})
				break
		
		if next_task['task_path'] is not None: break
	
	if next_task['task_path'] is None:
		print "NO DECERNABLE TASK PATH"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
		
	'''
		could be either a source or a j3mlog
	'''
	
	new_task = UnveillanceTask(inflate=next_task)
	if DEBUG: print new_task.emit()
	new_task.run()
	
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