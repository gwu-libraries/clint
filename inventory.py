import json

import requests

from settings import INVENTORY_CREDENTIALS as creds


baseurl = '%s/api/%s' % (creds['url'], creds['apiversion'])
auth_header = {'Authorization': 'ApiKey %s:%s' % (creds['user'],
               creds['apikey']), 'Content-Type': 'application/json'}

# Base HTTP methods


def _get(model, pk=None, params={}):
    params.update({'format': 'json', 'username': creds['user'],
                   'api_key': creds['apikey']})
    if pk:
        url = '%s/%s/%s/' % (baseurl, model, pk)
    else:
        url = '%s/%s/' % (baseurl, model)
    return requests.get(url, params=params, headers=auth_header,
                        verify=creds['verify_ssl_cert'])


def _post(model, **data):
    # POST is for new items, not changes. Use PUT or PATCH for changes
    url = '%s/%s/' % (baseurl, model)
    return requests.post(url, data=json.dumps(data), headers=auth_header,
                         verify=creds['verify_ssl_cert'])


def _put(model, pk, **data):
    # PUT changes all fields (overwrites with blank if you don't set a value)
    # use PATCH to change one or two fields without setting them all
    url = '%s/%s/%s/' % (baseurl, model, pk)
    return requests.put(url, data=json.dumps(data), headers=auth_header,
                        verify=creds['verify_ssl_cert'])


def _patch(model, pk, **data):
    url = '%s/%s/%s/' % (baseurl, model, pk)
    return requests.patch(url, data=json.dumps(data), headers=auth_header,
                          verify=creds['verify_ssl_cert'])


def _delete(model, pk):
    url = '%s/%s/%s/' % (baseurl, model, pk)
    return requests.delete(url, headers=auth_header,
                           verify=creds['verify_ssl_cert'])

# helper functions


def parse_id(location, uri=False):
    # Parsea an object id from the 'location' returned by API 201 response.
    # Option to return just the id or the relative uri,
    # such as: /api/v1/item/38989/c01hf854dw
    uriparts = location.strip('/').split('/')[3:]
    if uri is True:
        return '/%s/' % '/'.join(uriparts)
    else:
        return '/'.join(uriparts[3:])


class Inventory404(Exception):

    def __init__(self, msg=''):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class InventoryError(Exception):

    def __init__(self, msg=''):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class NoIdentifierError(Exception):

    def __init__(self, msg=''):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class NonUniqueIdentifierError(Exception):

    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return repr(self.identifier)


class Machine(object):

    __readonly = ['id', 'resource_uri']
    __readwrite = ['name', 'url', 'ip', 'notes', 'www_root']
    __relations = []

    def __init__(self, id=None, name='', url='', ip='', notes='',
            www_root=''):
        self.__loaded = False
        self.__id = id
        self.name = name
        self.url = url
        self.ip = ip
        self.notes = notes
        self.www_root = www_root

    def __str__(self):
        return '<Machine %s>' % (self.__id)

    def __setattr__(self, key, value):
        if key in self.__class__.__readonly:
            raise AttributeError("The attribute %s is read-only." % key)
        else:
            super(Machine, self).__setattr__(key, value)

    def __getattr__(self, key):
        if not self.__loaded:
            self._load_properties()
        if key in self.__class__.__readonly:
            return super(Machine, self).__getattribute__("_%s__%s" %
                         (self.__class__.__name__, key))
        else:
            return super(Machine, self).__getattribute__(key)

    def _load_properties(self):
        response = _get('machine', self.__id)
        if response.status_code == 200:
            data = response.json()
            self.name = data['name']
            self.url = data['url']
            self.ip = data['ip']
            self.notes = data['notes']
            self.www_root = data['www_root']
            self.__resource_uri = data['resource_uri']
            self.__loaded = True
        elif response.status_code == 404:
            raise Inventory404('Machine identified by %s not found' %
                               self.__id)
        else:
            raise InventoryError()

    def readwrite(self):
        return self.__readwrite

    def writeopts(self):
        return [(attr, None) for attr in self.__class__.__readwrite]

    def save(self):
        """
        Store item in Inventory
        Do a POST if new (no ID) and PUT otherwise
        """
        data = {}
        if not self.__loaded and not self.__id:
            for field in self.__class__.__readwrite:
                data[field] = getattr(self, field)
            response = _post('machine', **data)
            if response.status_code == 201:
                url = response.headers['Location']
                self.__id = url.rstrip('/').split('/')[-1]
                return self
            else:
                raise InventoryError()
        elif self.__loaded:
            for field in vars(self):
                data[field] = getattr(self, field)
            response = _put('machine', self.id, **data)
            if response.status_code == 204:
                return self
            else:
                raise InventoryError()
        else:
            return self

    def to_string(self):
        if not self.__loaded:
            self._load_properties()
        lines = ['--Machine--'.rjust(17)]
        lines.append('%s: %s' % ('id'.rjust(11), self.__id))
        lines.append('%s: %s' % ('name'.rjust(11), self.name))
        lines.append('%s: %s' % ('url'.rjust(11), self.url))
        lines.append('%s: %s' % ('ip'.rjust(11), self.ip))
        lines.append('%s: %s' % ('notes'.rjust(11), self.notes))
        lines.append('%s: %s' % ('www root'.rjust(11), self.www_root))
        return '\n'.join(lines)


class Collection(object):

    __readonly = ['id', 'created', 'stats', 'resource_uri']
    __readwrite = ['name', 'description', 'manager', 'access_loc']
    __relations = []

    def __init__(self, id=None, name='', description='', manager='',
                 created=None, access_loc='', stats=None):
        self.__loaded = False
        self.__id = id
        self.name = name
        self.description = description
        self.manager = manager
        self.access_loc = access_loc
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
        if key in self.__class__.__readonly or key in ['readonly', 'readwrite',
                                                       'relations', 'options']:
            return super(Collection, self).__getattribute__("_%s__%s" %
                         (self.__class__.__name__, key))
        else:
            return super(Collection, self).__getattribute__(key)

    def _load_properties(self):
        response = _get('collection', self.__id)
        if response.status_code == 200:
            data = response.json()
            self.name = data['name']
            self.description = data['description']
            self.manager = data['manager']
            self.access_loc = data['access_loc']
            self.__created = data['created']
            self.__stats = data['stats']
            self.__resource_uri = data['resource_uri']
            self.__loaded = True
        elif response.status_code == 404:
            raise Inventory404('Collection identified by %s not found' %
                               self.__id)
        else:
            raise InventoryError()

    def readwrite(self):
        return self.__readwrite

    def writeopts(self):
        return [(attr, None) for attr in self.__class__.__readwrite]

    def save(self):
        """
        Store item in Inventory
        Do a POST if new (no ID) and PUT otherwise
        """
        data = {}
        if not self.__loaded and not self.__id:
            for field in self.__class__.__readwrite:
                data[field] = getattr(self, field)
            response = _post('collection', **data)
            if response.status_code == 201:
                url = response.headers['Location']
                self.__id = '/'.join(url.rstrip('/').split('/')[-2:])
                return self
            else:
                raise InventoryError(response.text)
        elif self.__loaded:
            for field in vars(self):
                data[field] = getattr(self, field)
            response = _put('collection', self.id, **data)
            if response.status_code == 204:
                return self
            else:
                raise InventoryError(response)
        else:
            return self

    def to_string(self):
        if not self.__loaded:
            self._load_properties()
        lines = ['--Collection--'.rjust(19)]
        lines.append('%s: %s' % ('id'.rjust(11), self.id))
        lines.append('%s: %s' % ('name'.rjust(11), self.name))
        lines.append('%s: %s' % ('created'.rjust(11), self.created))
        lines.append('%s: %s' % ('manager'.rjust(11), self.manager))
        lines.append('%s: %s' % ('description'.rjust(11), self.description))
        lines.append('%s: %s' % ('access_loc'.rjust(11), self.access_loc))
        lines.append('%s: %s' % ('stats'.rjust(11), self.stats))
        return '\n'.join(lines)


class Project(object):

    __readonly = ['id', 'created', 'stats', 'resource_uri']
    __readwrite = ['name', 'collection']
    __relations = ['collection']

    def __init__(self, id=None, name='', manager='', created=None, stats=None,
                 collection=None, start_date='', end_date=''):
        self.__loaded = False
        self.__id = id
        self.name = name
        self.__created = created
        self.manager = manager
        self.start_date = start_date
        self.end_date = end_date
        self.__stats = stats
        self.collection = collection

    def __str__(self):
        return '<Project %s>' % self.id

    def __setattr__(self, key, value):
        if key in self.__relations:
            if value == '':
                value = None
            elif (isinstance(value, str) or isinstance(value, unicode)):
                obj = globals()[key.capitalize()](id=value)
                obj._load_properties()
                value = obj
        if key in self.__class__.__readonly:
            raise AttributeError("The attribute %s is read-only." % key)
        else:
            super(Project, self).__setattr__(key, value)

    def __getattr__(self, key):
        if not self.__loaded:
            self._load_properties()
        if key in self.__class__.__readonly or key in ['readonly', 'readwrite',
                                                       'relations', 'options']:
            return super(Project, self).__getattribute__("_%s__%s" %
                (self.__class__.__name__, key))
        else:
            return super(Project, self).__getattribute__(key)

    def _load_properties(self):
        response = _get('project', self.__id)
        if response.status_code == 200:
            data = response.json()
            if data['collection']:
                collection_id = '/'.join(
                    data['collection'].rstrip('/').split('/')[-2:])
                self.collection = collection_id
            else:
                self.__collection = None
            self.name = data['name']
            self.__created = data['created']
            self.__stats = data['stats']
            self.__resource_uri = data['resource_uri']
            self.__loaded = True
        elif response.status_code == 404:
            raise Inventory404('Project identified by %s not found' %
                               self.__id)
        else:
            raise InventoryError()

    def readwrite(self):
        return self.__readwrite

    def writeopts(self):
        return [(attr, None) for attr in self.__class__.__readwrite]

    def save(self):
        """
        Store item in Inventory
        Do a POST if new (no ID) and PUT otherwise
        """
        data = {}
        if not self.__loaded and not self.__id:
            for field in self.__class__.__readwrite:
                if field in self.__relations:
                    try:
                        data[field] = getattr(self, field).resource_uri
                    except AttributeError:
                        data[field] = None
                else:
                    data[field] = getattr(self, field)
            response = _post('project', **data)
            if response.status_code == 201:
                url = response.headers['Location']
                self.__id = '/'.join(url.rstrip('/').split('/')[-2:])
                return self
            else:
                raise InventoryError(response.text)
        elif self.__loaded:
            for field in vars(self):
                if field in self.__relations:
                    relobj = getattr(self, field)
                    data[field] = relobj.resource_uri if relobj else None
                else:
                    data[field] = getattr(self, field)
            response = _put('project', self.id, **data)
            if response.status_code == 204:
                return self
            else:
                raise InventoryError(response)
        else:
            return self

    def to_string(self):
        if not self.__loaded:
            self._load_properties()
        lines = ['--Project--'.rjust(17)]
        lines.append('%s: %s' % ('id'.rjust(10), self.__id))
        lines.append('%s: %s' % ('name'.rjust(10), self.name))
        lines.append('%s: %s' % ('created'.rjust(10), self.__created))
        lines.append('%s: %s' % ('collection'.rjust(10), self.collection))
        lines.append('%s: %s' % ('stats'.rjust(10), self.__stats))
        return '\n'.join(lines)


class Item(object):

    __readonly = ['id', 'created', 'stats', 'resource_uri']
    __readwrite = ['title', 'local_id', 'notes', 'project', 'collection',
                   'original_item_type', 'access_loc']
    __relations = ['collection', 'project']
    __options = {
        'original_item_type': {
            '1': 'book',
            '2': 'microfilm',
            '3': 'audio',
            '4': 'video',
            '5': 'mixed',
            '6': 'other'
        }
    }

    def __init__(self, id=None, title='', local_id='', notes='', stats=None,
                 project=None, original_item_type='', created=None,
                 collection=None, access_loc=''):
        self.__loaded = False
        self.__id = id
        self.title = title
        self.local_id = local_id
        self.__created = created
        self.original_item_type = original_item_type
        self.notes = notes
        self.__stats = stats
        self.collection = collection
        self.project = project
        self.access_loc = access_loc

    def __str__(self):
        return '<Item %s>' % self.__id

    def __setattr__(self, key, value):
        if key in self.__relations:
            if value == '':
                value = None
            elif (isinstance(value, str) or isinstance(value, unicode)):
                obj = globals()[key.capitalize()](id=value)
                obj._load_properties()
                value = obj
        elif key in self.options().keys() \
                and value in self.options(field=key).values():
            value = self.options(field=key, value=value)
        if key in self.__class__.__readonly:
            raise AttributeError("The attribute %s is read-only." % key)
        else:
            super(Item, self).__setattr__(key, value)

    def __getattr__(self, key):
        if not self.__loaded:
            self._load_properties()
        if key in self.__class__.__readonly or key in ['readonly', 'readwrite',
                                                       'relations', 'options']:
            return super(Item, self).__getattribute__("_%s__%s" %
                (self.__class__.__name__, key))
        else:
            return super(Item, self).__getattribute__(key)

    def _load_properties(self):
        if self.__id:
            response = _get('item', self.__id)
        elif self.local_id:
            response = _get('item', params={'local_id': self.local_id})
        else:
            raise NoIdentifierError()
        if response.status_code == 200:
            data = response.json()
            if not self.__id:
                if len(data['objects']) > 1:
                    raise NonUniqueIdentifierError(self.local_id)
                elif len(data['objects']) == 0:
                    print 'no objects'
                    raise Inventory404('Item identified by %s not found' %
                                       self.__id)
                else:
                    data = data['objects'][0]
                    self.__id = data['id']
            self.title = data['title']
            self.local_id = data['local_id']
            self.__created = data['created']
            if data['collection']:
                collection_id = '/'.join(
                    data['collection'].rstrip('/').split('/')[-2:])
                self.collection = collection_id
            else:
                self.__collection = None
            if data['project']:
                project_id = '/'.join(
                    data['project'].rstrip('/').split('/')[-2:])
                self.project = project_id
            else:
                self.__project = None
            self.original_item_type = data['original_item_type']
            self.__stats = data['stats']
            self.__resource_uri = data['resource_uri']
            self.__loaded = True
            self.access_loc = data['access_loc']
        elif response.status_code == 404:
            # try looking up by local id instead
            if self.__id and not self.local_id:
                self.local_id = self.__id
                self.__id = None
                self._load_properties()
            else:
                raise Inventory404('Item identified by %s not found' %
                                   self.__id)
        else:
            raise InventoryError()

    def readwrite(self):
        return self.__readwrite

    def writeopts(self):
        output = []
        for attr in self.__class__.__readwrite:
            if attr in self.__options.keys():
                opts = self.options(attr)
            else:
                opts = None
            output.append((attr, opts))
        return output

    def options(self, field=None, key=None, value=None):
        # if not arguments sent, output entire dictionary
        if field is None and key is None and value is None:
            return self.__options
        elif field is not None:
            # if field set w/o key or value to fine, give option tuples list
            if key is None and value is None:
                return self.__options[field]
            # if given field and key, return value of that option
            elif key is not None:
                if key in self.__options[field].keys():
                    return self.__options[field][key]
            # if given field and value, give option key
            elif value is not None:
                for k, v in self.__options[field].items():
                    if value == v:
                        return k

    def save(self):
        """
        Store item in Inventory
        Do a POST if new (no ID) and PUT otherwise
        """
        data = {}
        if not self.__loaded and not self.__id:
            for field in self.__class__.__readwrite:
                if field in self.__relations:
                    try:
                        data[field] = getattr(self, field).resource_uri
                    except AttributeError:
                        data[field] = None
                else:
                    data[field] = getattr(self, field)
            response = _post('item', **data)
            if response.status_code == 201:
                url = response.headers['Location']
                self.__id = '/'.join(url.rstrip('/').split('/')[-2:])
                return self
            else:
                raise InventoryError(response.text)
        elif self.__loaded:
            for field in vars(self):
                if field in self.__relations:
                    relobj = getattr(self, field)
                    data[field] = relobj.resource_uri if relobj else None
                else:
                    data[field] = getattr(self, field)
            response = _put('item', self.id, **data)
            if response.status_code == 204:
                return self
            else:
                print 'Error with data: %s\n%s' % (data, response.text)
                raise InventoryError(response)
        else:
            return self

    def to_string(self):
        if not self.__loaded:
            self._load_properties()
        lines = ['--Item--'.rjust(19)]
        lines.append('%s: %s' % ('id'.rjust(14), self.id))
        lines.append('%s: %s' % ('title'.rjust(14), self.title))
        lines.append('%s: %s' % ('local_id'.rjust(14), self.local_id))
        lines.append('%s: %s' % ('created'.rjust(14), self.created))
        lines.append('%s: %s' % ('collection'.rjust(14), self.collection))
        lines.append('%s: %s' % ('project'.rjust(14), self.project))
        lines.append('%s: %s' % ('orig item type'.rjust(14),
                     self.options('original_item_type',
                     self.original_item_type)))
        lines.append('%s: %s' % ('access_loc'.rjust(14), self.access_loc))
        lines.append('%s: %s' % ('notes'.rjust(14), self.notes))
        lines.append('%s: %s' % ('stats'.rjust(14), self.stats))
        return '\n'.join(lines)


class Bag(object):

    __readonly = ['resource_uri']
    # bagname is readwrite for now because inventory does not autoassign names
    # change this once inventory code has been changed
    __readwrite = ['bagname', 'bag_type', 'absolute_filesystem_path', 'payload', 'machine',
                   'item', 'created']
    __relations = ['machine', 'item']
    __options = {
        'bag_type': {
            '1': 'Access',
            '2': 'Preservation',
            '3': 'Export'
        }
    }

    def __init__(self, bagname=None, created=None, item=None, machine=None,
                 absolute_filesystem_path='', bag_type='', payload=''):
        self.__loaded = False
        self.bagname = bagname
        self.created = created
        self.bag_type = bag_type
        self.absolute_filesystem_path = absolute_filesystem_path
        self.payload = payload
        self.machine = machine
        self.item = item

    def __str__(self):
        return '<Bag %s>' % self.bagname

    def __setattr__(self, key, value):
        if key in self.__relations \
                and (isinstance(value, str) or isinstance(value, unicode)):
            obj = globals()[key.capitalize()](id=value)
            obj._load_properties()
            value = obj
        elif key in self.options().keys() \
                and value in self.options(field=key).values():
            value = self.options(field=key, value=value)
        if key in self.__class__.__readonly:
            raise AttributeError("The attribute %s is read-only." % key)
        else:
            super(Bag, self).__setattr__(key, value)

    def __getattr__(self, key):
        if not self.__loaded:
            self._load_properties()
        if key in self.__class__.__readonly or key in ['readonly', 'readwrite',
                                                       'relations', 'options']:
            return super(Bag, self).__getattribute__("_%s__%s" %
                (self.__class__.__name__, key))
        else:
            return super(Bag, self).__getattribute__(key)

    def _load_properties(self):
        response = _get('bag', self.bagname)
        if response.status_code == 200:
            data = response.json()
            item_id = '/'.join(data['item'].rstrip('/').split('/')[-2:])
            machine_id = '/'.join(data['machine'].rstrip('/').split('/')[-1:])
            self.bagname = data['bagname']
            self.created = data['created']
            self.bag_type = data['bag_type']
            self.item = item_id
            self.machine = machine_id
            self.absolute_filesystem_path = data['absolute_filesystem_path']
            self.payload = data['payload']
            self.__resource_uri = data['resource_uri']
            self.__loaded = True
        elif response.status_code == 404:
            raise Inventory404('Bag identified by %s not found' %
                               self.__bagname)
        else:
            raise InventoryError()

    def save(self):
        """
        Store bag in Inventory
        Do a POST if new (no ID) and PUT otherwise
        """
        data = {}
        if not self.__loaded:
            for field in self.__class__.__readwrite:
                if field in self.__relations:
                    data[field] = getattr(self, field).resource_uri
                else:
                    data[field] = getattr(self, field)
            response = _post('bag', **data)
            if response.status_code == 201:
                url = response.headers['Location']
                self.bagname = '/'.join(url.rstrip('/').split('/')[6:])
                return self
            else:
                raise InventoryError(response.text)
        elif self.__loaded:
            for field in vars(self):
                if field in self.__relations:
                    data[field] = getattr(self, field).resource_uri
                else:
                    data[field] = getattr(self, field)
            response = _put('bag', self.bagname, **data)
            if response.status_code == 204:
                return self
            else:
                raise InventoryError(response)
        else:
            return self

    def readwrite(self):
        return self.__readwrite

    def writeopts(self):
        output = []
        for attr in self.__class__.__readwrite:
            if attr in self.__options.keys():
                opts = self.options(attr)
            else:
                opts = None
            output.append((attr, opts))
        return output

    def options(self, field=None, key=None, value=None):
        # if not arguments sent, output entire dictionary
        if field is None and key is None and value is None:
            return self.__options
        elif field is not None:
            # if field set w/o key or value to fine, give option tuples list
            if key is None and value is None:
                return self.__options[field]
            # if given field and key, return value of that option
            elif key is not None:
                if key in self.__options[field].keys():
                    return self.__options[field][key]
            # if given field and value, give option key
            elif value is not None:
                for k, v in self.__options[field].items():
                    if value == v:
                        return k

    def to_string(self):
        if not self.__loaded:
            self._load_properties()
        lines = ['--Bag--'.rjust(12)]
        lines.append('%s: %s' % ('bagname'.rjust(8), self.bagname))
        lines.append('%s: %s' % ('bag type'.rjust(8),
                     self.options('bag_type', self.bag_type)))
        lines.append('%s: %s' % ('created'.rjust(8), self.created))
        lines.append('%s: %s' % ('item'.rjust(8), self.item))
        lines.append('%s: %s' % ('machine'.rjust(8), self.machine))
        lines.append('%s: %s' % ('absolute_filesystem_path'.rjust(8), self.absolute_filesystem_path))
        #lines.append('%s: %s' % ('payload'.rjust(11), self.__payload))
        return '\n'.join(lines)


class BagAction(object):

    __readonly = ['id']
    __readwrite = ['bag', 'timestamp', 'action', 'note']
    __relations = ['bag']
    __options = {
        'action': {
            '1': 'updated',
            '2': 'moved',
            '3': 'validated',
            '4': 'imported'
        }
    }

    def __init__(self, bag='', timestamp='', action='', note=''):
        self.__loaded = False
        self.bag = bag
        self.timestamp = timestamp
        self.action = action
        self.note = note

    def __str__(self):
        return '<BagAction %s>' % self.__id

    def __setattr__(self, key, value):
        if key in self.__relations \
                and (isinstance(value, str) or isinstance(value, unicode)):
            obj = globals()[key.capitalize()](value)
            obj._load_properties()
            value = obj
        elif key in self.options().keys() \
                and value in self.options(field=key).values():
            value = self.options(field=key, value=value)
        if key in self.__class__.__readonly:
            raise AttributeError("The attribute %s is read-only." % key)
        else:
            super(BagAction, self).__setattr__(key, value)

    def __getattr__(self, key):
        if not self.__loaded:
            self._load_properties()
        if key in self.__class__.__readonly or key in ['readonly', 'readwrite',
                                                       'relations', 'options']:
            return super(BagAction, self).__getattribute__("_%s__%s" %
                (self.__class__.__name__, key))
        else:
            return super(BagAction, self).__getattribute__(key)

    def _load_properties(self):
        response = _get('bagaction', self.__id)
        if response.status_code == 200:
            data = response.json()
            bagname = '/'.join(data['bag'].rstrip('/').split('/')[4:])
            self.bag = bagname
            self.timestamp = data['timestamp']
            self.action = data['action']
            self.note = data['note']
            self.__resource_uri = data['resource_uri']
            self.__loaded = True
        elif response.status_code == 404:
            raise Inventory404('BagAction identified by %s not found' %
                               self.__id)
        else:
            raise InventoryError()

    def save(self):
        """
        Store action in Inventory
        Do a POST if new (no ID) and PUT otherwise
        """
        data = {}
        if not self.__loaded:
            for field in self.__class__.__readwrite:
                if field in self.__relations:
                    data[field] = getattr(self, field).resource_uri
                else:
                    data[field] = getattr(self, field)
            response = _post('bagaction', **data)
            if response.status_code == 201:
                url = response.headers['Location']
                self.__id = '/'.join(url.rstrip('/').split('/')[6:])
                return self
            else:
                raise InventoryError(response.text)
        elif self.__loaded:
            for field in vars(self):
                if field in self.__relations:
                    data[field] = getattr(self, field).resource_uri
                else:
                    data[field] = getattr(self, field)
            response = _put('bagaction', self.__id, **data)
            if response.status_code == 204:
                return self
            else:
                raise InventoryError(response)
        else:
            return self

    def readwrite(self):
        return self.__readwrite

    def writeopts(self):
        output = []
        for attr in self.__class__.__readwrite:
            if attr in self.__options.keys():
                opts = self.options(attr)
            else:
                opts = None
            output.append((attr, opts))
        return output

    def options(self, field=None, key=None, value=None):
        # if not arguments sent, output entire dictionary
        if field is None and key is None and value is None:
            return self.__options
        elif field is not None:
            # if field set w/o key or value to fine, give option tuples list
            if key is None and value is None:
                return self.__options[field]
            # if given field and key, return value of that option
            elif key is not None:
                if key in self.__options[field].keys():
                    return self.__options[field][key]
            # if given field and value, give option key
            elif value is not None:
                for k, v in self.__options[field].items():
                    if value == v:
                        return k

    def to_string(self):
        if not self.__loaded:
            self._load_properties()
        lines = ['--BagAction--'.rjust(16)]
        lines.append('%s: %s' % ('id'.rjust(8), self.id))
        lines.append('%s: %s' % ('bag'.rjust(8), self.bag))
        lines.append('%s: %s' % ('action'.rjust(8),
                     self.options('action', self.action)))
        lines.append('%s: %s' % ('timestamp'.rjust(8), self.timestamp))
        lines.append('%s: %s' % ('note'.rjust(8), self.note))
        return '\n'.join(lines)
