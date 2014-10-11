import os, io

from fabric.api import *
from fabric.operations import get
from time import sleep, time, mktime, strptime
from datetime import datetime

from lib.Worker.Models.ic_client import InformaCamClient
from conf import DEBUG, ANNEX_DIR, getSecrets

class InformaCamGlobaleaksClient(InformaCamClient):
	def __init__(self, mode=None):
		credentials = None
		super(InformaCamGlobaleaksClient, self).__init__(mode, tag="globaleaks")

		if credentials is None:
			self.usable = False
			return
		
	def getAssetMimeType(self, file):
		with cd(self.config['asset_root']):
			mime_type = run("file --mime-type %s" % file)
		
		return mime_type
		
	def listAssets(self, omit_absorbed=False):
		assets = []
		files = None
		
		# ssh into gl server
		with cd(self.config['asset_root']):
			ls_la = run("ls -la --full-time")
			self.last_update_for_mode = time() * 1000
		
		for l in ls_la:
			file = l
			mime_type = self.getAssetMimeType(file)
			
			# if not in mime types, continue
		
			# date_str = " ".join(ls[-4:-2]).split(".")[0]
			# date_created = mktime(strptime(date_str, "%Y-%m-%d %H:%M:%S"))
		
			# if omit_absorbed and self.isAbsorbed(date_created, mime_type): continue
			# if DEBUG: print "INTAKE: %s (mime type %s)" % (f, date_created)
		
			# assets.append(file)
		return assets
	
	def isAbsorbed(self, date_created, mime_type):
		if self.mode == "sources":
			if mime_type != self.mime_types['zip']: return True
		elif self.mode == "submissions":
			if mime_type == self.mime_type['zip']: return True
		
		if date_created <= self.absorbed_log[mode]: return True

		return False
				
	def download(self, file, save_as=None, save=True, return_content=False):
		content = io.BytesIO()
		destination_path = None
		
		if save_as is None: save_as = file
		
		if len(re.findall(r'\.\.', save_as)) > 0: return None
		
		with cd(self.config['asset_root']):
			get(file, content)
			if content is None: return None
		
		destination_path = os.path.join(ANNEX_DIR, save_as)
		try:
			with open(destination_path, 'wb+') as C: C.write(content.getvalue())
		except IOError as e:
			if DEBUG: print e
			return None
		
		if return_content: return content.getvalue()
		else: return destination_path