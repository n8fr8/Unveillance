import requests, copy, json, sys, os

class Elasticsearch():
	def __init__(self, river=None):
		sys.path.insert(0, os.path.abspath('.'))
		from InformaCamModels.asset import Asset
		
		self.el = "http://localhost:9200/informacam/"
		if river is not None:
			self.river = river
			
	def get(self, _id, river):
		r = requests.get("%s%s/%s" % (self.el, river, _id))
		res = json.loads(r.text)
		
		if res['exists']:
			return res['_source']
		else:
			return None

	def delete(self, asset):
		r = requests.delete("%s%s/%s" % (self.el, self.river, asset._id))
		res = json.loads(r.text)

		try:
			return res['ok']
		except:
			return False
	
	def index(self, asset):
		r = requests.put("%s%s/%s" % (self.el, self.river, asset._id), data=json.dumps(asset.emit()))
		res = json.loads(r.text)
		
		try:
			return res['ok']
		except:
			return False
			
	def update(self, asset):
		r = requests.put("%s%s/%s" % (self.el, self.river, asset._id), data=json.dumps(asset.emit()))
		res = json.loads(r.text)
		
		try:
			return res['ok']
		except:
			return False
	
	def createIndex(self, reindex=True):
		mappings = {
			"mappings" : {
				"j3m" : {
					"properties" : {
						"data" : {
							"properties" : {
								"exif" : {
									"properties" : {
										"location" : {
											"type" : "geo_point"
										}
									}
								},
								"sensorCapture" : {
									"type" : "nested",
									"include_in_parent" : True,
									"include_in_root" : True,
									"properties" : {
										"sensorPlayback" : {
											"type" : "nested",
											"include_in_parent" : True,
											"include_in_root" : True,
											"properties" : {
												"gps_coords" : {
													"type" : "geo_point"
												},
												"regionLocationData" : {
													"properties" : {
														"gps_coords" : {
															"type" : "geo_point"
														}
													}
												},
												"visibleWifiNetworks" : {
													"type" : "nested",
													"include_in_parent" : True,
													"include_in_root" : True
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
		
		if reindex:
			r = requests.delete(self.el)
			print r.text
		
		r = requests.put(self.el, data=json.dumps(mappings))
		res = json.loads(r.text)
		
		try:
			return res['ok']
		except:
			return False	
	
	def query(self, params):
		url = "%s%s/_search" % (self.el, self.river)
		
		q = self.buildQuery(params)
		if q is None:
			return False
		
		query = {
			"query" : {
				"filtered" : {
					"query" : q['query'],
					"filter" : q['filters']
				}
			}
		}
		if len(q['filters'].keys()) == 0:
			del query['query']['filtered']['filter']
		print query
		
		proc_res = []
		r = requests.get(url, data=json.dumps(query))
		res = json.loads(r.text)
		
		try:
			print len(res['hits']['hits'])
			for hit in res['hits']['hits']:
				proc_res.append(hit['_source'])
		except:
			print "0 hits (query invalid)"
		
		if len(proc_res) == 0:
			return False
		return proc_res
	
	def buildQuery(self, params, as_sub_query=False):
		match_all = { "match_all" : {}}
		path_1 = "data.sensorCapture"
		path_2 = "%s.sensorPlayback" % path_1
		deep_drill = {
			"nested" : {
				"path" : path_1,
				"query" : {
					"filtered": {
						"query" : match_all,
						"filter": {
							"nested" : {
								"path" : path_2,
								"query" : {
									"filtered" : {
										"query" : match_all,
										"filter" : {}
									}
								}
							}
						}
					}
				}
			}
		}
							
		clauses = []
		query = {
			"query" : None,
			"filters" : {}
		}
		o = None
		
		for k, v in params.iteritems():
			if k == "operator":
				o = v
			elif k == "clauses" and type(v) is list:
				for clause in v:
					c = None
					try:
						if clause['field'] == "get_all":
							query['query'] = match_all
							return query
						elif clause['field'] == "location":
							c = {
								"geo_distance" : {
									"distance" : "%dmi" % clause['radius'],
									"data.exif.location" : [
										clause['longitude'], 
										clause['latitude']
									]
								}
							}

						elif clause['field'] == "source":
							c = {
								"bool": {
									"must" : {
										"term" : {
											"genealogy.createdOnDevice" : clause['source']
										}
									}
								}
							}
							
						elif clause['field'] == "alias":
							c = {
								"bool": {
									"must" : {
										"term" : {
											"alias" : clause['alias']
										}
									}
								}
							}
														
						elif clause['field'] == "capuredOn":
							day = datetime.date.fromtimestamp(clause['date']/1000)
							gte = datetime.date(day.year, day.month, day.day - clause['lower'])
							lte = datetime.date(day.year, day.month, day.day + clause['upper'])
														
							c = {
								"numeric_range": {
									"genealogy.dateCreated" : {
										"gte" : format(time.mktime(gte.timetuple()) * 1000, '0.0f'),
										"lte" : format(time.mktime(lte.timetuple()) * 1000, '0.0f')
									}
								}
							}
							
						elif clause['field'] == "exif":
							for k,v in clause.iteritems():
								if k != "field":
									c = {
										"bool": {
											"must" : {
												"term" : {
													"data.exif.%s" % k : v
												}
											}
										}
									}
									clauses.append(c)	
							continue
							
						elif clause['field'] == "bssid":
							bssid = hashlib.sha1(clause['bssid']).hexdigest()
							path_3 = "%s.visibleWifiNetworks" % path_2
							c = copy.deepcopy(deep_drill)
							c_ = {
								"nested" : {
									"path" : path_3,
									"query" : {
										"filtered": {
											"query" : match_all,
											"filter" : {
												"bool" : {
													"must" : {
														"term" : {
															"%s.bt_hash" % path_3 : bssid
														}
													}
												}
											}
										}
									}
								}
							}
							c['nested']['query']['filtered']['filter']['nested']['query']['filtered']['filter'] = c_
							
						elif clause['field'] == "bluetoothDeviceAddress":
							c = copy.deepcopy(deep_drill)
							c_ =  {
								"bool" : {
									"must" : {
										"term" : {
											"%s.bluetoothDeviceAddress" % path_2 : clause['bluetoothDeviceAddress']
										}
									}
								}
							}
							c['nested']['query']['filtered']['filter']['nested']['query']['filtered']['filter'] = c_
						
						elif clause['field'] == "cellTowerId":
							c = copy.deepcopy(deep_drill)
							c_ =  {
								"bool" : {
									"must" : {
										"term" : {
											"%s.cellTowerId" % path_2 : clause['cellTowerId']
										}
									}
								}
							}
							c['nested']['query']['filtered']['filter']['nested']['query']['filtered']['filter'] = c_
								
						if c is not None:
							clauses.append(c)
						
					except KeyError as e:
						try:
							if clause['clauses'] is not None:
								clauses.append(self.buildQuery(clause, as_sub_query=True)['filters'])
						except KeyError as e:
							pass
					
		if len(clauses) == 0:
			return None

		if o is not None:
			query['filters'][o] = []
			query['query'] = match_all

		for clause in clauses:
			print clause.keys()[0]
			if query['query'] is None:
				if clause.keys()[0] == "bool":
					query['query'] = clause['bool']['must']
				elif clause.keys()[0] == "geo_distance":
					query['query'] = match_all
					query['filters']['geo_distance'] = clause['geo_distance']
				elif clause.keys()[0] == "nested":
					query['query'] = match_all
					query['filters']['nested'] = clause['nested']

			elif o is not None:
				query['filters'][o].append(clause)
			else:
				query['filters'][clause.keys()[0]] = clause[clause.keys()[0]]

				
		return query
		