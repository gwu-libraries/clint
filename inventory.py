from datetime import datetime
import json
import requests


class Inventory():

    def __init__(self, user, apikey, apiversion, url, port='80'):
        self.user = user
        self.apikey = apikey
        self.apiversion = apiversion
        self.url = url
        self.port = port
        self.baseurl = '%s:%s/api/%s' % (url, port, apiversion)

    def __str__(self):
        return '<Inventory %s>' % self.url

    def get(self, model, pk):
        params = {'format': 'json', 'username': self.user,
            'api_key': self.apikey}
        url = '%s/%s/%s/' % (self.baseurl, model, pk)
        return requests.get(url, params=params)

    def post(self, model, **data):
        url = '%s/%s/' % (self.baseurl, model)
        data.update({'username': self.user, 'api_key': self.apikey})
        return requests.post(url, data=json.dumps(data))

    def put(self, model, pk, **data):
        # put changes all fields, use patch for subset changes
        url = '%s/%s/%s' % (self.baseurl, model, pk)
        data.update({'username': self.user, 'api_key': self.apikey})
        return requests.put(url, data=json.dumps(data))

    def patch(self, model, pk, **data):
        url = '%s/%s/%s' % (self.baseurl, model, pk)
        data.update({'username': self.user, 'api_key': self.apikey})
        return requests.patch(url, data=json.dumps(data))

    def delete(self, model, pk):
        url = '%s/%s/%s' % (self.baseurl, model, pk)
        data = {'username': self.user, 'api_key': self.apikey}
        return requests.delete(url, data=json.dumps(data))        


class Machine():
    
    def __init__(self, name='', url=''):
        self.name = name
        self.url = url

    def __str__(self):
        return '<Machine %s>' % self.name


class Collection():

    def __init__(self, id='', name='', created='', description='', manager=''):
        self.id = id
        self.name = name
        self.created = created if created else datetime.now()
        self.description = description
        self.manager = manager

    def __str__(self):
        return '<Collection %s>' % self.id


class Project():

    def __init__(self, id='', name='', created='', manager='', collection='',
        start_date='', end_date=''):
        self.id = id
        self.name = name
        self.created = created if created else datetime.now()
        self.manager = manager
        self.collection = collection
        self.start_date = start_date
        self.end_date = end_date

    def __str__(self):
        return '<Project %s>' % self.id


class Item():

    def __init__(self, id='', title='', local_id='', collection='', project='',
        created='', original_item_type='', rawfiles_loc='', qcfiles_loc='',
        qafiles_loc='', finfiles_loc='', ocrfiles_loc='', notes=''):
        self.id = id
        self.title = title
        self.local_id = local_id
        self.collection = collection
        self.project = project
        self.created = created
        self.original_item_type = original_item_type
        self.rawfiles_loc = rawfiles_loc
        self.qcfiles_loc = qcfiles_loc
        self.qafiles_loc = qafiles_loc
        self.finfiles_loc = finfiles_loc
        self.ocrfiles_loc = ocrfiles_loc
        self.notes = notes

    def __str__(self):
        return '<Item %s>' % self.id


class Bag():

    def __init__(self, bagname='', created='', item='', machine='', path='',
        bag_type='', payload=''):
        self.bagname = bagname
        self.created = created
        self.item = item
        self.machine = machine
        self.path = path
        self.payload = payload

    def __str__(self):
        return '<Bag %s>' % self.bagname


class BagAction():

    def __init__(self, bag='', timestamp='', action='', note=''):
        self.bag = bag
        self.timestamp = timestamp
        self.action = action
        self.note = note

    def __str__(self):
        return '<BagAction %s>' % self.action

