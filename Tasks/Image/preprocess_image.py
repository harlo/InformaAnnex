from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def preprocessImage(task):
	task_tag = "IMAGE PREPROCESSING"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(302)
		
	from lib.Worker.Models.ic_image import InformaCamImage
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	image = InformaCamImage(_id=task.doc_id)
	if image is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return

	image.get_image_hash()
	image.get_image_vector()
	image.update_similar_media()
	
	try:
		res, has_j3m = image.pull_metadata()
	except Exception as e:
		print e, type(e)

	if not res:
		print "COULD NOT PULL METADATA"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	if has_j3m:
		task.put_next("J3M.locate_j3m.locate_j3m")

		try:
			upload_restriction = image.getFileMetadata('uv_restriction')
		except Exception as e:
			print "could not get metadata for uv_restriction"
			print e
	else:
		print "\n\n************** %s [WARN] ******************\n" % task_tag
		upload_restriction = UPLOAD_RESTRICTION['for_local_use_only']

		# if image is a dopelganger, set a forwarder on it
		image.set_media_alias()

	if upload_restriction is None or upload_restriction == UPLOAD_RESTRICTION['no_restriction']:
		task.put_next("Image.make_derivatives.makeDerivatives")

	image.addCompletedTask(task.task_path)
	
	task.routeNext()
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag