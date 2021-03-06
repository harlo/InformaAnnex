from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def evaluateTextFile(task):
	task_tag = "EVALUATING TEXT FILE"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "evaluating text file at %s" % task.doc_id
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
	
	if not media.queryFile(media.file_name):
		print "NO DOCUMENT CONTENT"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return
	
	content = media.loadFile(media.file_name)
	if content is None:
		print "NO DOCUMENT CONTENT"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return
	
	from lib.Core.Utils.funcs import b64decode
	un_b64 = b64decode(content)
	
	# We have removed base 64-ing from the log files...
	if un_b64 is None:
		un_b64 = content

	if un_b64 is not None:
		from lib.Worker.Utils.funcs import getFileType
		from vars import MIME_TYPES, MIME_TYPE_MAP
		
		un_b64_mime_type = getFileType(un_b64, as_buffer=True)
		if DEBUG:
			print "MIME TYPE: %s" % un_b64_mime_type
		
		if un_b64_mime_type not in [MIME_TYPES['pgp'], MIME_TYPES['wildcard']]:
			err_msg = "MIME TYPE NOT USABLE"
			print err_msg
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			task.fail(status=412, message=err_msg)
			return
		
		media.addAsset(un_b64, "%s.pgp" % media.file_name, description="un-b64'ed pgp asset")
		media.addCompletedTask(task.task_path)

		message_sentinel = "-----BEGIN PGP MESSAGE-----"
		if un_b64[0:len(message_sentinel)] == message_sentinel:
			task.put_next("PGP.decrypt.decrypt")
			task.routeNext(inflate={
				'pgp_file' : ".data/%s/%s.pgp" % (media._id, media.file_name)
			})

	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag