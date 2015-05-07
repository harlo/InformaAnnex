from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def verifyVisualContent(task):
	task_tag = "VERIFYING VISUAL CONTENT"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(302)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return
	
	j3m = media.loadAsset("j3m.json")
	if j3m is None:
		print "NO J3M AT ALL"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return
	
	
	from json import loads
	
	from vars import MIME_TYPES
	
	try:
		supplied_hashes = loads(j3m)['genealogy']['hashes']
	except KeyError as e:
		print "NO HASHES"
		print "\n\n************** %s [WARNING] ******************\n" % task_tag
		task.finish()
		return
		
	media.media_verified = False
	if not hasattr(media, "verified_hash"):	
		if media.mime_type == MIME_TYPES['image']:
			media.get_image_hash()
		elif media.mime_type == MIME_TYPES['video']:
			media.get_video_hash()
	
	if type(supplied_hashes) is list:
		for hash in supplied_hashes:
			if type(hash) is unicode:
				hash = str(hash)
			
			if hash == media.verified_hash:
				media.media_verified = True
	
	media.saveFields("media_verified")
	media.addCompletedTask(task.task_path)

	task.routeNext()
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag

