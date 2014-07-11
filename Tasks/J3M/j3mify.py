from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def j3mify(uv_task):
	task_tag = "J3MIFYING"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "j3mifying asset at %s" % uv_task.doc_id
	uv_task.setStatus(412)
	
	import os
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=uv_task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	from conf import ANNEX_DIR
	if hasattr(uv_task, "j3m_name"):
		j3m_name = uv_task.j3m_name
	else:
		j3m_name = os.path.join(media.base_path, "j3m_raw.gz")
	
	if not media.getFile(j3m_name):
		print "NO J3M.GZ at %s" % j3m_name
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	
	from cStringIO import StringIO
	from lib.Worker.Utils.funcs import getFileType, unGzipBinary
	from vars import MIME_TYPES
	
	j3m = media.loadFile(j3m_name)
	j3m_type = getFileType(j3m, as_buffer=True)
	
	if j3m_type == MIME_TYPES['gzip']:
		j3m = unGzipBinary(j3m)
	
	if j3m is None or getFileType(j3m, as_buffer=True) != MIME_TYPES['json']:
		print "THIS IS NOT A J3M (type %s)" % j3m_type
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	import json

	try:
		j3m_sig = json.loads(j3m)['signature']
	except KeyError as e:
		print "NO SIGNATURE TO EXTRACT"
		print "\n\n************** J3MIFYING [ERROR] ******************\n"
		return
	
	media.addAsset(j3m_sig, "j3m.sig", tags=[ASSET_TAGS['SIG']],
		description="The j3m's signature")
	
	front_sentinel = "{\"j3m\":"
	back_sentinel = ",\"signature\":"
	
	j3m = j3m[len(front_sentinel) : j3m.rindex(back_sentinel)]
	media.addFile(
		media.addAsset(
			j3m, "j3m.json", tags=[ASSET_TAGS['J3M']], description="The j3m itself."), 
		None, sync=True)
	
	from lib.Worker.Models.uv_task import UnveillanceTask
	next_task = UnveillanceTask(inflate={
		'task_path' : "PGP.verify_signature.verifySignature",
		'doc_id' : media._id,
		'queue' : uv_task.queue
	})
	next_task.run()
	
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag