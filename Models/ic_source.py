from lib.Workers.Models.uv_object import UnveillanceObject

from conf import DEBUG

class InformaCamSource(UnveillanceDocument):
	def __init__(self, _id=None, inflate=None):
		if inflate is not None:
			if DEBUG: print "NEW SOURCE\n%s" % inflate
		
		super(InformaCamSource, self).__init__(_id=_id, inflate=inflate)