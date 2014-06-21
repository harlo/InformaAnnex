from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def doIntake(task):
	task_tag = "INTAKE"
	print "\n\n************** %s [START] ******************\n" % task_tag
	task.setStatus(412)

	if not hasattr(task, 'mode'): mode = "submissions"

	if mode not in ['sources', 'submissions']:
		print "No acceptable mode"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	repo = None
	try:
		from conf import getSecrets
		repo = getSecrets("repo")
	except Exception as e: pass
	
	if repo is None:
		print "No repos to query."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	client = None

	if repo['source'] == "google_drive":
		client = InformaCamDriveClient(mode=mode)
	elif repo['source'] == "globaleaks":
		client = InformaCamGlobaleaksClient(mode=mode)

	if not client.usable:
		print "Client invalid."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	for asset in client.listAssets(omit_absorbed=True):
		mime_type = client.getAssetMimeType(asset)
		if not mime_type in client.mime_types.itervalues(): continue
	
		if client.download(asset) is not None:
			client.absorb(asset)
			client.lockFile(asset)

	client.updateLog()

	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag
