from lib.Workers.Models.uv_batch import UnveillanceBatch

from conf import DEBUG

class InformaCamLog(UnveillanceBatch):
	def __init__(self, _id=None, inflate=None):
		if inflate is not None:
			if DEBUG: print "NEW LOG:\n%s" % inflate
	
		super(InformaCamLog, self)__init__(_id=_id, inflate=inflate)