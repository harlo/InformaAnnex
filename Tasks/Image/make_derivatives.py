from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def makeDerivatives(uv_task):
	task_tag = "DERIVATIVES: IMAGE"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "making derivatives for %s" % uv_task.doc_id
	uv_task.setStatus(302)
		
	from lib.Worker.Models.ic_image import InformaCamImage
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	image = InformaCamImage(_id=uv_task.doc_id)
	if image is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return
	
	import os, Image
	from conf import ANNEX_DIR
	
	resolutions = {
		'high' : None,
		'thumb' : [0.15, 0.15],
		'med' : [0.75, 0.75],
		'low' : [0.5, 0.5]
	}

	image.getFile(image.file_name)
	for label, res in resolutions.iteritems():
		asset_path = image.addAsset(None, "%s_%s.jpg" % (label, image.file_name),
			tags=[ASSET_TAGS['M_DERIV'], ASSET_TAGS[label.upper()]],
			description="derivative of image in %s resolution" % label)
			
		if asset_path is None:
			print "COULD NOT INIT THIS ASSET"
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			uv_task.fail()
			return

		image_obj = Image.open(os.path.join(ANNEX_DIR, image.file_name))
		if res is not None:
			resolution_tuple = tuple([int(x*y) for x, y in zip(res, list(image_obj.size))])
			if DEBUG:
				print "NEW DOWNSIZE RESOLUTION:"
				print resolution_tuple

			image_obj = image_obj.resize(resolution_tuple)

		image_obj.save(os.path.join(ANNEX_DIR, asset_path), "JPEG")
		image.addFile(asset_path, None, sync=True)
	
	image.addCompletedTask(uv_task.task_path)
	uv_task.routeNext()
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag