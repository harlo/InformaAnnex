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

	def reset(self):
		for r in ['media_verified', 'j3m_verified', 'verified_hash']:
			if hasattr(self, r):
				delattr(self, r)

		'''
		from lib.Worker.Models.ic_media import InformaCamMedia
		i = InformaCamMedia(_id="b00957d3a27b8cfa0306fa7ddb01557e515056e7")
		'''

		super(InformaCamMedia, self).reset()

	def emit(self, remove=None):
		e = super(InformaCamMedia, self).emit(remove=remove)
		e['provenance'] = self.get_provenance()
		return e

	def get_provenance(self):
		for p in ['media_verified', 'j3m_verified']:
			if not hasattr(self, p):
				if DEBUG:
					print "Media item has no key %s" % p

				return False

			if type(getattr(self, p)) is not bool:
				if DEBUG:
					print "Media.%s is False" % p
				return False

		return self.media_verified and self.j3m_verified

	def add_media_reference(self, _id):
		if not hasattr(self, "media_references"):
			self.media_references = []

		if _id not in self.media_references:
			self.media_references.append(_id)
			self.saveFields("media_references")

	def set_media_alias(self):
		similar_media = self.get_similar_media()
		if similar_media is None:
			return False

		try:
			media_alias = InformaCamMedia(_id=similar_media[0]['_id'])
			
			self.permanent_media_alias = media_alias._id
			self.saveFields("permanent_media_aliass")

			media_alias.add_media_reference(self._id)

			return True
		except Exception as e:
			print "PROBLEM SETTING MEDIA ALIAS:"
			print e, type(e)

		return False

	def update_similar_media(self):
		self.similar_media = self.get_similar_media()
		self.saveFields("similar_media")

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

		if similar_media and similar_media['count'] > 0:
			if DEBUG:
				print similar_media

			similar_media = [InformaCamMedia(_id=m['_id']) for m in similar_media['documents'] if m['_id'] != self._id]
			similar_media = [{ '_id' : m._id, 'provenance' : m.get_provenance()} for m in similar_media]
		
		try:
			return None if len(similar_media) is 0 else similar_media
		except Exception as e:
			print e, type(e)

		return None

	def set_j3m_comp(self):
		from vars import ASSET_TAGS

		j3m = self.loadAsset("j3m_raw.json")
		if j3m is None:
			return False

		try:
			j3m_compare = j3m[7:j3m.rfind("signature")-2]
			self.addAsset(j3m_compare, "j3m_compare.json", tags=[ASSET_TAGS['J3M_COMP']], 
				description="The j3m's original json for verification")
			return True
		except Exception as e:
			print "ERROR MAKING J3M COMP ASSET"
			print e, type(e)

		return False

	def verify_signature(self):
		sig = self.getAsset("j3m.sig", return_only="path")
		j3m = self.getAsset("j3m_compare.json", return_only="path")
		
		if DEBUG:
			print "j3m path: %s, sig path: %s" % (j3m, sig)
		
		if sig is None or j3m is None:
			err_msg = "NO SIGNATURE or J3M"
			print err_msg
			return False

		import gnupg, json
		from conf import getConfig
		
		try:
			gpg = gnupg.GPG(homedir=getConfig('gpg_homedir'))
		except Exception as e:
			print "ERROR INITING GPG"
			return False
		
		self.j3m_verified = False
		verified = gpg.verify_file(j3m, sig_file=sig)
		
		if DEBUG:
			print verified.stderr
			print "verified fingerprint: %s" % verified.fingerprint
		
		if verified.fingerprint is not None:
			from json import loads
			
			supplied_fingerprint = str(json.loads(
				self.loadAsset("j3m.json"))['genealogy']['createdOnDevice'])
			
			if verified.fingerprint.upper() == supplied_fingerprint.upper():
				if DEBUG:
					print "SIGNATURE VALID for %s" % verified.fingerprint.upper()
				
				self.j3m_verified = True
		
		self.saveFields("j3m_verified")
		return True
	



