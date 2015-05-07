from lib.Worker.Models.uv_document import UnveillanceDocument
from lib.Worker.Models.ic_j3m import InformaCamJ3M
from vars import EmitSentinel
from conf import DEBUG

class InformaCamMedia(UnveillanceDocument):
	def __init__(self, _id=None, inflate=None):
		emit_sentinels = [EmitSentinel("j3m", "InformaCamJ3M", None)]

		super(InformaCamMedia, self).__init__(_id=_id, inflate=inflate,
			emit_sentinels=emit_sentinels)
	
	def inflate(self, inflate):
		super(InformaCamMedia, self).inflate(inflate)
		
		if hasattr(self, "j3m_id"):
			self.j3m = InformaCamJ3M(_id=self.j3m_id)

	def update_similar_media(self):
		self.similar_media = self.get_similar_media()
		self.save()

	def get_similar_media(self):

		if not hasattr(self, "verified_hash"):
			if DEBUG:
				print "No verified hash yet."

			return

		GET_ALL_BY_HASH = {
			"bool" : {
				"must" : [
					{
						"match" : {
							"uv_document.verified_hash" : self.verified_hash
						}
					}
				]
			}
		}

		similar_media = self.query(GET_ALL_BY_HASH)

		if similar_media['count'] > 0:
			similar_media = [{ '_id' : m['_id'], \
				'provenance' : False if 'provenance' not in m.keys() else m['provenance']} \
				for m in similar_media['documents'] if m['_id'] != self._id]
		
		try:
			return None if len(similar_media) is 0 else similar_media
		except Exception as e:
			print e, type(e)

		return None



