from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def locate_j3m(uv_task):
	task_tag = "PULLING J3M"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "pulling j3m at %s" % uv_task.doc_id
	uv_task.setStatus(302)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=uv_task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	from lib.Worker.Utils.funcs import getFileType
	from vars import MIME_TYPES, MIME_TYPE_MAP

	ic_j3m_txt = media.loadAsset("j3m_raw.txt")
	ic_j3m_txt_mime_type = getFileType(ic_j3m_txt, as_buffer=True)
	inflate = {}

	print "J3M MIME TYPE SNIFFED: %s" % ic_j3m_txt_mime_type

	if ic_j3m_txt_mime_type != MIME_TYPES['json']:
		import os
		from lib.Core.Utils.funcs import b64decode
		
		un_b64 = b64decode(ic_j3m_txt)
	
		if un_b64 is not None:
			un_b64_mime_type = getFileType(un_b64, as_buffer=True)
			if un_b64_mime_type in [MIME_TYPES['pgp'], MIME_TYPES['gzip']]:
				if DEBUG:
					print "MIME TYPE: %s" % un_b64_mime_type
				
				asset_path = "j3m_raw.%s" % MIME_TYPE_MAP[un_b64_mime_type]
				media.addAsset(un_b64, asset_path)
				
				if DEBUG:
					print "\n\nPGP KEY FILE PATH: %s\n\n" % asset_path
				
				gz = media.addAsset(None, "j3m_raw.gz", tags=[ASSET_TAGS['OB_M']], 
					description="j3m data extracted from obscura marker")
				
				if un_b64_mime_type == MIME_TYPES['pgp']:
					uv_task.put_next([
						"PGP.decrypt.decrypt",
						"J3M.j3mify.parse_zipped_j3m"
					])

					inflate.update({
						'pgp_file' : os.path.join(media.base_path, asset_path),
						'save_as' : gz
					})
					
					was_encrypted = True
					
				elif un_b64_mime_type in MIME_TYPES['gzip']:
					uv_task.put_next("J3M.j3mify.parse_zipped_j3m")
				
	else:
		from fabric.api import settings, json
		with settings(warn_only=True):
			local("mv %s %s" % (os.path.join(media.base_path, ".data", "j3m_raw.txt"),
				os.path.join(media.base_path, ".data", "j3m_raw.json")))

		uv_task.put_next([
			"J3M.j3mify.j3mify",
			"J3M.massage_j3m.massageJ3M",
			"PGP.verify_signature.verifySignature",
			"J3M.verify_visual_content.verifyVisualContent"
		])
		
		inflate.update({'j3m_name' : "j3m_raw.json"})

	media.addCompletedTask(uv_task.task_path)
	uv_task.routeNext(inflate=inflate)
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag