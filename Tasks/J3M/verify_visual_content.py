from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def verifyVisualContent(task):
	task_tag = "VERIFYING VISUAL CONTENT"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	j3m = media.loadAsset("j3m.json")
	if j3m is None:
		print "NO J3M AT ALL"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	from json import loads
	from subprocess import Popen, PIPE
	from conf import ANNEX_DIR, getConfig
	
	supplied_hashes = loads(j3m)['genealogy']['hashes']
	media.media_verified = False
	
	if media.mime_type == MIME_TYPES['image']:
		cmd = ["java", "-jar", 
			os.path.join(getConfig('jpeg_tools_dir'), "JavaMediaHasher.jar"),
			os.path.join(ANNEX_DIR, media.file_name)]
	elif media.mime_type == MIME_TYPES['video']:
		cmd = ["ffmpeg", "-y", "-i",
			os.path.join(ANNEX_DIR, media.file_name), "-vcodec", "copy",
			"-an", "-f", "md5", "-"]
		
	p = Popen(cmd, stdout=PIPE, close_fds=True)
	verified_hash = p.stdout.readline().strip().replace("MD5=", "")
	p.stdout.close()
	
	if type(supplied_hashes) is list:
		for hash in supplied_hashes:
			if type(hash) is unicode:
				hash = str(hash)
			
			if hash == verified_hash:
				media.media_verified = True
	
	media.save()
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag