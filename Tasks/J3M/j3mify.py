from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def parse_zipped_j3m(uv_task):
	task_tag = "PARSING ZIPPED J3M"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "parsing zipped j3m asset at %s" % uv_task.doc_id
	uv_task.setStatus(302)
	
	import os
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=uv_task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
	
	from conf import ANNEX_DIR
	if hasattr(uv_task, "j3m_name"):
		j3m_name = uv_task.j3m_name
	else:
		j3m_name = os.path.join(media.base_path, "j3m_raw.gz")
	
	if not media.getFile(j3m_name):
		print "NO J3M.GZ at %s" % j3m_name
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
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
		uv_task.fail(status=412)
		return

	asset_path = "j3m_raw.json"
	media.addAsset(j3m, asset_path, as_literal=False)

	uv_task.put_next([
		"J3M.j3mify.j3mify",
		"J3M.massage_j3m.massageJ3M",
		"PGP.verify_signature.verifySignature",
		"J3M.verify_visual_content.verifyVisualContent"
	])

	uv_task.routeNext(inflate={'j3m_name' : asset_path})	
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag

@celery_app.task
def j3mify(uv_task):
	task_tag = "J3MIFYING"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "j3mifying asset at %s" % uv_task.doc_id
	uv_task.setStatus(302)
	
	import os
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=uv_task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	j3m = media.loadAsset(uv_task.j3m_name)
	if j3m is None:
		error_message = "J3M IS NONE"
		print error_message
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(message=error_message)
		return
	
	import json
	print "JSSON HERE:"
	try:
		print type(j3m)
		j3m = json.loads(j3m)
	except Exception as e:
		print "\n\n************** J3MIFYING [WARN] ******************\n"
		print e
		print "json load once fail. trying again"

		print j3m

	if type(j3m) in [str, unicode]:
		try:
			j3m = json.loads(j3m)
		except Exception as e:
			print "\n\n************** J3MIFYING [WARN] ******************\n"
			print e
			print "json loads twice fail."

	print type(j3m)

	try:
		j3m_sig = j3m['signature']
	except Exception as e:
		print "NO SIGNATURE TO EXTRACT"
		print "\n\n************** J3MIFYING [ERROR] ******************\n"
		uv_task.fail(status=412, message="No Signature in J3M.")
		return
	
	media.addAsset(j3m_sig, "j3m.sig", tags=[ASSET_TAGS['SIG']],
		description="The j3m's signature")
	
	media.addFile(
		media.addAsset(j3m['j3m'], "j3m.json", tags=[ASSET_TAGS['J3M']], description="The j3m itself.", as_literal=False), 
		None, sync=True)

	media.addCompletedTask(uv_task.task_path)
	
	uv_task.j3m_name = "j3m.json"
	uv_task.save()
	
	uv_task.routeNext()	
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag