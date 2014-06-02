from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def initForms(task):
	task_tag = "INITTING FORMS"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "initing forms at form folder"
	task.setStatus(412)
	
	import os, re, json
	import xml.etree.ElementTree as ET
	
	from conf import DEBUG, CONF_ROOT
	
	for root, _, files in os.walk(os.path.join(CONF_ROOT, "forms")):
		for f in files:
			if re.match(r'.xml$', f):
				if DEBUG: print "ADDING FORM %s" % os.path.join(root, f)
				forms.append(os.path.join(root, f))
	
	jr_sentinel = "jr:itext('"
	parse = {"forms" : []}

	for form in forms:
		xmldoc = ET.parse(form)
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
				for mi in [m for m in model_item if re.match(r'{.*}item', m.tag)]:
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
		
			if map is not None: mapping['mapping'].append(map)

		if len(mapping['mapping']) == 0: del mapping['mapping']
		if len(mapping['audio_form_data']) == 0: del mapping['audio_form_data']
			
		if len(mapping.keys()) != 0:
			# get the namespace for this form from head (root[0]) head.title
			for el in root[0]:
				if re.match(r'{.*}title', el.tag):
					mapping['namespace'] = el.text
					break
		
			parse['forms'].append(mapping)
			if DEBUG: print mapping
	
	if DEBUG: print parse
	
	m = open(os.path.join(CONF_ROOT, "forms", "forms.json"), 'wb+')
	m.write(json.dumps(parse))
	m.close()
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag