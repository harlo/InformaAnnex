from time import sleep, time, mktime, strptime
from datetime import datetime

from lib.Worker.Models.ic_client import InformaCamClient
from conf import DEBUG, ANNEX_DIR, getSecrets

class InformaCamS3Client(InformaCamClient):
	def __init__(self, mode=None):
		super(InformaCamClient, self).__init__(mode, tag="s3bucket")

	def getAssetMimeType(self, file):
		return None

	def listAssets(self, omit_absorbed=False):
		assets = []

		return assets

	def isAbsorbed(self, date_created, mime_type):
		return False

	def download(self, file, save_as=None, save=True, return_content=False):
		return None