from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def makeDerivatives(task):
	task_tag = "DERIVATIVES: IMAGE"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.ic_image import InformaCamImage
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	image = InformaCamImage(_id=task.doc_id)
	if image is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	from subprocess import Popen
	from conf import ANNEX_DIR
	
	resolutions = {
		'high' : None,
		'thumb' : [0.15, 0.15],
		'med' : [0.75, 0.75],
		'low' : [0.5, 0.5]
	}
	
	for label, res in resolutions.iteritems():
		asset_path = image.addAsset(None, "%s_%s" % (label, image.file_name),
			tags=[ASSET_TAGS['M_DERIV'], ASSET_TAGS[label.upper()]],
			description="derivative of image in %s resolution" % label)
			
		if asset_path is None:
			print "COULD NOT INIT THIS ASSET"
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			return
			
		cmd = ["ffmpeg", "-y", "-i", os.path.join(ANNEX_DIR, image.file_name)]
		if res is not None:
			cmd.extend(["-vf", "scale=iw*%.3f:ih*%.3f" % (res[0], res[1])])
		
		cmd.append(asset_path)
		
		p = Popen(cmd)
		p.wait()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag