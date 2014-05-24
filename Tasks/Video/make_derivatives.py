from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def makeDerivatives(task):
	task_tag = "DERIVATIVES: VIDEO"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "image preprocessing at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.ic_video import InformaCamVideo
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	video = InformaCamVideo(_id=task.doc_id)
	if video is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	import os
	from subprocess import Popen
	
	resolutions = {
		'high' : None,
		'med' : [0.75, 0.75],
		'low' : [0.5, 0.5]
	}
	
	for label, res in resolutions.iteritems():
		asset_path = video.addAsset(None, "%s_%s" % (label, video.file_name),
			tags=[ASSET_TAGS['M_DERIV'], ASSET_TAGS[label.upper()]],
			description="derivative of video in %s resolution (mp4)" % label)
			
		if asset_path is None:
			print "COULD NOT INIT THIS ASSET"
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			return
			
		if res is not None:
			cmd = ["ffmpeg", "-y", "-i", os.path.join(ANNEX_DIR, video.file_name),
				"-filter:v", "scale=%d:%d" % (res[0], res[1]),
				"-acodec", "copy", asset_path]
		else:
			cmd = ["cp", os.path.join(ANNEX_DIR, video.file_name), asset_path]
		
		p = Popen(cmd)
		p.wait()
		video.addFile(asset_path, None, sync=True)
		
		ogv_asset_path = video.addAsset(None, asset_path.replace(".mp4", ".ogv"),
			tags=[ASSET_TAGS['M_DERIV'], ASSET_TAGS[label.upper()]],
			description="derivative of video in %s resolution (ogv)" % label)
		
		if ogv_asset_path is not None:
			p = Popen(["ffmpeg2theora", asset_path])
			p.wait()
			
			video.addFile(ogv_asset_path, None, sync=True)
	
	asset_path = video.addAsset(None, "thumb_%s.jpg" % video.file_name[:-4],
		tags=[ASSET_TAGS['M_DERIV'], ASSET_TAGS['THUMB']],
		description="derivative of video in thumb resolution")
	
	if asset_path is not None:
		cmd = ["ffmpeg", "-y", "-i", os.path.join(ANNEX_DIR, video.file_name),
			"-f", "image2", "-ss", "0.342", "-vframes", "1", asset_path]
	
		p = Popen(cmd)
		p.wait()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag