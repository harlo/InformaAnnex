import os, json, gnupg, re, yaml, gzip
import xml.etree.ElementTree as ET

from sys import exit, argv
from base64 import b64encode
from cStringIO import StringIO
from time import sleep
from fabric.api import local, settings
from fabric.operations import prompt

def gzipFile(path):
	_out = StringIO()
	_in = open(path)
	
	z = gzip.GzipFile(fileobj=_out, mode='w')
	z.write(_in.read())
	
	z.close()
	_in.close()
	
	return _out.getvalue()

def initForms(forms):
	jr_sentinel = "jr:itext('"
	parse = {"forms" : []}

	for form in [f for f in forms if re.match(r'.*\.xml', f)]:
		print "evaluating form %s" % form
		
		try:
			xmldoc = ET.parse(form)
		except Exception as e:
			print "form at %s invalid. (error %s)" % (form, e)
			continue

		root = xmldoc.getroot()
		translation = None
	
		mapping = {
			"mapping" : [],
			"audio_form_data" : []
		}
	
		# actual text mapping for objects is in the head (root[0]) at head.model.itext.translation
		for el in root[0][1]:
			if re.match(r'{.*}itext', el.tag):
				translation = el[0]
	
		# bindings are described in body (root[1]) at body
		for model_item in root[1]:
			map = None
			# if tag is select, select1, or upload
			if re.match(r'{.*}(select|select1)', model_item.tag):
				# get the binding by drilling down
				map = {}
				tag = model_item.attrib['bind']
				bindings = []
				for mi in model_item:
					if re.match(r'{.*}item', mi.tag):
						key = None
						value = None
						for kvp in mi:
							if re.match(r'{.*}label', kvp.tag):
								key = kvp.attrib['ref'][len(jr_sentinel):-2]
							elif re.match(r'{.*}value', kvp.tag):
								value = kvp.text
								for t in translation:
									if key == t.attrib['id']:
										key = t[0].text
										break

						if key is not None and value is not None:
							bindings.append({ value : key })
				map[tag] = bindings
					
			elif re.match(r'{.*}upload', model_item.tag):
				mapping['audio_form_data'].append(model_item.attrib['bind'])
		
			if map is not None:
				mapping['mapping'].append(map)

		if len(mapping['mapping']) == 0:
			del mapping['mapping']
	
		if len(mapping['audio_form_data']) == 0:
			del mapping['audio_form_data']
			
		if len(mapping.keys()) != 0:
			# get the namespace for this form from head (root[0]) head.title
			for el in root[0]:
				if re.match(r'{.*}title', el.tag):
					mapping['namespace'] = el.text
					break
		
			parse['forms'].append(mapping)
			print mapping
	
	print parse
	return parse

def validateRepository(repo=None):
	repos = ['google_drive', 'globaleaks']
	
	for r in repos:
		if repo is None:
			use_repo = prompt("Create %s repository? y or n\n[DEFAULT: n]" % r)
			if use_repo == "y":
				repo = { 'source' : r }
		
		if repo is None or repo['source'] != r:
			continue
		
		if 'asset_id' not in repo.keys():
			repo['asset_id'] = prompt("Repo Asset ID: ")

		if 'absorbed_log' not in repo.keys(): 
			repo['absorbed_log'] = os.path.join(os.getcwd(), "lib", 
				"Annex", ".monitor", "absorbedBy%s.txt" % repo['source'])
		
		if 'absorbed_flag' not in repo.keys():
			repo['absorbed_flag'] = "absorbedByInformaCam"
		
		if r == "google_drive":
			repo['scopes'] = [
				"https://www.googleapis.com/auth/drive",
				"https://www.googleapis.com/auth/drive.file",
				"https://www.googleapis.com/auth/drive.install",
				"https://www.googleapis.com/auth/userinfo.profile"
			]
			
			if 'account_type' not in repo.keys():
				repo['account_type'] = prompt("What account type?\n'service' or 'user'?")
			else:
				print "Account type: %s" % repo['account_type']
				
			if repo['account_type'] == "service":
				if 'p12' not in repo.keys():
					repo['p12'] = prompt("Path to p12 for account:")
				
				if 'client_secrets' not in repo.keys():
					repo['client_secrets'] = prompt("Path to client secrets:")
					
			elif repo['account_type'] == "user":
				repo['client_email'] = repo['asset_id']
				repo['redirect_url'] = "urn:ietf:wg:oauth:2.0:oob"
				
				if 'client_id' not in repo.keys():
					repo['client_id'] = prompt("Client ID:")
				
				if 'client_secret' not in repo.keys():
					repo['client_secret'] = prompt("Client Secret:")
				
				if 'auth_storage' not in repo.keys():
					from oauth2client.client import OAuth2WebServerFlow
					from oauth2client.file import Storage
					
					print "To use Google Drive to import documents into the Annex server, you must authenticate the application by visiting the URL below."
					print "You will be shown an authentication code that you must paste into this terminal when prompted."					
					
					repo['auth_storage'] = os.path.join(os.getcwd(), "lib", 
						"Annex", "conf", "drive.secrets.json")
						
					flow = OAuth2WebServerFlow(repo['client_id'], repo['client_secret'], repo['scopes'], repo['redirect_url'])
					
					print "URL: %s" % flow.step1_get_authorize_url()
					credentials = flow.step2_exchange(prompt("Code: "))
					Storage(repo['auth_storage']).put(credentials)

			repo['public_url'] = "https://drive.google.com"
			
		elif r == "globaleaks":
			repo['context_gus'] = repo['asset_id']

			if 'host' not in repo.keys():
				repo['host'] = prompt("Globaleaks Host: ")
			
			if 'asset_root' not in repo.keys():
				repo['asset_root'] = prompt("Globaleaks Asset Root: ")
			
			if 'user' not in repo.keys():
				repo['user'] = prompt("Globaleaks User: ")

			if 'port' not in repo.keys():
				repo['port'] = prompt("Globaleaks ssh port: ")

			if len(repo['port']) == 0:
				repo['port'] = 22
			
			if 'public_url' not in repo.keys():
				repo['public_url'] = prompt("Globaleaks Public URL: ")

			if 'identity_file' not in repo.keys():
				repo['identity_file'] = prompt("Globaleaks Identity File (for ssh/rsync): ")
		
		return repo

if __name__ == "__main__":
	base_dir = os.getcwd()
	conf_dir = os.path.join(base_dir, "lib", "Annex", "conf")

	print "****************************************"

	sec_config = {}
	if len(argv) == 2 and len(argv[1]) > 3:
		try:
			with open(argv[1], 'rb') as CONFIG: sec_config.update(json.loads(CONFIG.read()))
		except Exception as e: pass
	else:
		try:
			with open(os.path.join(conf_dir, "unveillance.secrets.json"), 'rb') as SECRETS:
				sec_config.update(json.loads(SECRETS.read()))
		except Exception as e:
			print "no config file found.  please fill out the following:"
		
	if 'org_name' not in sec_config.keys():
		sec_config['org_name'] = prompt("Organization Name:")
	
	if 'org_details' not in sec_config.keys():
		sec_config['org_details'] = prompt("Organization Details:")
	
	try:
		repo = sec_config['repo']
	except KeyError as e:
		repo = None
	
	sec_config['repo'] = validateRepository(repo=repo)
	
	if 'gpg_dir' not in sec_config.keys():
		sec_config['gpg_dir'] = prompt(
			"Where is your GPG home dir?\n[DEFAULT: %s]" % os.path.join(base_dir,
				".gnupg"))
				
	if len(sec_config['gpg_dir']) == 0 :
		sec_config['gpg_dir'] = os.path.join(base_dir, ".gnupg")

	if 'gpg_priv_key' not in sec_config.keys():
		sec_config['gpg_priv_key'] = prompt(
			"Where is your PRIVATE GPG key?\nIf you don't have one, press enter.")
	
	sec_config['gpg_pub_key'] = os.path.join(conf_dir, "gpg_pub_key.pub")
	
	rm_key = False
	
	if len(sec_config['gpg_priv_key']) == 0:
		rm_key = True
		sec_config['gpg_priv_key'] = os.path.join(conf_dir, "gpg_priv_key.sec")
		sec_config['gpg_pwd'] = prompt("Enter your passphrase for your GPG key:")
		with open(os.path.join(base_dir, "ickeygen"), 'wb+') as KEYGEN:
			KEYGEN.write("Key-Type:RSA\n")
			KEYGEN.write("Key-Length:4096\n")
			KEYGEN.write("Name-Real:%s\n" % sec_config['org_name'])
			KEYGEN.write("Name-Comment:%s\n" % sec_config['org_details'])
			KEYGEN.write("Name-Email:%s\n" % sec_config['repo']['asset_id'])
			KEYGEN.write("Passphrase:%s\n" % sec_config['gpg_pwd'])
			KEYGEN.write("%%secring %s\n" % sec_config['gpg_priv_key'])
			KEYGEN.write("%%pubring %s\n" % sec_config['gpg_pub_key'])
			
		with settings(warn_only=True):
			local("gpg --batch --gen-key %s" % os.path.join(base_dir, "ickeygen"))
			local("rm %s" % os.path.join(base_dir, "ickeygen"))
			sleep(5)

	if 'gpg_pwd' not in sec_config.keys():
		sec_config['gpg_pwd'] = prompt("What is the password to your GPG key?")
		
	gpg = gnupg.GPG(homedir=sec_config['gpg_dir'])
	with open(sec_config['gpg_priv_key'], 'rb') as PRIV_KEY:
		import_result = gpg.import_keys(PRIV_KEY.read())
		sec_config['org_fingerprint'] = import_result.results[0]['fingerprint']
	
		with settings(warn_only=True):
			local(
			"gpg --export --secret-keyring %s -a > %s.asc" % (sec_config['gpg_priv_key'],
				sec_config['gpg_pub_key']))

			sec_config['gpg_pub_key'] += ".asc"
	
	if rm_key:
		with settings(warn_only=True):
			local("rm %s" % sec_config['gpg_priv_key'])
	
	'''
		make an ictd and put it in our annex.  does not need to be indexed.
	'''
	ictd = {
		'publicKey' : b64encode(gzipFile(sec_config['gpg_pub_key'])),
		'organizationName' : sec_config['org_name'],
		'organizationDetails' : sec_config['org_details'],
		'organizationFingerprint' : sec_config['org_fingerprint'],
		'forms' : []
	}

	forms_root = None
	if 'forms_root' not in sec_config.keys():
		forms_root = prompt("If your ICTD contains forms, enter the folder where they are found.\nIf you don't have any forms, just press enter.")
		if len(forms_root) == 0:
			forms_root = None
	else:
		forms_root = sec_config['forms_root']
	
	if forms_root is not None:
		for _, _, files in os.walk(forms_root):
			for file in files:
				ictd['forms'].append(b64encode(gzipFile(os.path.join(forms_root, file))))
				
			with open(os.path.join(forms_root, "forms.json"), 'wb+') as FORMS:
				forms = [os.path.join(forms_root, f) for f in files]
				print forms
				
				FORMS.write(json.dumps(initForms(forms)))
			
			break

	try:
		ictd['repositories'] = [{
			'source' : sec_config['repo']['source'],
			'asset_id' : sec_config['repo']['asset_id'],
			'asset_root' : sec_config['repo']['public_url']
		}]

	except Exception as e:
		print e
		pass

	from lib.Annex.conf import ANNEX_DIR
	with open(os.path.join(ANNEX_DIR, "ictd.json"), 'wb+') as ICTD:
		ICTD.write(json.dumps(ictd))
	
	os.chdir(ANNEX_DIR)
	with settings(warn_only=True):
		local("git annex add ictd.json")
	os.chdir(base_dir)

	with open(os.path.join(conf_dir, "annex.config.yaml"), 'ab') as CONFIG:
		CONFIG.write("jpeg_tools_dir: %s\n" % os.path.join(base_dir, "lib", "jpeg"))	
		CONFIG.write("informacam.forms_root: %s\n" % forms_root)
		CONFIG.write("vars_extras: %s\n" % os.path.join(base_dir, "vars.json"))
		CONFIG.write("gpg_homedir: %s\n" % sec_config['gpg_dir'])

		with settings(warn_only=True):
			CONFIG.write("puzzle_diff: %s\n" % local("which puzzle-diff", capture=True))
	
	with open(os.path.join(conf_dir, "unveillance.secrets.json"), 'wb+') as SECRETS:
		SECRETS.write(json.dumps(sec_config))
	
	initial_tasks = []
	
	try:
		with open(os.path.join(conf_dir, "initial_tasks.json"), 'rb') as I_TASKS:
			initial_tasks.extend(json.loads(I_TASKS.read()))
	except IOError as e: pass
		
	initial_tasks.append({
		'task_path' : "Intake.intake.doIntake",
		'queue' : os.getenv('UV_UUID'),
		'persist' : 3
	})
	
	with open(os.path.join(conf_dir, "initial_tasks.json"), 'wb+') as I_TASKS:
		I_TASKS.write(json.dumps(initial_tasks))
		
	exit(0)