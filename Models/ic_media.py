from lib.Worker.Models.uv_document import UnveillanceDocument
from lib.Worker.Models.ic_j3m import InformaCamJ3M
from vars import EmitSentinel

class InformaCamMedia(UnveillanceDocument):
	def __init__(self, _id=None, inflate=None):
		emit_sentinels = [EmitSentinel("j3m", "InformaCamJ3M", None)]

		super(InformaCamMedia, self).__init__(_id=_id, inflate=inflate,
			emit_sentinels=emit_sentinels)
	
	def inflate(self, inflate):
		super(InformaCamMedia, self).inflate(inflate)
		
		if hasattr(self, "j3m_id"):
			self.j3m = InformaCamJ3M(_id=self.j3m_id)