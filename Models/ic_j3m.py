from Models.uv_object import UnveillanceObject
from vars import EmitSentinel
from conf import DEBUG

class InformaCamJ3M(UnveillanceObject):
	def __init__(self, _id=None, inflate=None):
		if inflate is not None:
			from lib.Core.Utils.funcs import generateMD5Hash
			from conf import UUID
			from vars import UV_DOC_TYPE
			
			inflate['_id'] = generateMD5Hash()
			inflate['farm'] = UUID
			inflate['uv_doc_type'] = UV_DOC_TYPE['J3M']
			
		super(InformaCamJ3M, self).__init__(_id=_id, inflate=inflate)
	
	def sendELSRequest(self, data=None, to_root=False, endpoint=None, method="get"):
		j3m_endpoint = "ic_j3m/"
		if endpoint is not None: j3m_endpoint += endpoint
		
		return super(InformaCamJ3M, self).sendELSRequest(data=data, 
			to_root=True, endpoint=j3m_endpoint, method=method)