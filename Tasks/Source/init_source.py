from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def initSource(task):
	task_tag = "INITING SOURCE"
	print "\n\n************** %s [START] ******************\n" % task_tag
	task.setStatus(412)
	
	from lib.Worker.Models.ic_source import InformaCamSource
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	source = InformaCamSource(_id=task.doc_id)
	if source is None:
		print "SOURCE DOCUMENT DOES NOT EXIST"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	if not hasattr(task, "assets"):
		print "NO ASSETS FOR THIS SOURCE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	import re, json, os
	from conf import ANNEX_DIR
	
	next_task = None
	for asset in task.assets:
		description = None
		tags = None
		sync = False
		
		if re.match(r'publicKey', asset):
			# import key
			description = "Source's public pgp key"
			tags = [ASSET_TAGS['PGP_KEY']]
			
			from lib.Worker.Models.uv_task import UnveillanceTask
		
			next_task = UnveillanceTask(inflate={
				'doc_id' : source._id,
				'task_path' : "PGP.import_key.importKey",
				'queue' : task.queue
			})
			sync = True
		elif re.match(r'credentials', asset):
			# parse creds
			with open(os.path.join(ANNEX_DIR, source.base_path, asset), 'rb') as C:
				try:
					credentials = json.loads(C.read())
					if DEBUG: print credentials
					for field in ['email','alias']:
						if field in credentials.keys() and credentials[field] != "":
							setattr(source, field, credentials[field])
					
					source.save()
				except Exception as e:
					if DEBUG: print e
					pass
			
					
		asset_path = source.addAsset(None, asset, description=description, tags=tags)
		print "ASSET PATH: %s" % asset_path
		
		if asset_path is None: continue
		if sync:
			print "ADDING %s AS FILE AS WELL:" % asset_path
			source.addFile(asset_path, None, sync=True)
			
	if next_task is None:
		print "NO PUBLIC KEY FOR SOURCE."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	source.addCompletedTask(task.task_path)
	from time import sleep
	sleep(10)
	
	next_task.run()
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag
