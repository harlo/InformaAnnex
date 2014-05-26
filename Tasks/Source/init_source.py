from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def initSource(task):
	task_tag = "INITING SOURCE"
	print "\n\n************** %s [START] ******************\n" % task_tag
	task.setStatus(412)
	
	if not hasattr(task, "assets"):
		print "NO ASSETS FOR THIS SOURCE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
		
	from lib.Worker.Models.ic_source import InformaCamSource
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	source = InformaCamSource(inflate={
	
	})
	
	for asset in task.assets:
		description = None
		tags = None
		
		
		
		source.addAsset(None, asset, description=description, tags=tags)
	
	source.reverifyMedia()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag
