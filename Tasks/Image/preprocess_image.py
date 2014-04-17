from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def preprocessImage(task):
	task_tag = "IMAGE PREPROCESSING"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.ic_image import InformaCamImage
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	image = InformaCamImage(_id=task.doc_id)
	if image is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	import os
	from conf import getConfig, ANNEX_DIR
	try:
		J3M_DIR = getConfig('jpeg_tools_dir')
	except Exception as e:
		if DEBUG: print "NO J3M DIR! %s" % e
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	import re
	from subprocess import Popen, PIPE
	from cStringIO import StringIO
	
	tiff_txt = StringIO()
	
	obscura_marker_found = False
	was_encrypted = False
	ic_j3m_txt = None
	
	cmd = [os.path.join(J3M_DIR, "j3mparser.out"), 
		os.path.join(ANNEX_DIR, image.file_name)]
	
	p = Popen(cmd, stdout=PIPE, close_fds=True)
	data = p.stdout.readline()
	while data:
		if DEBUG: print data
		write_line = False
		
		if re.match(r'^file: .*', line): pass
		elif re.match(r'^Generic APPn ffe0 loaded.*', line): pass
		elif re.match(r'^Component.*', line): pass
		elif re.match(r'^Didn\'t find .*', line): pass
		elif re.match(r'^Got obscura marker.*', line): 
			obscura_marker_found = True
			ic_j3m_txt = StringIO()
		else:
			if obscura_marker_found: ic_j3m_txt.write(line)
			else: tiff_txt.write(line)
				
		data = p.stdout.readline()
		
	p.stdout.close()
	tiff_txt.close()
	
	image.addAsset(tiff_txt.getvalue(), "file_metadata.txt",
		description="tiff metadata as per jpeg redaction library")
	del tiff_txt
	
	if ic_j3m_txt is not None:
		ic_j3m_txt.close()
		
		from lib.Core.Utils.funcs import b64decode
		un_b64 = b64decode(ic_j3m_txt.getvalue())
		del ic_j3m_txt
		
		if un_b64 is not None:	
			from lib.Worker.Utils.funcs import getFileType
			from vars import MIME_TYPES, MIME_TYPE_MAP
		
			un_b64_mime_type = getFileType(un_b64, as_buffer=True)
			if un_b64_mime_type in [MIME_TYPES['pgp'], MIME_TYPES['gzip']]:
	
				asset_path = "j3m_raw.%s" % MIME_TYPE_MAP[un_b64_mime_type]
				image.addAsset(un_b64, asset_path)
				
				new_task = { 'doc_id' : image._id, 'queue' : task.queue }
				task_path = None
				
				if un_b64_mime_type == MIME_TYPES['pgp']:
					task_path = "PGP.request_decrypt.requestDecrypt"
					new_task['pgp_file'] = asset_path
					
					was_encrypted = True
					
				elif un_b64_mime_type == MIME_TYPES['gzip']:
					task_path = "J3M.j3mify.j3mify"
					image.addAsset(None, "j3m_raw.gz", tags=[ASSET_TAGS['OB_M']], 
						description="j3m data extracted from obscura marker")

				if task_path is not None:
					new_task['task_path'] = task_path					
					new_task = UnveillanceTask(inflate=new_task)
					new_task.run()

	new_task = UnveillanceTask(inflate={
		'task_path' : "Documents.compile_metadata.compileMetadata",
		'doc_id' : image._id,
		'queue' : task.queue,
		'md_rx' : '%s\s+%s\s+\d+x\d+\s+.+\s+\((.*)\)',
		'md_namespace' : "Tiff",
		'md_extras' : {
			'was_encrypted' : 1.0 if was_encrypted else 0.0,
			'has_j3m' : 1.0 if obscura_marker_found else 0.0
		},
		'md_file' : "file_metadata.txt"
	})
	new_task.run()
	
	new_task = UnveillanceTask(inflate={
		'task_path' : "Image.make_derivatives.makeDerivatives",
		'doc_id' : image._id,
		'queue' : task.queue
	})
	new_task.run()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag