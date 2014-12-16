from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def generate_csv(uv_task):
	task_tag = "GENERATING CSV"

	print "\n\n************** %s [START] ******************\n" % task_tag
	uv_task.setStatus(302)

	for req in ["documents", "query"]:
		if not hasattr(uv_task, req):
			error_msg = "do not have %s for clustering" % req

			print error_msg
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			
			uv_task.fail(message=error_msg)
			return

	if type(uv_task.documents) in [str, unicode]:
		uv_task.documents = [uv_task.documents]

	from vars import ASSET_TAGS

	csv_asset = uv_task.addAsset(None, "cluster_%s.csv" % uv_task._id, tags=[ASSET_TAGS['C_RES']])

	if csv_asset is None:
		error_msg = "Could not create asset for cluster"

		print error_msg
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		
		uv_task.fail(message=error_msg)
		return

	import csv
	from json import di=umps

	from conf import DEBUG
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from lib.Worker.Models.ic_j3m import InformaCamJ3M

	with open(csv_asset, 'wb+') as C:
		csv_writer = csv.writer(C, quotechar='|', quoting=csv.QUOTE_MINIMAL)
		csv_writer.writerow([''].extend(query.keys()))

		for d, doc in enumerate(uv_task.documents):
			row = [str(d)].extend(['' for k in query.keys()])
			doc = UnveillanceDocument(_id=doc)

			for k, key in enumerate(query.keys()):
				key = key.split(".")
				if DEBUG:
					print key
				
				use_doc = None
				if hasattr(doc, key[0]):
					use_doc = doc
				else:
					if not hasattr(doc, "j3m_id"):
						print "No J3M for this document"
						print "\n\n************** %s [WARN] ******************\n" % task_tag
						continue

					use_doc = InformaCamJ3M(_id=doc.j3m_id)

				if use_doc is None:
					continue

				val = use_doc
				for x in key:
					if DEBUG:
						print "start on %s" % x
						print " which is %s" % val

					val = val[x]

					if DEBUG:
						print "now val is"
						print val

				row[k + 1] = str(val)

			csv_writer.writerow(row)

	print "\n\n************** %s [END] ******************\n" % task_tag
	uv_task.finish()