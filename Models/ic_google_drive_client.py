import httplib2, json, os, re
from subprocess import Popen

from apiclient import errors
from apiclient.discovery import build

from Models.ic_client import InformaCamClient

from conf import DEBUG, ANNEX_DIR, getSecrets

class InformaCamDriveClient(InformaCamSyncClient):
	def __init__(self, mode=None):
		credentials = None
		
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
		self.setInfo()
		
		if mode is not None:
			InformaCamClient.__init__(self, mode)
			
			self.mime_types['folder'] = "application/vnd.google-apps.folder"
			self.mime_types['file'] = "application/vnd.google-apps.file"
			
			try:
				files = self.service.children().list(
					folderId=self.config['asset_root']).execute()
				
				self.files_manifest = [self.getFile(f['id']) for f in files['items']]
		
			except errors.HttpError as e:
				if DEBUG: print e
			
	def setInfo(self):
		print "setting user info"
	
	def getAssetMimeType(self, fileId):
		return self.getFile(fileId)['mimeType']
	
	def lockFile(self, file):
		if type(file) is str or type(file) is unicode:
			return self.lockFile(self.getFile(file))
		
		pass
	
	def listAssets(self, omit_absorbed=False):
		assets = []
		files = None
		q = { 'q' : 'sharedWithMe' }
		
		try:
			files = self.service.files().list(**q).execute()
		except errors.HttpError as e:
			if DEBUG: print e
			return False
		
		for f in files['items']:
			if f['mimeType'] not in self.mime_types.itervalues() or f['mimeType'] == self.mime_types['folder']: continue
			
			if omit_absorbed and self.isAbsorbed(f['id'], f['mimeType']): continue
			
			if DEBUG: print "INTAKE: %s (mime type: %s)" % (f['id'], f['mimeType'])
			
			try:
				clone = self.service.files().copy(
					fileId=f['id'], body={'title':f['id']}).execute()
				if DEBUG: print clone
				
				assets.append(clone['id'])
				sleep(2)
			except errors.HttpError as e:
				print e
				continue
		
		self.last_update_for_mode = time() * 1000
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
			return self.absorb(self.getFile(file))
		
		self.files_manifest.append(file)
	
	def getFileName(self, file):
		if type(file) is str or type(file) is unicode:
			return self.getFileName(self.getFile(file))
					
		return str(file['title'])
	
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
		# don't waste my time.
		if DEBUG: print "HAAAAAAAY DOWNLOAD FIRST!"
		
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
		
	def authenticate(self, auth_token=None):
		if auth_token is None:
			from oauth2client.client import OAuth2WebServerFlow
			
			self.flow = OAuth2WebServerFlow(
				self.config['client_id'], self.config['client_secret'],
				self.config['scopes'], 
				"http://localhost:%d%s" % (API_PORT, self.config['redirect_uri']))

			return self.flow.step1_get_authorize_url()
		else:
			credentials = self.flow.step2_exchange(auth_token)

			auth_storage = os.path.join(INFORMA_CONF_ROOT, "drive.secrets.json")
			
			from oauth2client.file import Storage
			Storage(auth_storage).put(credentials)
			
			self.config.update({
				'auth_storage' : auth_storage,
				'account_type' : "user"
			})
			
			sync_config = getSecrets(key="informacam.sync")
			sync_config['google_drive'].update(self.config)
			saveSecret("informacam.sync", sync_config)
			
			del self.flow
			return True
		
		return False