import httplib2, json, os, re
from subprocess import Popen
from apiclient import errors
from apiclient.discovery import build
from time import sleep, time
from datetime import datetime

from lib.Worker.Models.ic_client import InformaCamClient
from conf import DEBUG, ANNEX_DIR, getSecrets

class InformaCamDriveClient(InformaCamClient):
	def __init__(self, mode=None):
		credentials = None
		super(InformaCamDriveClient, self).__init__(mode, tag="google_drive")

		last_update = datetime.fromtimestamp(int(self.last_update_for_mode/1000))
		self.last_update_for_mode_iso = last_update.isoformat()
		
		try:
			if self.config['account_type'] == "service":
				from oauth2client.client import SignedJwtAssertionCredentials
				
				try:
					with open(self.config['p12'], 'rb') as key:
						with open(self.config['client_secrets'], 'rb') as secrets:
							secrets = json.loads(secrets.read())
				
							credentials = SignedJwtAssertionCredentials(
								secrets['web']['client_email'], key.read(), 
								self.config['scopes'])

				except KeyError as e:
					print e
					print "cannot authenticate with service account."
			elif self.config['account_type'] == "user":
				from oauth2client.file import Storage	
				credentials = Storage(self.config['auth_storage']).get()
			
		except KeyError as e:
			if DEBUG: print "NO AUTH YET!"
		
		if credentials is None:
			self.usable = False
			return
				
		http = httplib2.Http()
		http = credentials.authorize(http)
		
		self.service = build('drive', 'v2', http=http)
		
		if mode is not None:
			self.mime_types['folder'] = "application/vnd.google-apps.folder"
			self.mime_types['file'] = "application/vnd.google-apps.file"

			q = {
				'q' : "modifiedDate <= '%s'" % self.last_update_for_mode_iso,
				'folderId' : self.config['asset_root'],
				'maxResults' : 500
			}

			print q
			
			try:
				files = self.service.children().list(**q).execute()
				
				self.files_manifest = [self.getFile(f['id']) for f in files['items']]
				print "\n***\nTHESE ARE THE FILES ALREADY ABSORBED IN %s" % self.config['asset_root']
				print len(self.files_manifest)
				print "OUR MODE: %s" % mode
				print self.mode
		
			except errors.HttpError as e:
				if DEBUG: print e
	
	def getAssetMimeType(self, fileId):
		return self.getFile(fileId)['mimeType']
	
	def listAssets(self, omit_absorbed=False):
		assets = []
		files = None
		q = { 'q' : 'sharedWithMe' }
		
		try:
			files = self.service.files().list(**q).execute()
		except errors.HttpError as e:
			if DEBUG: print e
			return False
		
		self.last_update_for_mode = time() * 1000

		for f in files['items']:
			if f['mimeType'] not in self.mime_types.itervalues() or f['mimeType'] == self.mime_types['folder']: continue
			
			if omit_absorbed and self.isAbsorbed(f['id'], f['mimeType']): continue
			
			if DEBUG: print "\nINTAKE: %s (mime type: %s)\n" % (f['id'], f['mimeType'])
			
			try:
				clone = self.service.files().copy(
					fileId=f['id'], body={
						'title':f['id'],
						'parents' : [{ 'id' : self.config['asset_root'] }],
						'description' : f['title']
					}).execute()
				if DEBUG: print "CLONE RESULT:\n%s" % clone
				
				assets.append(clone['id'])				
				sleep(2)
			except errors.HttpError as e:
				print e
				continue
		
		
		self.updateLog()
		
		if DEBUG:
			print "ASSETS TO BE ABSORBED FOR MODE %s" % self.mode
			print assets

		return assets
	
	def isAbsorbed(self, file_name, mime_type):
		if self.mode == "sources":
			if mime_type != self.mime_types['zip']: return True
		elif self.mode == "submissions":
			if mime_type == self.mime_types['zip']: return True
		
		for f in self.files_manifest:
			if f['title'] == file_name: return True
		
		return False
	
	def absorb(self, file):
		if type(file) is str or type(file) is unicode:
			self.absorb(self.getFile(file))
		
		print "***ABSORBING FILE:\n%s\n\n" % file
		self.files_manifest.append(file)
		super(InformaCamDriveClient, self).absorb(self.getFileName(file), file_alias=self.getFileAlias(file))
	
	def getFileName(self, file):
		if type(file) is str or type(file) is unicode:
			return self.getFileName(self.getFile(file))
					
		return str(file['title'])

	def getFileAlias(self, file):
		if type(file) is str or type(file) is unicode:
			return self.getFileAlias(self.getFile(file))
					
		return str(file['description'])
	
	def getFileNameHash(self, file):
		if type(file) is str or type(file) is unicode:
			return self.getFileName(self.getFile(file))
		
		name_base = file['id']
		return super(InformaCamDriveClient, self).getFileNameHash(name_base)
	
	def share(self, fileId, email=None):
		if not hasattr(self, "service"): return None
		if email is None: email = self.config['client_email']
		
		body = {
			'role' : "writer",
			'value' : email,
			'type' : "user"
		}
		
		try:
			return self.service.permissions().insert(fileId=fileId, body=body).execute()
		except errors.HttpError as e:
			if DEBUG: print e
		
		return None
		
	def upload(self, data, mime_type=None, as_binary=False, **body):
		if not hasattr(self, "service"): return None
		
		if not as_binary:
			try:
				with open(data, 'rb') as d: data = d.read()
			except IOError as e:
				if DEBUG: print e
				return False
		
		import io, sys
		from apiclient.http import MediaIoBaseUpload
		
		if mime_type is None:
			mime_type = "application/octet-stream"
			
		chunk_size = 1024*1024	# unless data is tiny. check first
		data = io.BytesIO(data)

		if sys.getsizeof(data) < chunk_size:
			chunk_size = -1
		
		media_body = MediaIoBaseUpload(data, mimetype=mime_type,
			chunksize=chunk_size, resumable=True)
		
		try:
			upload = self.service.files().insert(
				body=body, media_body=media_body).execute()
			
			return upload
		except errors.HttpError as e:
			if DEBUG: print e
		
		return None
	
	def getFile(self, fileId):
		if not hasattr(self, "service"): return None
		
		try:
			return self.service.files().get(fileId=fileId).execute()
		except errors.HttpError as e:
			if DEBUG: print e
		
		return None
	
	def download(self, file, save_as=None, save=True, return_content=False):		
		if not hasattr(self, "service"): return None
		if not save and not return_content: return None
		
		if type(file) is str or type(file) is unicode:
			return self.download(self.getFile(file))
		
		url = file.get('downloadUrl')
		if url:
			content = None
			destination_path = None
			
			if save_as is None:
				save_as = self.getFileName(file)
			
			# fuck you. (path traversal)
			if len(re.findall(r'\.\.', save_as)) > 0:
				return None
			
			from conf import ANNEX_DIR
			destination_path = os.path.join(ANNEX_DIR, save_as)
			
			response, content = self.service._http.request(url)
			if response.status != 200: return None
			
			try:
				with open(destination_path, 'wb+') as C: C.write(content)
			except IOError as e:
				if DEBUG: print e
				return None
					
			if return_content: return content
			else: return destination_path
		
		return None