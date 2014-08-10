import json, copy, os
from time import time, sleep
from fabric.api import local, settings

from lib.Core.Utils.funcs import generateMD5Hash
from vars import MIME_TYPES, MIME_TYPE_MAP
from conf import getSecrets, ANNEX_DIR

class InformaCamClient(object):
	def __init__(self, mode, tag=None):
		self.mime_types = copy.deepcopy(MIME_TYPES)
		self.mime_type_map = copy.deepcopy(MIME_TYPE_MAP)
		self.config = getSecrets(key="repo")

		if tag is not None:
			self.tag = tag
		
		try:
			with open(self.config['absorbed_log'], 'rb') as log:
				self.absorbed_log = json.loads(log.read())
		except:
			self.absorbed_log = { 'sources': 0, 'submissions': 0 }
		
		self.mode = mode
		self.last_update_for_mode = self.absorbed_log[mode]
		self.usable = True
	
	def absorb(self, file):
		this_dir = os.getcwd()
		os.chdir(ANNEX_DIR)

		with settings(warn_only=True):
			if hasattr(self, 'tag'):
				local("git annex metadata %s --json --set=importer_source=%s" % (file, self.tag))

			local(".git/hooks/uv-post-netcat %s" % file)
		
		os.chdir(this_dir)
	
	def getFileNameHash(self, name_base):
		from conf import DOC_SALT
		return generateMD5Hash(content=name_base, salt=DOC_SALT)
	
	def updateLog(self, num_tries=0):
		if num_tries >= 10: return
		
		self.absorbed_log[self.mode] = self.last_update_for_mode
		try:
			with open(self.config['absorbed_log'], 'wb+') as log:
				log.write(json.dumps(self.absorbed_log))
		except IOError as e:
			num_tries += 1
			sleep(2)
			self.updateLog(num_tries)