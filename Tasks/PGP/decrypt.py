from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def decrypt(uv_task):
	task_tag = "DECRYPTING"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "decrypting pgp blob for %s" % uv_task.doc_id
	uv_task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
		
	media = UnveillanceDocument(_id=uv_task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
	
	if not media.getFile(uv_task.pgp_file):
		print "NO PGP FILE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
	
	from conf import getSecrets
	gpg_pwd = getSecrets("gpg_pwd")
	if gpg_pwd is None:
		err_msg = "NO PASSPHRASE TO DECRYPT"
		print err_msg
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(message=err_msg)
		return
	
	# save as task.pgp_file.decrypted or whatever	
	import os
	from fabric.api import local, settings
	from fabric.context_managers import hide

	from conf import ANNEX_DIR, DEBUG
	
	if not hasattr(uv_task, "save_as"): 
		save_as = "%s.decrypted" % uv_task.pgp_file
	else:
		save_as = uv_task.save_as

	with settings(hide('everything'), warn_only=True):
		local("gpg --no-tty --passphrase %s --output %s --decrypt %s" % (gpg_pwd,
		os.path.join(ANNEX_DIR, save_as), os.path.join(ANNEX_DIR, uv_task.pgp_file)))
	
	del gpg_pwd
		
	task_path = None
	if hasattr(uv_task, 'next_task_path'):
		# if there is a next path tag, do that. or...
		task_path = uv_task.next_task_path
	else:
		# route according to mime type
		# get mime type of decrypted
		from vars import MIME_TYPE_TASKS
		from lib.Worker.Utils.funcs import getFileType
		mime_type = getFileType(os.path.join(ANNEX_DIR, save_as))
		
		# usable: json (a j3m), zip (a source or a log->batch)
		if mime_type in MIME_TYPE_TASKS.keys():
			print "mime type (%s) usable..." % mime_type
						
			try:
				task_path = MIME_TYPE_TASKS[mime_type][0]
			except Exception as e:
				print e

	media.addCompletedTask(uv_task.task_path)
	
	if task_path is not None:
		from lib.Worker.Models.uv_task import UnveillanceTask
		new_task = UnveillanceTask(inflate={
			'task_path' : task_path,
			'doc_id' : media._id,
			'queue' : uv_task.queue,
			'file_name' : save_as
		})
	
		new_task.run()
	
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag