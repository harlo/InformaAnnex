from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def unpackJ3MLog(task):
	task_tag = "UNPACKING J3M LOG"
	print "\n\n************** %s [START] ******************\n" % task_tag
	task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag
