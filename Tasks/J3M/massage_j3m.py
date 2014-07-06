from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def massageJ3M(task):
	task_tag = "MASSAGING J3M"
	
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "massaging j3m at %s" % task.doc_id
	task.setStatus(412)
		
	from lib.Worker.Models.uv_document import UnveillanceDocument
	
	from conf import DEBUG
	from vars import ASSET_TAGS
	
	media = UnveillanceDocument(_id=task.doc_id)
	if media is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	if hasattr(task, "j3m_name"):
		j3m_name = task.j3m_name
	else:
		j3m_name = "j3m.json"

	j3m = media.loadAsset(j3m_name)
	if j3m is None:
		print "J3M IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	from json import loads
	
	try:
		j3m = loads(j3m)
	except Exception as e:
		print "J3M IS INVALID"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	from hashlib import sha1
	try:
		j3m['public_hash'] = sha1("".join(
			[j3m['genealogy']['createdOnDevice'],
			"".join(j3m['genealogy']['hashes'])])).hexdigest()
	except KeyError as e:
		if DEBUG: print "no key %s" % e
		pass
	
	try:
		location = j3m['data']['exif']['location']
		j3m['data']['exif'].update({
			'location' : [location[1], location[0]]
		})
	except KeyError as e:
		if DEBUG: print "no key %s" % e
		pass
	
	try:
		if type(j3m['data']['sensorCapture']) is list: pass
	except KeyError as e:
		if DEBUG: print "no key %s" % e
		pass
	
	for playback in j3m['data']['sensorCapture']:
		if 'gps_coords' in playback['sensorPlayback'].keys():
			try:
				gps = str(playback['sensorPlayback']['gps_coords'])[1:-1].split(",")
				if DEBUG:
					print "REPLACING %s as geopoint" % gps
					print type(gps)
			
				playback['sensorPlayback'].update({
					'gps_coords' : [float(gps[1]), float(gps[0])]
				})
			except Exception as e:
				if DEBUG: print e
				pass
		
		if 'regionLocationData' in playback['sensorPlayback'].keys():
			try:
				gps = str(playback['sensorPlayback']['regionLocationData']['gps_coords'])
				gps = gps[1:-1].split(",")

				if DEBUG:
					print "REPLACING %s as geopoint" % gps
					
				playback['sensorPlayback']['regionLocationData'].update({
					'gps_coords' : [float(gps[1]), float(gps[0])]
				})
			except Exception as e:
				if DEBUG: print e
				pass
		
		if 'visibleWifiNetworks' in playback['sensorPlayback'].keys():
			try:
				for i,b in enumerate(playback['sensorPlayback']['visibleWifiNetworks']):
					playback['sensorPlayback']['visibleWifiNetworks'][i].update({
						'bt_hash' : sha1(b['bssid']).hexdigest()
					})
			except Exception as e:
				if DEBUG: print e
				pass
	
	import os, json
	from conf import getConfig
	from lib.Core.Utils.funcs import b64decode
	from lib.Worker.Utils.funcs import getFileType, unGzipBinary

	searchable_text = []
	
	try:
		with open(os.path.join(getConfig('informacam.forms_root'), "forms.json"), 'rb') as F:		
			for udata in j3m['data']['userAppendedData']:
				for aForms in udata['associatedForms']:
					st_keys = aForms['answerData'].keys()
					
					for f in json.loads(F.read())['forms']:
						if f['namespace'] == aForms['namespace']:
							try:
								for mapping in f['mapping']:
									try:
										group = mapping.keys()[0]
										key = aForms['answerData'][group].split(" ")
										
										for m in mapping[group]:
											if m.keys()[0] in key:
												key[key.index(m.keys()[0])] = m[m.keys()[0]]
										aForms['answerData'][group] = " ".join(key)
									except KeyError as e:
										if DEBUG: print "no key %s" % e
										pass
							except KeyError as e:
								if DEBUG: print "no key %s" % e
								pass
							
							try:
								idx = 0
								for audio in f['audio_form_data']:
									try:
										while audio in st_keys: st_keys.remove(audio)
									except Exception as e: pass
									
									try:
										audio_data = b64decode(
											aForms['answerData'][audio])
										
										if audio_data is None:
											if DEBUG: print "could not unb64 audio"
											continue
										
										if getFileType(audio_data, as_buffer=True) != MIME_TYPES['gzip']:
											if DEBUG: print "audio is not gzipped"
											continue
												
										audio_f = "audio_%d.3gp" % idx
										idx += 1
										
										media.addAsset(unGzipBinary(audio_data), audio_f,
											tags=[ASSET_TAGS['A_3GP']],
											description="3gp audio file from form")
										
										new_task=UnveillanceTask(inflate={
											'task_path' : "Media.convert.audioConvert",
											'doc_id' : media._id,
											'formats' : ["3gp", "wav"],
											'src_file' : "audio_%d.3gp" % idx,
											'queue' : task.queue
										})
										new_task.run()
										
										aForms['answerData'][audio] = "audio_%d.wav"
									except KeyError as e:
										if DEBUG: print "no key %s" % e
										pass
							except KeyError as e:
								if DEBUG: print "no key %s" % e
								pass
					
					if len(st_keys) > 0:
						for key in st_keys:
							searchable_text.append(aForms['answerData'][key])
						
	except KeyError as e:
		if DEBUG: print "no key %s" % e
		pass
	except IOError as e:
		if DEBUG: print "no forms to go over: %s" % e
										
	if media.addAsset(j3m, "j3m.json", as_literal=False) is not False:
		from lib.Worker.Models.ic_j3m import InformaCamJ3M
		from lib.Worker.Models.uv_task import UnveillanceTask
		
		j3m['media_id'] = media._id
		if len(searchable_text) > 0:
			j3m['searchable_text'] = searchable_text

		j3m = InformaCamJ3M(inflate=j3m)
		
		print "\n\n***NEW J3M CREATED***\n\n" 
		j3m.save()
		
		media.j3m_id = j3m._id
		print "NEW J3M ID TO SAVE: %s " % media.j3m_id
		media.save()
		
		new_task = UnveillanceTask(inflate={
			'task_path' : "J3M.verify_visual_content.verifyVisualContent",
			'doc_id' : media._id,
			'queue' : task.queue
		})
		new_task.run()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag