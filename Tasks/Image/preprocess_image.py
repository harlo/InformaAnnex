from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def preprocessImage(task):
	print "\n\n************** IMAGE PREPROCESSING [START] ******************\n"
	print "image preprocessing at %s" % task.img_id
	task.setStatus(412)
	
	import re
	from json import loads
	
	from Models.ic_image import InformaCamImage
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	image = InformaCamImage(_id=task.img_id)
	if image is None: 
		print "DOC IS NONE"
		return