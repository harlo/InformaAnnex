from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def doIntake(task):
	task_tag = "INTAKE"

	print "\n\n************** %s [START] ******************\n" % task_tag
	task.setStatus(302)

	next_mode = None
	if not hasattr(task, 'mode'):
		mode = "sources"
		next_mode = "submissions"
	else:
		mode = task.mode
		del task.mode

	if mode not in ['sources', 'submissions']:
		print "No acceptable mode"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return

	repo = None
	try:
		from conf import getSecrets
		repo = getSecrets("repo")
	except Exception as e:
		print "ERROR GETTING REPO: %s" % e
		pass
	
	if repo is None:
		print "No repos to query."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return

	client = None

	if repo['source'] == "google_drive":
		from lib.Worker.Models.ic_google_drive_client import InformaCamDriveClient
		try:
			client = InformaCamDriveClient(mode=mode)
		except Exception as e:
			print "ERROR Creating client:\n%s" % e
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			task.fail()
			return
	
	elif repo['source'] == "globaleaks":
		from lib.Worker.Models.ic_globaleaks_client import InformaCamGlobaleaksClient
		client = InformaCamGlobaleaksClient(mode=mode)

	if not client.usable:
		print "Client invalid."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return

	from time import sleep
	
	try:
		for asset in client.listAssets(omit_absorbed=True):
			mime_type = client.getAssetMimeType(asset)
			if not mime_type in client.mime_types.itervalues(): continue
	
			if client.download(asset) is not None:
				client.absorb(asset)
			
			sleep(5)

	except TypeError as e:
		print e

	if next_mode is not None:
		task.mode = next_mode
		doIntake(task)
	else:
		task.finish()
		print "\n\n************** %s [END] ******************\n" % task_tag