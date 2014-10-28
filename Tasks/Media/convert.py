from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def unzipAndEvaluateArchive(uv_task):
	task_tag = "UNZIPPING FILE"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "unzipping and evaluating %s" % uv_task.doc_id
	uv_task.setStatus(302)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=uv_task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
	
	if hasattr(uv_task, "file_name"):
		zip = uv_task.file_name
	else:
		zip = media.file_name
	
	if DEBUG: print "Zip file here: %s" % zip
	
	if zip is None or not media.getFile(zip):
		print "THERE IS NO ZIP HERE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
	
	import os
	from time import sleep
	from fabric.api import *
	from fabric.context_managers import hide
	from conf import ANNEX_DIR
	
	with settings(warn_only=True):
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)
		local("unzip -o %s -d %s" % (zip, media.base_path))
		sleep(2)
		
		try:
			unzipped_files = local("ls %s" % media.base_path, capture=True).splitlines()
		except Exception as e:
			print e
			err_msg = "Could not find any unzipped files in %s" % media.base_path
			print err_msg
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			uv_task.fail(status=412, message=err_msg)
			return
			
		os.chdir(this_dir)
	
	if DEBUG: print "UNZIPPED FILES: \n%s" % unzipped_files
	
	ZIPPED_ASSET_EXPECTED_NAMES = {
		'source' : [
			r"publicKey",
			r"baseImage_\d",
			r"credentials"
		],
		'j3mlog' : [
			r"log.j3m(?:\.json)?",
			r".+\.(?:jpg|mkv)$"
		]
	}
	
	next_task = { 
		'queue' : uv_task.queue,
		'assets' : [],
		'task_path' : None,
		'doc_id' : media._id
	}
	
	import re
	for facet, names in ZIPPED_ASSET_EXPECTED_NAMES.iteritems():
		for file in unzipped_files:
			matches = [n for n in names if re.match(n, file) is not None]
			if len(matches) > 0:
				next_task['assets'].append(file)
				
				if next_task['task_path'] is None:
					if facet == "source":
						next_task.update({
							'task_path' : "Source.init_source.initSource"
						})
					elif facet == "j3mlog":
						next_task.update({
							'task_path' : "Log.unpack_j3mlog.unpackJ3MLog"
						})
	
	if next_task['task_path'] is None:
		print "NO DECERNABLE TASK PATH"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
		
	'''
		could be either a source or a j3mlog at this point.
	'''

	media.addCompletedTask(uv_task.task_path)

	from lib.Worker.Models.uv_task import UnveillanceTask
	new_task = UnveillanceTask(inflate=next_task)
	new_task.run()
	
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag

@celery_app.task
def audioConvert(task):
	task_tag = "CONVERTING SOME AUDIO"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(302)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return
	
	audio = media.getAsset(task.src_file, return_only="path")
	if audio is None:
		print "SOURCE FILE IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
	
	from subprocess import Popen
	cmd = ["ffmpeg", "-y", "-i", audio, "-vn", "-acodec", "mp2", 
		"-ar", "22050", "-f", task.formats[1], 
		audio.replace(".%s" % task.formats[0], ".%s" % task.formats[1])]

	p = Popen(cmd)
	p.wait()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag