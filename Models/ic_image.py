from lib.Worker.Models.ic_media import InformaCamMedia

class InformaCamImage(InformaCamMedia):
	def __init__(self, _id=None, inflate=None):
		super(InformaCamImage, self).__init__(_id=_id, inflate=inflate)

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

