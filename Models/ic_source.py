from lib.Worker.Models.uv_document import UnveillanceDocument

from conf import DEBUG

class InformaCamSource(UnveillanceDocument):
	def __init__(self, _id=None, inflate=None):
		if inflate is not None:
			if DEBUG: print "NEW SOURCE\n%s" % inflate
		
		super(InformaCamSource, self).__init__(_id=_id, inflate=inflate)
	
	def reverifyMedia(self):
		media = self.query()
		
		if media is None: 
			if DEBUG: print "NO DOCUMENTS FROM THIS SOURCE"
			return
		
		for m in media:
			m.j3m_verified = True
			m.save()