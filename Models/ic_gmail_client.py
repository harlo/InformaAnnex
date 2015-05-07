class InformaCamGmailClient(InformaCamClient):
	def __init__(self, mode=None):
		credentials = None
		super(InformaCamGmailClient, self).__init__(mode, tag="gmail")

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

		self.service = build('gmail', 'v1', http=http)

		if mode is not None:
			q = {
				'userId' : "me",
				'q' : "after:%s" % yesterday
			}

			print q

			try:
				files = self.service.users().messages().list(**q).execute()
				# set files manifest for email
			except Exception as e:
				if DEBUG:
					print "BAD SERVICE CONNECTION"
					print e, type(e)

