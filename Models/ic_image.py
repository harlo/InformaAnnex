from lib.Worker.Models.ic_media import InformaCamMedia

class InformaCamImage(InformaCamMedia):
	def __init__(self, _id=None, inflate=None):
		super(InformaCamImage, self).__init__(_id=_id, inflate=inflate)

	def pull_metadata(self):
		from conf import getConfig, ANNEX_DIR

		try:
			J3M_DIR = getConfig('jpeg_tools_dir')
		except Exception as e:
			if DEBUG: 
				print "NO J3M DIR! %s" % e
			return False

		import re, os
		from subprocess import Popen, PIPE
		from cStringIO import StringIO
		
		from vars import UPLOAD_RESTRICTION
		from conf import DEBUG

		tiff_txt = StringIO()
	
		obscura_marker_found = False
		was_encrypted = False
		ic_j3m_txt = None
		
		cmd = [os.path.join(J3M_DIR, "j3mparser.out"), os.path.join(ANNEX_DIR, self.file_name)]
		
		p = Popen(cmd, stdout=PIPE, close_fds=True)
		data = p.stdout.readline()
		while data:
			data = data.strip()
					
			if re.match(r'^file: .*', data): pass
			elif re.match(r'^Generic APPn .*', data): pass
			elif re.match(r'^Component.*', data): pass
			elif re.match(r'^Didn\'t find .*', data): pass
			elif re.match(r'^Got obscura marker.*', data):
				if DEBUG:
					print "\n\nWE ALSO HAVE J3M DATA\n\n"
				
				obscura_marker_found = True
				ic_j3m_txt = StringIO()
			else:
				if obscura_marker_found:
					ic_j3m_txt.write(data)
				else:
					tiff_txt.write(data)
					
			data = p.stdout.readline()
			
		p.stdout.close()
		
		self.addAsset(tiff_txt.getvalue(), "file_metadata.txt",
			description="tiff metadata as per jpeg redaction library")
		
		tiff_txt.close()
		del tiff_txt
		
		if ic_j3m_txt is not None:
			asset_path = self.addAsset(ic_j3m_txt.getvalue(), "j3m_raw.txt")

			if asset_path is None:
				print "COULD NOT MAKE ASSET"
				return False

			return True, True

		else:
			print "NO IC J3M TEXT FOUND???"
			return True, False

		return False


	def get_image_hash(self):
		import os, re
		from subprocess import Popen, PIPE
		from conf import ANNEX_DIR, getConfig

		cmd = ["java", "-jar", 
			os.path.join(getConfig('jpeg_tools_dir'), "JavaMediaHasher.jar"),
			os.path.join(ANNEX_DIR, self.file_name)]

		p = Popen(cmd, stdout=PIPE, close_fds=True)
		verified_hash = p.stdout.readline().strip().replace("MD5=", "")
		p.stdout.close()

		if not re.match(r'[a-zA-A0-9]{32}', verified_hash):
			print "NO MD5 FOUND SORRY"
			return False

		self.verified_hash = verified_hash
		self.save()
		return True

	def get_image_vector(self):
		import os, pypuzzle
		from vars import ASSET_TAGS
		from conf import ANNEX_DIR, DEBUG

		hi_res = self.getAssetsByTagName(ASSET_TAGS['HIGH'])
	
		if hi_res is None:
			hi_res = self.file_name
		else:
			hi_res = os.path.join(self.base_path, hi_res[0]['file_name'])

		hi_res = os.path.join(ANNEX_DIR, hi_res)
		puzz = pypuzzle.Puzzle()

		if DEBUG:
			print "generate puzzle vector from %s" % hi_res

		try:
			cvec = puzz.get_cvec_from_file(hi_res)

			if not self.addAsset(cvec, "image_cvec.json", as_literal=False, tags=[ASSET_TAGS['IMAGE_CVEC']]):
				error_msg = "could not save cvec asset!"
				print error_msg
			else:
				return True
				
		except Exception as e:
			error_msg = "Could not get image vector because %s" % e
			print error_msg

		return False

