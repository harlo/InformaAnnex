from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def get_vector(uv_task):
	task_tag = "IMAGE: GETTING VECTOR"

	print "\n\n************** %s [START] ******************\n" % task_tag
	uv_task.setStatus(302)

	from lib.Worker.Models.uv_document import UnveillanceDocument
	from vars import ASSET_TAGS
	from conf import ANNEX_DIR, DEBUG
	
	import os, pypuzzle

	image = UnveillanceDocument(_id=uv_task.doc_id)
	hi_res = image.getAssetsByTagName(ASSET_TAGS['HIGH'])
	
	if hi_res is None:
		error_msg = "Could not find the hi-res clone"

		print error_msg
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		
		uv_task.fail(message=error_msg)
		return

	hi_res = os.path.join(ANNEX_DIR, image.base_path, hi_res[0]['file_name'])
	puzz = pypuzzle.Puzzle()

	if DEBUG:
		print "generate puzzle vector from %s" % hi_res

	try:
		cvec = puzz.get_cvec_from_file(hi_res)
	except Exception as e:
		error_msg = "Could not get image vector because %s" % e

		print error_msg
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		
		uv_task.fail(message=error_msg)
		return

	if not image.addAsset(cvec, "image_cvec.json", as_literal=False, tags=[ASSET_TAGS['IMAGE_CVEC']]):
		error_msg = "could not save cvec asset!"

		print error_msg
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		
		uv_task.fail(message=error_msg)
		return

	print "\n\n************** %s [END] ******************\n" % task_tag
	uv_task.finish()
