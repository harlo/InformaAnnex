from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def decrypt(task):
	task_tag = "DECRYPTING"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "decrypting pgp blob for %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
		
	media = UnveillanceDocument(_id=task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	pgp_file = media.getFile(task.pgp_file, return_only="path")
	if pgp_file is None:
		print "NO PGP FILE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	gpg_pwd = getConfig("informacam.pgp.passphrase")
	if gpg_pwd is None:
		print "NO PASSPHRASE TO DECRYPT"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	# save as task.pgp_file.decrypted or whatever
	if not hasattr(task, "save_as"): save_as = "%s.decrypted"
	else: save_as = task.save_as

	from fabric.api import *
	
	local("gpg --no-tty --passphrase %s --output %s --decrypt %s" % (gpg_pwd,
		save_as, pgp_file))
	del gpg_pwd
	
	# if there is a next path tag, do that. or...
	task_path = None
	if hasattr(task, 'next_task_path'):
		task_path = task.next_task_path
	
	# route according to mime type
	else:
		# get mime type of decrypted
		from vars import MIME_TYPE_TASKS
		from lib.Core.Utils.funcs import getFileType
		mime_type = getFileType("%s.decrypted" % pgp_file)
		
		# usable: json (a j3m), zip (a source or a log->batch)
		if mime_type in MIME_TYPE_TASKS.keys():
			if DEBUG:
				print "mime type usable..."
				print MIME_TYPE_TASKS[mime_type][0]
	
	if task_path is not None:
		from lib.Worker.Models.uv_task import UnveillanceTask
		new_task = UnveillanceTask(inflate={
			'task_path' : task_path,
			'doc_id' : media._id,
			'queue' : task.queue,
			'file_name' : "%s.decrypted" % pgp_file
		})
	
		if DEBUG: print new_task.emit()
		new_task.run()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag