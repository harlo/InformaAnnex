from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def makeDerivatives(task):
	print "\n\n************** DERIVATIVES: IMAGE [START] ******************\n"
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.ic_image import InformaCamImage
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	image = InformaCamImage(_id=task.doc_id)
	if image is None:
		print "DOC IS NONE"
		print "\n\n************** DERIVATIVES: IMAGE [ERROR] ******************\n"
		return
	
	task.finish()
	print "\n\n************** DERIVATIVES: IMAGE [END] ******************\n"