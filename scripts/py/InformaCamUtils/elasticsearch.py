import requests, copy, json, sys, os, re, time, datetime, hashlib

class Elasticsearch():
	def __init__(self, river=None):
		from InformaCamModels.asset import Asset
		
		self.el = "http://localhost:9200/unveillance/"
		
		if river is not None:
			self.river = river
			
	def get(self, _id, river):
		r = requests.get("%s%s/%s" % (self.el, river, _id))
		res = json.loads(r.text)
				
		try:
			if res['exists']:
				return res['_source']
		except KeyError as e:
			print e
			pass
			
		return None

	def delete(self, asset):
		r = requests.delete("%s%s/%s" % (self.el, self.river, asset._id))
		res = json.loads(r.text)

		try:
			return res['ok']
		except:
			return False
	
	def index(self, asset):
		r = requests.put("%s%s/%s" % (self.el, self.river, asset._id), data=json.dumps(asset.emit(exclude=['_id'])))
		res = json.loads(r.text)
		
		try:
			print res['ok']
			return res['ok']
		except KeyError as e:
			print r.text
			return False
			
	def update(self, asset):
		r = requests.put("%s%s/%s" % (self.el, self.river, asset._id), data=json.dumps(asset.emit(exclude=['_id'])))
		res = json.loads(r.text)
		
		try:
			return res['ok']
		except:
			return False
	
	def createIndex(self, reindex=True):
		mappings = {
			"submissions": {
				"properties": {
					"asset_path": {
						"type" : "string",
						"store" : True
					}
				}
			},
			"collections" : {
				"properties" : {
					"submissions" : {
						"type" : "nested",
						"include_in_parent" : True,
						"include_in_root" : True
					},
					"sensor_captures" : {
						"type" : "nested",
						"include_in_parent" : True,
						"include_in_root" : True
					}
				}
			},
			"j3m" : {
				"properties" : {
					"asset_path": {
						"type" : "string",
						"store" : True
					},
					"public_hash" : {
						"type" : "string",
						"store" : True
					},
					"data" : {
						"properties" : {
							"exif" : {
								"properties" : {
									"location" : {
										"type" : "geo_point",
										"store" : True
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
							},
							"userAppendedData" : {
								"type" : "nested",
								"include_in_parent" : True,
								"include_in_root" : True,
								"properties" : {
									"associatedForms" : {
										"type" : "nested",
										"include_in_parent" : True,
										"include_in_root" : True
									}
								}
							}
						}
					},
					"genealogy" : {
						"properties" : {
							"createdOnDevice" : {
								"type" : "string",
								"store" : True
							},
							"dateCreated" : {
								"type" : "long",
								"store" : True
							},
							"hashes" : {
								"type" : "string",
								"store" : True
							}
						}
					}
				}
			}
		}
		
		if reindex:
			r = requests.delete(self.el)
			res = json.loads(r.text)
			try:
				if res['error'] == "IndexMissingException[[unveillance] missing]":
					pass
			except KeyError as e:
				print r.text
					
		index = {
			"mappings" : mappings
		}
		r = requests.put(self.el, data=json.dumps(index))
		res = json.loads(r.text)
		
		try:
			return res['ok']
		except:
			return False	
	
	def query(self, params):
		url = "%s%s/_search?size=50" % (self.el, self.river)
		
		q = self.buildQuery(params)
		if q is None:
			return False

		print q['fields']
		query = {
			"fields" : q['fields'],
			"query" : {
				"filtered" : {
					"query" : q['query'],
					"filter" : q['filters']
				}
			},
			"sort" : q['sort']
		}
		
		if len(q['filters'].keys()) == 0:
			del query['query']['filtered']['filter']
		
		del query['fields']
		'''
		if query['fields'] is None:
			del query['fields']
		'''
		
		print "QUERY I USE:\n%s" % query
		
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
		sort = [
			{
				"date_admitted" : {
					"order" : "desc"
				}
			}
		]
		
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
			"filters" : {},
			"fields" : None,
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
							if not clause['get_all']:
								print "WITH J3M FILTER!"
								# just give me location, asset_path (for now...)
								query['fields'] = ["data.exif.location", "asset_path"]
								
							query['sort'] = sort
							return query
						elif clause['field'] == "location":
							c = {
								"geo_distance" : {
									"distance" : "%dmi" % clause['location']['radius'],
									"data.exif.location" : [
										clause['location']['longitude'], 
										clause['location']['latitude']
									]
								}
							}
						elif clause['field'] == "sourceID":
							c = {
								"bool": {
									"must" : {
										"term" : {
											"genealogy.createdOnDevice" : clause['sourceID']
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
						elif clause['field'] == "capturedOn":
							day = datetime.date.fromtimestamp(
								clause['capturedOn']['date']/1000
							)
							
							if clause['capturedOn']['upper'] == 0:
								lte = datetime.date(day.year, day.month, day.day + 1)
								gte = datetime.date(day.year, day.month, day.day)
							else:
								lte = datetime.date.fromtimestamp(
									(
										clause['capturedOn']['date'] +
										clause['capturedOn']['upper']
									)/1000
								)
								gte = datetime.date.fromtimestamp(
									clause['capturedOn']['date']/1000
								)
		
							c = {
								"range": {
									"genealogy.dateCreated" : {
										"gte" : format(time.mktime(
											gte.timetuple()) * 1000, '0.0f'
										),
										"lte" : format(time.mktime(
											lte.timetuple()) * 1000, '0.0f'
										)
									}
								}
							}
							print "PUSHING QUERY %s" % c			
						elif clause['field'] == "exif":
							c = {
								"bool": {
									"must" : []
								}
							}
							for k,v in clause.iteritems():
								if k != "field":
									c['bool']['must'].append({
										"term" : {
											"data.exif.%s" % k : v
										}
									})
						elif clause['field'] == "broadcast":
							c = copy.deepcopy(deep_drill)
							c_ = {
								"bool" : {
									"must" : []
								}
							}
							for k, v in clause['broadcast'].iteritems():
								c_['bool']['must'].append({
									"term" : {
										"%s.%s" % (path_2, k) : v
									}
								})
							c['nested']['query']['filtered']['filter']['nested']['query']['filtered']['filter'] = c_
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
						elif clause['field'] == "public_hash":
							if re.match(r'[a-zA-Z0-9]{40}', clause['public_hash']):
								c = {
									"bool" : {
										"must" : {
											"term" : {
												"public_hash" : clause['public_hash']
											}
										}
									}
								}						
						elif clause['field'] == "keyword":
							continue
						elif clause['field'] == "fingerprint":
							if self.river == "sources":
								term = {
									"fingerprint" : clause['fingerprint']
								}
							else:
								term = {
									"genealogy.createdOnDevice" : clause['fingerprint']
								}

							c = {
								"bool" : {
									"must" : {
										"term" : term
									}
								}
							}	
						
						if c is not None:
							clauses.append(c)
						
					except KeyError as e:
						print e
						try:
							if clause['clauses'] is not None:
								clauses.append(self.buildQuery(clause, as_sub_query=True)['filters'])
						except KeyError as e:
							pass
					
		if len(clauses) == 0:
			return None

		query['sort'] = sort
		if o is not None:
			query['filters'][o] = []
			query['query'] = match_all

		for clause in clauses:
			print clause.keys()[0]
			if query['query'] is None:
				print "so query['query'] is none"
				if clause.keys()[0] == "bool":
					query['query'] = clause['bool']['must']
				elif clause.keys()[0] == "geo_distance":
					query['query'] = match_all
					query['filters']['geo_distance'] = clause['geo_distance']
				elif clause.keys()[0] == "nested":
					query['query'] = match_all
					query['filters']['nested'] = clause['nested']
				elif clause.keys()[0] == "range":
					print "numeric range query!"
					query['query'] = clause

			elif o is not None:
				print "caught here: elif o is not None"
				query['filters'][o].append(clause)
			else:
				print "caught here: else"
				query['filters'][clause.keys()[0]] = clause[clause.keys()[0]]
		return query