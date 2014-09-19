from Models.uv_els_stub import UnveillanceELSStub
from conf import DEBUG

class InformaCamJ3M(UnveillanceELSStub):
	def __init__(self, _id=None, inflate=None):
		if inflate is not None:
			from lib.Core.Utils.funcs import generateMD5Hash
			from conf import UUID
			from vars import UV_DOC_TYPE, MIME_TYPES
			
			inflate['_id'] = generateMD5Hash(content=inflate['media_id'],
				salt=MIME_TYPES['j3m'])

			inflate['farm'] = UUID
			inflate['uv_doc_type'] = UV_DOC_TYPE['DOC']
			inflate['mime_type'] = MIME_TYPES['j3m']
			
		super(InformaCamJ3M, self).__init__("ic_j3m", _id=_id, inflate=inflate)