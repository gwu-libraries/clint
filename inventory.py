from datetime import datetime
import json
import requests

from settings import INVENTORY_CREDENTIALS as creds


baseurl = '%s:%s/api/%s' % (creds['url'], creds['port'], creds['apiversion'])
auth_header = {'Authorization': 'ApiKey %s:%s' % (creds['user'],
    creds['apikey'])}

# Base HTTP methods

def _get(model, pk):
    params = {'format': 'json', 'username': creds['user'],
        'api_key': creds['apikey']}
    url = '%s/%s/%s/' % (baseurl, model, pk)
    return requests.get(url, params=params, headers=auth_header)

def _post(model, **data):
    # POST is for new items, not changes. Use PUT or PATCH for changes
    url = '%s/%s/' % (baseurl, model)
    return requests.post(url, data=json.dumps(data), headers=auth_header)

def _put(model, pk, **data):
    # PUT changes all fields, use PATCH for subset changes
    url = '%s/%s/%s/' % (baseurl, model, pk)
    return requests.put(url, data=json.dumps(data), headers=auth_header)

def _patch(model, pk, **data):
    url = '%s/%s/%s/' % (baseurl, model, pk)
    return requests.patch(url, data=json.dumps(data), headers=auth_header)

def _delete(model, pk):
    url = '%s/%s/%s/' % (baseurl, model, pk)
    return requests.delete(url, headers=auth_header)


# API methods

def getobject(model, pk):
    response = _get(model, pk)
    if response.status_code == 200:
        return _build_object(model, response)
    elif response.status_code == 404:
        raise Inventory404
    else:
        raise InventoryError


class Inventory404(Exception):
    pass


class InventoryError(Exception):
    pass


class Machine():

    def __init__(self, name='', url=''):
        self.name = name
        self.url = url

    def __str__(self):
        return '<Machine %s>' % self.name


class Collection(object):

    __readonly = ['id', 'created', 'stats']

    def __init__(self, id, name='', description='', manager='',
        created=None, stats=None):
        self.__loaded = False
        self.__id = id
        self.__name = name
        self.__description = description
        self.__manager = manager
        self.__created = created
        self.__stats = stats

    def __str__(self):
        return '<Collection %s>' % self.id

    def __setattr__(self, key, value):
        if key in self.__class__.__readonly:
            raise AttributeError("The attribute %s is read-only." % key)
        else:
            super(Collection, self).__setattr__(key, value)

    def __getattr__(self, key):
        if not self.__loaded:
            self._load_properties()
        if key in self.__class__.__readonly:
            return super(Collection, self).__getattribute__("_%s__%s" %
                (self.__class__.__name__, key))
        else:
            return super(Collection, self).__getattribute__(key)

    def _load_properties(self):
        response = _get('collection', self.__id)
        if response.status_code == 200:
            data = response.json()
            self.__name = data['name']
            self.__description = data['description']
            self.__manager = data['manager']
            self.__created = data['created']
            self.__stats = data['stats']
            self.__loaded = True
        elif response.status_code == 404:
            raise Inventory404()
        else:
            raise InventoryError()

    def to_string(self):
        if not self.__loaded:
            self._load_properties()
        lines = ['--Collection--'.center(24)]
        lines.append('%s: %s' % ('id'.rjust(11), self.__id))
        lines.append('%s: %s' % ('name'.rjust(11), self.__name))
        lines.append('%s: %s' % ('created'.rjust(11), self.__created))
        lines.append('%s: %s' % ('manager'.rjust(11), self.__manager))
        lines.append('%s: %s' % ('description'.rjust(11), self.__description))
        lines.append('%s: %s' % ('stats'.rjust(11), self.__stats))
        return '\n'.join(lines)


class Project(object):

    __readonly = ['id', 'created', 'stats']

    def __init__(self, id='', name='', manager='', collection='',
        start_date='', end_date='', created=None, stats=None):
        self.__loaded = False
        self.__id = id
        self.__name = name
        self.__created = created
        self.__manager = manager
        self.__collection = collection # FIX!
        self.__start_date = start_date
        self.__end_date = end_date
        self.__stats = stats

    def __str__(self):
        return '<Project %s>' % self.__id

    def __setattr__(self, key, value):
        if key in self.__class__.__readonly:
            raise AttributeError("The attribute %s is read-only." % key)
        else:
            super(Project, self).__setattr__(key, value)

    def __getattr__(self, key):
        if not self.__loaded:
            self._load_properties()
        if key in self.__class__.__readonly:
            return super(Project, self).__getattribute__("_%s__%s" %
                (self.__class__.__name__, key))
        else:
            return super(Project, self).__getattribute__(key)

    def _load_properties(self):
        response = _get('project', self.__id)
        if response.status_code == 200:
            data = response.json()
            collection_id = '/'.join(
                data['collection'].rstrip('/').split('/')[-2:])
            self.__name = data['name']
            self.__manager = data['manager']
            self.__created = data['created']
            self.__collection = Collection(collection_id)
            self.__start_date = data['start_date']
            self.__end_date = data['end_date']
            self.__stats = data['stats']
            self.__loaded = True
        elif response.status_code == 404:
            raise Inventory404()
        else:
            raise InventoryError()

    def to_string(self):
        if not self.__loaded:
            self._load_properties()
        lines = ['--Project--'.center(24)]
        lines.append('%s: %s' % ('id'.rjust(11), self.__id))
        lines.append('%s: %s' % ('name'.rjust(11), self.__name))
        lines.append('%s: %s' % ('created'.rjust(11), self.__created))
        lines.append('%s: %s' % ('manager'.rjust(11), self.__manager))
        lines.append('%s: %s' % ('collection'.rjust(11), self.__collection))
        lines.append('%s: %s' % ('start date'.rjust(11), self.__start_date))
        lines.append('%s: %s' % ('end date'.rjust(11), self.__end_date))
        lines.append('%s: %s' % ('stats'.rjust(11), self.__stats))
        return '\n'.join(lines)


class Item(object):

    __readonly = ['id', 'created', ]

    def __init__(self, id='', title='', local_id='', collection='', project='',
        original_item_type='', notes='', created=None, stats=None):
        self.__loaded = False
        self.__id = id
        self.__title = title
        self.__local_id = local_id
        self.__collection = collection
        self.__project = project
        self.__created = created
        self.__original_item_type = original_item_type
        self.__notes = notes
        self.__stats = stats

    def __str__(self):
        return '<Item %s>' % self.__id

    def __setattr__(self, key, value):
        if key in self.__class__.__readonly:
            raise AttributeError("The attribute %s is read-only." % key)
        else:
            super(Item, self).__setattr__(key, value)

    def __getattr__(self, key):
        if not self.__loaded:
            self._load_properties()
        if key in self.__class__.__readonly:
            return super(Item, self).__getattribute__("_%s__%s" %
                (self.__class__.__name__, key))
        else:
            return super(Item, self).__getattribute__(key)

    def _load_properties(self):
        response = _get('item', self.__id)
        if response.status_code == 200:
            data = response.json()
            collection_id = '/'.join(
                data['collection'].rstrip('/').split('/')[-2:])
            project_id = '/'.join(
                data['project'].rstrip('/').split('/')[-2:])
            self.__title = data['title']
            self.__local_id = data['local_id']
            self.__created = data['created']
            self.__collection = Collection(collection_id)
            self.__project = Project(project_id)
            self.__original_item_type = data['original_item_type']
            self.__stats = data['stats']
            self.__loaded = True
        elif response.status_code == 404:
            raise Inventory404()
        else:
            raise InventoryError()

    def to_string(self):
        if not self.__loaded:
            self._load_properties()
        lines = ['--Item--'.center(24)]
        lines.append('%s: %s' % ('id'.rjust(11), self.id))
        lines.append('%s: %s' % ('title'.rjust(11), self.__title))
        lines.append('%s: %s' % ('local_id'.rjust(11), self.__local_id))
        lines.append('%s: %s' % ('created'.rjust(11), self.__created))
        lines.append('%s: %s' % ('collection'.rjust(11), self.__collection))
        lines.append('%s: %s' % ('project'.rjust(11), self.__project))
        lines.append('%s: %s' % ('orig item type'.rjust(11),
            self.__original_item_type))
        lines.append('%s: %s' % ('stats'.rjust(11), self.__stats))
        return '\n'.join(lines)


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
