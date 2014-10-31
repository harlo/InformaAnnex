import os, io, re

from fabric.api import *
from fabric.operations import get
from time import sleep, time, mktime, strptime
from datetime import datetime

from lib.Worker.Models.ic_client import InformaCamClient, InformaCamClientFabricProcess
from conf import DEBUG, ANNEX_DIR, getSecrets

def listGlobaleakAssets(asset_root, identity_file):
	cmd = "ssh -f -i %s %s 'sudo ls -la --full-time %s'" % (identity_file, env.host_string, asset_root)
	
	with settings(warn_only=True):
		try:
			asset_list = [a for a in local(cmd, capture=True).splitlines() if re.match(r'^total', a) is None and re.match(r'^drwx', a) is None]
			return [{'file_name' : a[-1], 'date_created' : " ".join([a[-4], a[-3]])} for a in [[b for b in c.split(' ') if b != ''] for c in asset_list]]
		except Exception as e:
			if DEBUG:
				print e
	
	return None

def getGlobaleaksAssetMimeType(file, asset_root, identity_file):
	cmd = "ssh -f -i %s %s 'sudo file --mime-type %s'" % (identity_file, 
		env.host_string, os.path.join(asset_root, file))

	with settings(warn_only=True):
		try:
			return local(cmd, capture=True).split(": ")[-1]
		except Exception as e:
			if DEBUG:
				print e

	return None

def downloadGlobaleaksAsset(file, asset_root, identity_file):
	u = env.host_string.split('@')[0]
	cmd = "ssh -f -i %s %s 'sudo cp %s /%s && sudo chown %s /%s'" % (identity_file,
		env.host_string, os.path.join(asset_root, file),
		os.path.join('home', u), "%(u)s:%(u)s" % ({'u' : u}),
		os.path.join('home', u, file))

	with settings(warn_only=True):
		local(cmd, capture=True)
		
		content = io.BytesIO()		
		env.key_filename = identity_file

		with cd("/%s" % os.path.join('home', u)):
			get(file, content)

		cmd = "ssh -f -i %s %s 'rm /%s'" % (identity_file,
			env.host_string, os.path.join('home', u, file))
		
		local(cmd, capture=True)
	
	return content

class InformaCamGlobaleaksClient(InformaCamClient):
	def __init__(self, mode=None):
		super(InformaCamGlobaleaksClient, self).__init__(mode, tag="globaleaks")

		print self.config
		
	def getAssetMimeType(self, file):
		mime_type = InformaCamClientFabricProcess(getGlobaleaksAssetMimeType,
			self.config['host'], self.config['user'], self.config['identity_file'], args={
				'file' : file, 
				'asset_root' : self.config['asset_root'],
				'identity_file' : self.config['identity_file']
			})

		mime_type.join()
		return mime_type.output
		
	def listAssets(self, omit_absorbed=False):
		assets = []

		list_gl_assets = InformaCamClientFabricProcess(listGlobaleakAssets, 
			self.config['host'], self.config['user'], self.config['identity_file'],
			args={ 'asset_root' : self.config['asset_root'], 'identity_file' : self.config['identity_file']})

		list_gl_assets.join()

		if list_gl_assets.error is None and list_gl_assets.output is not None:
			self.last_update_for_mode = time() * 1000

			# get mime types
			for l in list_gl_assets.output:
				mime_type = self.getAssetMimeType(l['file_name'])
				if mime_type is None:
					continue

				date_str = l['date_created'].split(".")[0]
				date_created = mktime(strptime(date_str, "%Y-%m-%d %H:%M:%S")) * 1000

				if DEBUG:
					print "MIME TYPE: %s" % mime_type
					print "DATE CREATED: %d" % date_created

				if omit_absorbed and self.isAbsorbed(date_created, mime_type):
					continue
						
				assets.append(l['file_name'])

		print assets
		return assets
	
	def isAbsorbed(self, date_created, mime_type):
		if self.mode == "sources":
			if mime_type != self.mime_types['zip']: return True
		elif self.mode == "submissions":
			if mime_type == self.mime_types['zip']: return True
		
		print "LAST ABSORBED: %d" % self.absorbed_log[self.mode]
		if date_created <= self.absorbed_log[self.mode]: return True

		return False
				
	def download(self, file, save_as=None, save=True, return_content=False):
		destination_path = None
		
		if save_as is None:
			save_as = file
		
		if len(re.findall(r'\.\.', save_as)) > 0:
			return None
		
		content = InformaCamClientFabricProcess(downloadGlobaleaksAsset,
			self.config['host'], self.config['user'], self.config['identity_file'], args={
				'file' : file,
				'asset_root' : self.config['asset_root'],
				'identity_file' : self.config['identity_file']
			})
		content.join()

		if content.output is None:
			return None

		destination_path = os.path.join(ANNEX_DIR, save_as)
		try:
			with open(destination_path, 'wb+') as C: C.write(content.output.getvalue())
		except IOError as e:
			if DEBUG: print e
			return None
		
		if return_content: return content.output.getvalue()
		else: return destination_path