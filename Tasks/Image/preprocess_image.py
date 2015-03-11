from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def preprocessImage(task):
	task_tag = "IMAGE PREPROCESSING"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(302)
		
	from lib.Worker.Models.ic_image import InformaCamImage
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	image = InformaCamImage(_id=task.doc_id)
	if image is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return
	
	import os
	from conf import getConfig, ANNEX_DIR
	try:
		J3M_DIR = getConfig('jpeg_tools_dir')
	except Exception as e:
		if DEBUG: print "NO J3M DIR! %s" % e
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return
	
	import re
	from subprocess import Popen, PIPE
	from cStringIO import StringIO

	from vars import UPLOAD_RESTRICTION
	from lib.Worker.Models.uv_task import UnveillanceTask
	
	tiff_txt = StringIO()
	
	obscura_marker_found = False
	was_encrypted = False
	ic_j3m_txt = None
	
	cmd = [os.path.join(J3M_DIR, "j3mparser.out"), 
		os.path.join(ANNEX_DIR, image.file_name)]
	
	p = Popen(cmd, stdout=PIPE, close_fds=True)
	data = p.stdout.readline()
	while data:
		data = data.strip()
				
		if re.match(r'^file: .*', data): pass
		elif re.match(r'^Generic APPn .*', data): pass
		elif re.match(r'^Component.*', data): pass
		elif re.match(r'^Didn\'t find .*', data): pass
		elif re.match(r'^Got obscura marker.*', data):
			if DEBUG:
				print "\n\nWE ALSO HAVE J3M DATA\n\n"
			
			obscura_marker_found = True
			ic_j3m_txt = StringIO()
		else:
			if obscura_marker_found:
				ic_j3m_txt.write(data)
			else:
				tiff_txt.write(data)
				
		data = p.stdout.readline()
		
	p.stdout.close()
	
	image.addAsset(tiff_txt.getvalue(), "file_metadata.txt",
		description="tiff metadata as per jpeg redaction library")
	
	tiff_txt.close()
	del tiff_txt
	
	if ic_j3m_txt is not None:
		asset_path = image.addAsset(ic_j3m_txt.getvalue(), "j3m_raw.txt")

		if asset_path is None:
			print "COULD NOT MAKE ASSET"
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			uv_task.fail()
			return

		task.put_next("J3M.locate_j3m.locate_j3m")

		try:
			upload_restriction = image.getFileMetadata('uv_restriction')
		except Exception as e:
			print "could not get metadata for uv_restriction"
			print e

	else:
		print "NO IC J3M TEXT FOUND???"
		print "\n\n************** %s [WARN] ******************\n" % task_tag
		upload_restriction = UPLOAD_RESTRICTION['for_local_use_only']
	

	if upload_restriction is None or upload_restriction == UPLOAD_RESTRICTION['no_restriction']:
		task.put_next("Image.make_derivatives.makeDerivatives")

	task.put_next("Image.get_vector.get_vector")

	image.addCompletedTask(task.task_path)
	
	task.routeNext()
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag