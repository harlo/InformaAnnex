from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def unpackJ3MLog(uv_task):
	task_tag = "UNPACKING J3M LOG"
	print "\n\n************** %s [START] ******************\n" % task_tag
	uv_task.setStatus(412)
		
	from lib.Worker.Models.ic_j3mlog import InformaCamLog
	from conf import DEBUG
	
	if not hasattr(uv_task, "assets"):
		print "NO ASSETS FOR THIS J3M LOG"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	j3m_log = InformaCamLog(_id=uv_task.doc_id)
	if j3m_log is None:
		print "J3M LOG DOES NOT EXIST"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	if DEBUG:
		print "\n\nTHIS IS THE J3M IN QUESTION\n"
		print j3m_log.emit()
		print "\n\n"
	
	import re, os
	from fabric.api import local, settings
	
	from lib.Worker.Models.uv_task import UnveillanceTask
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import ANNEX_DIR
	
	next_task = None
	for asset in uv_task.assets:
		print "J3M LOG ASSET: %s" % asset
		attachment = None
		
		if re.match(r'log.j3m(?:\.json)?', asset):
			# is the j3m
			if DEBUG:
				print "\n\n*************SAVING ASSET TO J3M (asset %s)" % asset
				for key in j3m_log.emit().keys():
					print key
					print type(getattr(j3m_log, key))
					print "\n"
				print "\n\n"
			
			try:	
				j3m_name = j3m_log.addAsset(None, asset)
			except Exception as e:
				print "WE COULD NOT ADD ASSET %s?" % asset
				print e
				print "\n\n************** %s [WARN] ******************\n" % task_tag
				continue
				
			if j3m_name is None:
				print "COULD NOT ADD J3M."
				print "\n\n************** %s [WARN] ******************\n" % task_tag
				continue
			
			next_task = UnveillanceTask(inflate={
				'task_path' : "J3M.j3mify.j3mify",
				'doc_id' : j3m_log._id,
				'queue' : uv_task.queue,
				'j3m_name' : j3m_name
			})
			
		elif re.match(r'.+\.(?:jpg|mkv)$', asset):
			# is a submission; create it, but move asset over into ANNEX_DIR first
			asset_path = os.path.join(ANNEX_DIR, j3m_log.base_path, asset)
			if DEBUG:
				print "MOVING ASSET FROM %s" % asset_path
				
			with settings(warn_only=True):
				local("mv %s %s" % (asset_path, ANNEX_DIR))
			
			media = UnveillanceDocument(inflate={ 'file_name' : asset })
			
			if not hasattr(j3m_log, "documents"): j3m_log.documents = []
			j3m_log.documents.append(media)
			
			media_task = UnveillanceTask(inflate={
				'task_path' : "Documents.evaluate_document.evaluateDocument",
				'doc_id' : media._id,
				'queue' : uv_task.queue,
				'file_name' : asset
			})
			media_task.run()
	
	from vars import MIME_TYPES
	j3m_log.original_mime_type = j3m_log.mime_type
	j3m_log.mime_type = MIME_TYPES['j3mlog']

	print "\n\n*********BEFORE SAVING:\n%s\n\n*******" % j3m_log.emit()	
	j3m_log.save()
	
	if next_task is not None: next_task.run()
	
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag
