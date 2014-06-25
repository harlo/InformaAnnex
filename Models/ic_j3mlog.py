from lib.Worker.Models.uv_batch import UnveillanceBatch

from conf import DEBUG
from vars import EmitSentinel

class InformaCamLog(UnveillanceBatch):
	def __init__(self, _id=None, inflate=None):
		if inflate is not None:
			if DEBUG: print "NEW LOG:\n%s" % inflate
	
		super(InformaCamLog, self).__init__(_id=_id, inflate=inflate, emit_sentinels=[
			EmitSentinel("j3m", "InformaCamJ3M", "_id")])