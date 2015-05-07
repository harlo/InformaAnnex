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
