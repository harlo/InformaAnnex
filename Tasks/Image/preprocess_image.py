from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def preprocessImage(task):
	print "\n\n************** IMAGE PREPROCESSING [START] ******************\n"
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
	
	import re
	from json import loads
	
	from lib.Worker.Models.ic_image import InformaCamImage
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	image = InformaCamImage(_id=task.doc_id)
	if image is None:
		print "DOC IS NONE"
		print "\n\n************** IMAGE PREPROCESSING [ERROR] ******************\n"
		return
	
	import os
	from conf import getConfig, ANNEX_DIR
	try:
		J3M_DIR = os.path.join(getConfig('jpeg_tools_dir'), "jpeg-reaction", "lib")			
	except Exception as e:
		if DEBUG: print "NO J3M DIR! %s" % e
		print "\n\n************** IMAGE PREPROCESSING [ERROR] ******************\n"
		return
		
	from subprocess import Popen, PIPE
	cmd = [os.path.join(J3M_DIR, "j3mparser.out"), 
		os.path.join(ANNEX_DIR, image.file_name)]
	
	p = Popen(cmd, stdout=PIPE, close_fds=True)
	data = p.stdout.readline()
	while data:
		if DEBUG: print data
		
		data = p.stdout.readline()
	
	p.stdout.close()
	
	
	print "\n\n************** IMAGE PREPROCESSING [START] ******************\n"