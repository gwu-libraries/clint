#! ENV/bin/python

import argparse
import ast
from datetime import datetime
import glob
import json
import logging
import os
from pprint import pprint
import readline
import shutil
import sys

import bagit

from inventory import Bag, BagAction, Collection, Item, Machine, Project
import inventory as inv


log = logging.getLogger(__name__)

'''
List of potential clint commands

Interacting with Inventory
--------------------------
show collection/item/bag <id>
add collection/item/bag
edit collection/item/bag <id>
delete collection/item/bag <id>
list collections/items/bags/files in collection/item/bag <id>

Managing Bags
-------------
bag <dir>
rebag <dir>
copy <id>
move <id>
validate <id>
'''
# reference variables
models = ['machine', 'collection', 'project', 'item', 'bag', 'bag_action']
orig_item_types = ['book', 'microfilm', 'audio', 'video', 'mixed',
                   'other']
bag_types = ['Access', 'Preservation', 'Export']
actions = ['updated', 'moved', 'validated', 'imported to DSpace', 'added']


def ls(args):
    # add params to filter by foreignkey models
    params = {}
    for model in models:
        if model in args:
            val = getattr(args, model.replace('_', ''))
            if val is not None and val != '':
                params[model] = val
    res = inv._get(model=args.model.replace('_', ''), params=params)
    data = res.json()
    if args.json:
        print json.dumps(data, indent=2)
    else:
        objects = res.json().get('objects', None)
        if not objects:
            print 'No %ss found' % args.model
        else:
            for index, obj in enumerate(objects, start=1):
                print '-----%s-----' % index
                if 'bagname' in obj.keys():
                    print 'bagname: %s' % obj.pop('bagname')
                else:
                    print 'id: %s' % obj.pop('id')
                if 'name' in obj.keys():
                    print 'name: %s' % obj.pop('name')
                elif 'title' in obj.keys():
                    print 'title: %s' % obj.pop('title').encode('utf-8')
                for k in sorted(obj.keys()):
                    print '%s: %s' % (k, obj[k])
            print '----------\n%s total %ss' % (len(objects), args.model)


def show(args):
    try:
        if args.local_id:
            obj = globals()[args.model.capitalize()](local_id=args.id)
        elif args.model == 'bag_action':
            obj = globals()[args.model.title().replace('_', '')](args.id)
        else:
            obj = globals()[args.model.capitalize()](args.id)
        if args.json:
            print json.dumps(obj.as_json, indent=2)
        else:
            print obj.to_string()
    except inv.Inventory404, e:
        sys.exit('No record found for %s %s' % (args.model, args.id))
    except Exception, e:
        log.exception('Error fetching %s "%s"' % (args.model, args.id))
        sys.exit('Error fetching data: %s' % e.msg)


def add(args):
    try:
        if args.model == 'bag_action':
            obj = globals()[args.model.title().replace('_', '')]()
        else:
            obj = globals()[args.model.capitalize()]()
        vals = [a for a in obj.readwrite()
                if getattr(args, a, None) is not None]
        for attr in vals:
            setattr(obj, attr, getattr(args, attr))
        # if no optional args passed, get metadata from user
        if vals == []:
            user_build_new_obj(obj, args.model)
        if args.model == 'bag':
            bag = bagit.Bag(obj.absolute_filesystem_path)
            obj.payload = build_bag_payload(bag, obj.absolute_filesystem_path)
        obj.save()

        #Add Inventory Bag Id in bag-info.txt
        if args.model == 'bag':
            bag.info['Bag-Id'] = str(obj.id)
            bag.save(manifests=True)

        if args.json:
            print json.dumps(obj.as_json, indent=2)
        else:
            if args.model == 'bag':
                print '%s added!\n' % args.model.capitalize()
            elif args.model == 'bag_action':
                print '%s recorded!\n' % args.model.title().replace('_', '')
            else:
                print '%s Created!\n' % args.model.capitalize()
            print obj.to_string().encode('utf8')

        #Record an action
        if args.model == 'bag':
            action = BagAction(bag=obj.id, timestamp=str(datetime.now()),
                               action='5', note='initiated by clint')
            action.save()

    except inv.Inventory404, e:
        sys.exit('Error creating record: %s' % e.msg)
    except bagit.BagError, e:
        sys.exit('Error registering Bag: %s\nTry to validate the Bag and then try re-adding it.' % e)


def edit(args):
    try:
        if 'local_id' in args and args.local_id:
            obj = globals()[args.model.capitalize()](local_id=args.local_id)
        elif args.model == 'bag_action':
            obj = globals()[args.model.title().replace('_', '')](args.id)
        else:
            obj = globals()[args.model.capitalize()](args.id)
        if args.json:
            print json.dumps(obj.as_json, indent=2)
        else:
            print obj.to_string()
    except inv.Inventory404, e:
        sys.exit('No record found for %s %s' % (args.model, args.id))
    try:
        edits = [a for a in obj.readwrite()
                 if getattr(args, a, None) is not None]
        for attr in edits:
            setattr(obj, attr, getattr(args, attr))
        # if no optional args passed, get metadata from user
        if edits == []:
            user_edit_obj(obj)
        if args.model == 'bag':
            bag = bagit.Bag(obj.absolute_filesystem_path)
            obj.payload = build_bag_payload(bag, obj.absolute_filesystem_path)
        obj.save()
        if args.json:
            print json.dumps(obj.as_json, indent=2)
        else:
            if args.model == 'bag_action':
                print '\n%s Edited!\n' % args.model.title().replace('_', '')
            else:
                print '\n%s Edited!\n' % args.model.capitalize()
            print obj.to_string()
    except inv.Inventory404, e:
        sys.exit('Error editing record: %s' % e.msg)


def delete(args):
    if not args.force:
        ans = ''
        ans = raw_input('Please confirm by typing "Yes": ')
        if ans != 'Yes':
            return
    response = inv._delete(args.model.replace('_', ''), args.id)
    if args.json:
        # TODO: status code perhaps? see
        # https://github.com/gwu-libraries/clint/issues/49
        pass
    else:
        if response.status_code == 204:
            print 'Successful deletion of %s %s' % (args.model, args.id)
        else:
            log.exception('response.status_code: %s' % response.status_code)
            log.debug('response.text: %s' % response.text)
            sys.exit('Error deleting %s %s' % (args.model, args.id))


def user_build_new_obj(obj, model):
    if model == 'bag_action':
        print 'Enter field values for new %s' % model.title().replace('_', '')
    else:
        print 'Enter field values for new %s' % model
    for attr, opts in obj.writeopts():
        if attr == 'created':
            value = str(datetime.now())
        elif model == 'bag' and attr == 'payload':
            continue
        else:
            if model == 'item' and attr == 'collection':
                value = get_user_input(obj, attr, opts, no_prefill=False)
            elif model == 'bag_action' and attr == 'timestamp':
                obj.timestamp = str(datetime.now())
                value = get_user_input(obj, attr, opts, no_prefill=False)
            else:
                value = get_user_input(obj, attr, opts, no_prefill=True)
        setattr(obj, attr, value)


def user_edit_obj(obj):
    print '\nEditable Fields'
    for attr, opts in obj.writeopts():
        if attr == 'payload':
            continue
        value = get_user_input(obj, attr, opts)
        setattr(obj, attr, value)


def get_user_input(obj, attr, opts, no_prefill=False):
    if attr == 'collection' and not getattr(obj, attr) and obj.project:
        setattr(obj, attr, obj.project.collection)

    if opts:
        optlist = ', '.join(['%s=%s' % (k, v) for k, v in opts.items()])
        prompt = '%s [Options: %s]: ' % (attr, optlist)
    else:
        prompt = '%s: ' % attr
    if no_prefill or not getattr(obj, attr):
        prefill = ''
    else:
        if (hasattr(obj, 'relations') and attr in obj.relations) \
                or (getattr(obj, attr) and hasattr(getattr(obj, attr), 'id')):
            prefill = getattr(obj, attr).id
        else:
            prefill = getattr(obj, attr)
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)
    try:
        return raw_input(prompt)
    finally:
        readline.set_startup_hook()


def build_bag_payload(bagitbag, path):
    payload = []
    for f in bagitbag.payload_files():
        size = os.path.getsize(os.path.join(path, f))
        payload.append('%s %s' % (f, size))
    return '\n'.join(payload)


def bag(args):
    # try to parse the optional fields
    addb = argparse.ArgumentParser()
    if args.remainder:
        addb.add_argument('-n', '--bagname', help='Identifier/name of the bag')
        addb.add_argument('-t', '--bag_type', choices=bag_types,
                          help='Type of bag')
        addb.add_argument('-p', '--path',
                          help='Path to bag from server root',
                          dest='absolute_filesystem_path')
        addb.add_argument('-y', '--payload', help='Payload of the bag')
        addb.add_argument('-m', '--machine',
                          help='Machine this bag is stored on')
        addb.add_argument('-i', '--item',
                          help='Item this bag is associated with')
        addb.add_argument('-c', '--created',
                          help='Timestamp when this bag was created')
        addb.add_argument('--model', default='bag')
        addb.add_argument('--force',
                          help='Forcefully bag an existing bag path',
                          action='store_true', default=False)
        addb.add_argument('-a', '--params',
                          help='Additional params for Bagit info file.')
        addb.set_defaults(func=add)
    try:
        bag = bagit.Bag(args.path)

        if bag.is_valid():
            bag_args = addb.parse_args(args.remainder)
            if not bag_args.__contains__('force'):
                print """The path provided is already a Bag. If you want to rebag an existing Bag use command "./clint rebag <PATH_TO_BAG>". If you want to forcefully bag an existing Bag, use the --force flag."""
                create_bag_ans = raw_input('Are you sure you want to continue and'
                                           ' create a new Bag for the path - <' +
                                           args.path + '>?(y or n):')
                while create_bag_ans.upper() not in ['Y', 'N', 'YES', 'NO']:
                    create_bag_ans = raw_input('Are you sure you want to continue'
                                               'and create a new Bag for the path '
                                               '- <' + args.path + '>? (y or n):')
                if create_bag_ans.upper() in ['N', 'NO']:
                    return
    except bagit.BagError:
        print 'Creating new Bag for path - <' + args.path + '>'

    try:
        # Additional params to be passed to Bagit to be included in
        # the bag-info.txt file
        params = {}
        if args.remainder:
            bag_args = addb.parse_args(args.remainder)
            if bag_args.params:
                params = ast.literal_eval(bag_args.params)

        # first create the bag
        bag = bagit.make_bag(args.path, params)
        if args.json:
            print json.dumps(bag.as_json, indent=2)
        else:
            print 'Bag created!'
            pprint(bag.entries)
        # also create the inventory object
        obj = Bag()
        # load payload
        obj.payload = build_bag_payload(bag, args.path)
        # load path and bagname values
        bagdir, bagname = os.path.split(args.path)
        obj.bagname = bagname
        obj.path = os.path.abspath(os.path.join(os.getcwd(), bagdir, bagname))
        # try to parse the optional fields
        if args.remainder:
            addb = argparse.ArgumentParser()
            addb.add_argument('-n', '--bagname',
                              help='Identifier/name of the bag')
            addb.add_argument('-t', '--bag_type', choices=bag_types,
                              help='Type of bag')
            addb.add_argument('-p', '--path',
                              help='Path to bag from server root')
            addb.add_argument('-y', '--payload', help='Payload of the bag')
            addb.add_argument('-m', '--machine',
                              help='Machine this bag is stored on')
            addb.add_argument('-i', '--item',
                              help='Item this bag is associated with')
            addb.add_argument('-c', '--created',
                              help='Timestamp when this bag was created')
            addb.add_argument('--model', default='bag')
            addb.set_defaults(func=add)
            addbargs = addb.parse_args(args.remainder)
            vals = [a for a in obj.readwrite()
                    if getattr(addbargs, a, None) is not None]
            log.debug('vals: %s' % vals)
            for attr in vals:
                setattr(obj, attr, getattr(addbargs, attr))
        # otherwise prompt the user
        else:
            user_build_new_obj(obj, 'bag')
        # adjust the bagname based on arguments
        dirname, bagname = os.path.split(args.path)
        if obj.bagname and obj.bagname != bagname:
            newpath = os.path.join(dirname, obj.bagname.replace('/', '_'))
            shutil.move(args.path, newpath)
            obj.path = newpath
        obj.save()

        #Change permissions for the 'data' directory inside the bagged folder
        datapath = os.path.join(obj.absolute_filesystem_path, 'data')
        os.chmod(datapath, 0755)

        #Add Inventory Bag Id in bag-info.txt
        bag.info["Bag-Id"] = str(obj.id)
        bag.save(manifests=True)

        if args.json:
            print json.dumps(obj.as_json, indent=2)
        else:
            print obj.to_string()

        #Record an action
        action = BagAction(bag=obj.id, timestamp=str(datetime.now()),
                           action='5', note='initiated by clint')
        action.save()
    except OSError:
        print 'Bag already exists'
        ans = ''
        while ans.upper() not in ['Y', 'N', 'YES', 'NO']:
            ans = raw_input('Shall I update it (rebag)? [yes/no] ')
        if ans.upper() in ['Y', 'YES']:
            rebag(args)
    except Exception, e:
        sys.exit('Error making bag\n%s' % e)


def rebag(args):
    # Ideally, this behavior should be included in the bagit.py package
    # remove bag info and manifest files
    bagpath = args.path
    old_bag = bagit.Bag(bagpath)
    bag_id = old_bag.info['Bag-Id']

    for f in os.listdir(bagpath):
        fpath = os.path.join(bagpath, f)
        if os.path.isfile(fpath):
            os.remove(fpath)
    # move subdirs in data back to bag root
    datapath = os.path.join(bagpath, 'data')
    for subd in os.listdir(datapath):
        shutil.move(os.path.join(datapath, subd), os.path.join(bagpath, subd))
    # remove data dir
    os.removedirs(datapath)
    # bag it again
    bag = bagit.make_bag(args.path)
    print 'Bag updated!'
    pprint(bag.entries)
    # also create the inventory object
    obj = Bag(id=bag_id)
    obj._load_properties()
    # load payload
    obj.payload = build_bag_payload(bag, bagpath)
    obj.save()
    action = BagAction(bag=bag_id, timestamp=str(datetime.now()),
                       action='1', note='initiated by clint')
    action.save()
    print 'Action recorded in Inventory'


def validate(args):
    """Validates if the Bag is valid or not. This function uses the
    bagit's 'validate' method to match file checksums. If the folder
    structure of the Bag provided is incorrect, bagit throws an error
    which is handled in the 'except' block. If the checksum validations
    fail, this function exits by displaying a message in the 'else' part of
    the outermost 'if' statement. In order to view which files have failed
    checksum valdiation, logging level must be set to DEBUG in the settings
    file"""
    try:
        bag = bagit.Bag(args.path)
        if bag.is_valid():
            if 'Bag-Id' in bag.info:
                bag_id = bag.info['Bag-Id']
                action = BagAction(bag=bag_id, timestamp=str(datetime.now()),
                                   action='3', note='initiated by clint')
                action.save()
                if args.json:
                    print json.dumps(action.as_json, indent=2)
                else:
                    print 'Bag is valid!'
                    print 'action id: %s' % action.id
                    print action.to_string()
            else:
                print 'Bag is valid, but not registered with Inventory.'
        else:
            sys.exit('Bag is NOT valid')
    except bagit.BagError,  e:
        sys.exit('Bag is NOT valid.\n' + e.message)


def copy(args):
    pass


def move(args):
    print 'Move operations not supported yet'


#This function is set as a completer for readline
# to enable tab autocomplete for file paths while
# reading input from user
def complete(text, state):
    return (glob.glob(text + '*') + [None])[state]


def main():
    # create clint level parser
    parser = argparse.ArgumentParser(
        description='A command line tool for Inventory operations')
    parser.add_argument('-j', '--json', action='store_true',
                        default=False, help='render output as JSON')

    # add subparsers for each command
    subparsers = parser.add_subparsers()

    # parser for the "show" command
    show_parser = subparsers.add_parser('show',
        help='Display metadata for an Inventory object')
    show_parser.add_argument('model', choices=models,
        help='type of object to be acted on')
    show_parser.add_argument('id', help='identifier of the object')
    show_parser.add_argument('-l', '--local_id', action="store_true",
        help='Set if you wish to use a local identifier (barcode)')
    show_parser.set_defaults(func=show)

    #parser for the "list" command
    list_parser = subparsers.add_parser('list',
                                        help='List objects in the inventory')
    list_parser.set_defaults(func=ls)
    # add subparsers for each kind of object
    listsubpar = list_parser.add_subparsers()
    # list collection
    listc = listsubpar.add_parser('collection',
                                  help='List collections in Inventory')
    listc.add_argument('-n', '--name', help='Name of the Collection')
    listc.add_argument('-d', '--description',
                       help='Description of the Collection')
    listc.add_argument('-m', '--contact_person',
                       help='Contact Person of the Collection')
    listc.add_argument('-l', '--local_id',
                       help='Local identifier of the Collection')
    listc.add_argument('--model', default='collection')
    # add project
    listp = listsubpar.add_parser('project', help='Add a project to Inventory')
    listp.add_argument('-n', '--name', help='Name of the project')
    listp.add_argument('-c', '--collection',
                       help='ID of the collection this project feeds')
    listp.add_argument('--model', default='project')
    # add item
    listi = listsubpar.add_parser('item', help='Add an item to Inventory')
    listi.add_argument('-t', '--title', help='Title of the item')
    listi.add_argument('-l', '--local_id', help='Alt/local ID of the item')
    listi.add_argument('-p', '--project',
                       help='Project this item is associated with')
    listi.add_argument('-c', '--collection',
                       help='Collection this item is associated with')
    listi.add_argument('-o', '--original-item-type', choices=orig_item_types,
                       help='The type of object this digital item came from')
    listi.add_argument('-n', '--notes', help='Notes about the item')
    listi.add_argument('--model', default='item')
    # add bag
    listb = listsubpar.add_parser('bag', help='Add a bag to the Inventory')
    listb.add_argument('-n', '--bagname', help='Identifier/name of the bag')
    listb.add_argument('-t', '--bag_type', choices=bag_types,
                       help='Type of bag')
    listb.add_argument('-p', '--path', help='Path to bag from server root')
    listb.add_argument('-m', '--machine', help='Machine this bag is stored on')
    listb.add_argument('-i', '--item', help='Item this bag is associated with')
    listb.add_argument('-c', '--created',
                       help='Timestamp when this bag was created')
    listb.add_argument('--model', default='bag')
    # add machine
    listm = listsubpar.add_parser('machine',
                                  help='Add a machine to the Inventory')
    listm.add_argument('-n', '--name', help='Name of the machine')
    listm.add_argument('-u', '--url', help='URL of the machine')
    listm.add_argument('-i', '--ip', help='IP address of the machine')
    listm.add_argument('-o', '--notes', help='Notes about the machine')
    listm.add_argument('--model', default='machine')

    listba = listsubpar.add_parser('bag_action',
                                   help='Record a bag action in Inventory')
    listba.add_argument('-b', '--bag', help='System identifier of the Bag')
    listba.add_argument('-t', '--timestamp',
                        help='Timestamp of the performed action')
    listba.add_argument('-a', '--action', help='Type of Bag action',
                        choices=actions)
    listba.add_argument('-n', '--note', help='Notes about the Bag action')
    listba.add_argument('--model', default='bag_action')

    # parser for the "add" command
    add_parser = subparsers.add_parser('add',
        help='Add a new object to the Inventory')
    add_parser.set_defaults(func=add)
    # add subsubparser for various object types in "add" command
    addsubpar = add_parser.add_subparsers()
    # add collection
    addc = addsubpar.add_parser('collection',
        help='Add a collection to Inventory')
    addc.add_argument('-n', '--name', help='Name of the Collection')
    addc.add_argument('-d', '--description',
        help='Description of the Collection')
    addc.add_argument('-m', '--contact_person', help='Contact Person of the Collection')
    addc.add_argument('-l', '--local_id', help='Local identifier of the Collection')
    addc.add_argument('--model', default='collection')
    # add project
    addp = addsubpar.add_parser('project', help='Add a project to Inventory')
    addp.add_argument('-n', '--name', help='Name of the project')
    addp.add_argument('-c', '--collection',
        help='ID of the collection this project feeds')
    addp.add_argument('--model', default='project')
    # add item
    addi = addsubpar.add_parser('item', help='Add an item to Inventory')
    addi.add_argument('-t', '--title', help='Title of the item')
    addi.add_argument('-l', '--local_id', help='Alt/local ID of the item')
    addi.add_argument('-p', '--project',
        help='Project this item is associated with')
    addi.add_argument('-c', '--collection',
        help='Collection this item is associated with')
    addi.add_argument('-o', '--original-item-type', choices=orig_item_types,
        help='The type of object this digital item came from')
    addi.add_argument('-n', '--notes', help='Notes about the item')
    addi.add_argument('-a', '--access_loc', help='Public url for the content')
    addi.add_argument('--model', default='item')
    # add bag
    addb = addsubpar.add_parser('bag', help='Add a bag to the Inventory')
    addb.add_argument('-n', '--bagname', help='Identifier/name of the bag')
    addb.add_argument('-t', '--bag_type', choices=bag_types,
        help='Type of bag')
    addb.add_argument('-p', '--path', help='Path to bag from server root', dest='absolute_filesystem_path')
    addb.add_argument('-y', '--payload', help='Payload of the bag')
    addb.add_argument('-m', '--machine', help='Machine this bag is stored on')
    addb.add_argument('-i', '--item', help='Item this bag is associated with')
    addb.add_argument('-c', '--created',
        help='Timestamp when this bag was created')
    addb.add_argument('--force', help='Forcefully bag an existing bag path', action='store_true')
    addb.add_argument('-a', '--params', help='Additional params for Bagit info file.')
    addb.add_argument('--model', default='bag')
    # add machine
    addm = addsubpar.add_parser('machine',
        help='Add a machine to the Inventory')
    addm.add_argument('-n', '--name', help='Name of the machine')
    addm.add_argument('-u', '--url', help='URL of the machine')
    addm.add_argument('-i', '--ip', help='IP address of the machine')
    addm.add_argument('-o', '--notes', help='Notes about the machine')
    addm.add_argument('--model', default='machine')

    # add an bag_action
    addba = addsubpar.add_parser('bag_action',
                                 help='Record a bag action in Inventory')
    addba.add_argument('-b', '--bag', help='System identifier of the Bag')
    addba.add_argument('-t', '--timestamp',
                       help='Timestamp of the performed action')
    addba.add_argument('-a', '--action', help='Type of Bag action',
                       choices=actions)
    addba.add_argument('-n', '--note', help='Notes about the Bag action')
    addba.add_argument('--model', default='bag_action')

    # parser for the "edit" command
    edit_parser = subparsers.add_parser('edit',
        help='Edit the metadata of an Inventory object')
    edit_parser.set_defaults(func=edit)
    # add subsubparser for various object types in "edit" command
    editsubpar = edit_parser.add_subparsers()
    # edit collection
    editc = editsubpar.add_parser('collection',
        help='Edit a collection in the Inventory')
    editc.add_argument('id', help='identifier of the collection')
    editc.add_argument('-n', '--name', help='Name of the Collection')
    editc.add_argument('-d', '--description',
        help='Description of the Collection')
    editc.add_argument('-m', '--contact_person', help='Contact Person of the Collection')
    editc.add_argument('-l', '--local_id', help='Local identifier of the Collection')
    editc.add_argument('--model', default='collection')
    # edit project
    editp = editsubpar.add_parser('project',
        help='Edit a project in the Inventory')
    editp.add_argument('id', help='identifier of the project')
    editp.add_argument('-n', '--name', help='Name of the project')
    editp.add_argument('-c', '--collection',
        help='ID of the collection this project feeds')
    editp.add_argument('--model', default='project')
    # edit item
    editi = editsubpar.add_parser('item',
        help='Edit an item in the Inventory')
    editi.add_argument('-i', '--id', help='identifier of the item')
    editi.add_argument('-t', '--title', help='Title of the item')
    editi.add_argument('-l', '--local_id', help='Alt/local ID of the item')
    editi.add_argument('-p', '--project',
        help='Project this item is associated with')
    editi.add_argument('-c', '--collection',
        help='Collection this item is associated with')
    editi.add_argument('-o', '--original-item-type', choices=orig_item_types,
        help='The type of object this digital item came from')
    editi.add_argument('-n', '--notes', help='Notes about the item')
    editi.add_argument('-a', '--access_loc', help='Public url for the content')
    editi.add_argument('--model', default='item')
    # edit bag
    editb = editsubpar.add_parser('bag', help='Edit a bag in the Inventory')
    editb.add_argument('id', help='Identifier/name of the bag')
    editb.add_argument('-t', '--bag_type', choices=bag_types,
        help='Type of bag')
    editb.add_argument('-p', '--path', help='Path to bag from server root')
    editb.add_argument('-y', '--payload', help='Payload of the bag')
    editb.add_argument('-m', '--machine', help='Machine this bag is stored on')
    editb.add_argument('-i', '--item', help='Item this bag is associated with')
    editb.add_argument('-c', '--created',
        help='Timestamp when this bag was created')
    editb.add_argument('--model', default='bag')
    # edit machine
    editm = editsubpar.add_parser('machine',
        help='Edit a machine in the Inventory')
    editm.add_argument('id', help='identifier of the machine')
    editm.add_argument('-n', '--name', help='Name of the machine')
    editm.add_argument('-u', '--url', help='URL of the machine')
    editm.add_argument('-i', '--ip', help='IP address of the machine')
    editm.add_argument('-o', '--notes', help='Notes about the machine')
    editm.add_argument('--model', default='machine')

    # edit bag_action
    editba = editsubpar.add_parser('bag_action',
                                   help='Edit a Bag action in Inventory')
    editba.add_argument('id', help='identifier of the Bag action record')
    editba.add_argument('-b', '--bag', help='System identifier of the Bag')
    editba.add_argument('-t', '--timestamp',
                        help='Timestamp of the performed action')
    editba.add_argument('-a', '--action', help='Type of Bag action',
                        choices=actions)
    editba.add_argument('-n', '--note', help='Notes about the Bag action')
    editba.add_argument('--model', default='bag_action')

    # parser for the "delete" command
    del_parser = subparsers.add_parser('delete',
        help='Delete an object from the Inventory')
    del_parser.add_argument('model', choices=models,
        help='type of object to be acted on')
    del_parser.add_argument('id', default=None,
        help='identifier of the object')
    del_parser.add_argument('--force', action='store_true',
                            default=False,
                            help='force deletion (no confirmation)')
    del_parser.set_defaults(func=delete)

    # parser for the "bag" command
    bag_parser = subparsers.add_parser('bag', help='Make a bag')
    bag_parser.add_argument('path',
        help='Relative path of directory to convert to a bag')
    bag_parser.add_argument('remainder', nargs=argparse.REMAINDER)
    bag_parser.set_defaults(func=bag)

    rebag_parser = subparsers.add_parser('rebag',
        help='Repackage and rehash a bag')
    rebag_parser.add_argument('path', help='Relative path to the bag')
    rebag_parser.set_defaults(func=rebag)

    valid_parser = subparsers.add_parser('validate', help='Validate a bag')
    valid_parser.add_argument('path', help='Relative path to the bag')
    valid_parser.set_defaults(func=validate)

    copy_parser = subparsers.add_parser('copy', help='Copy a bag')
    copy_parser.add_argument('source', help='Relative path to the source bag')
    copy_parser.add_argument('target', help='Relative path to the target bag')
    copy_parser.set_defaults(func=copy)

    move_parser = subparsers.add_parser('move', help='Move a bag')
    move_parser.add_argument('source', help='Relative path to the source bag')
    move_parser.add_argument('target', help='Relative path to the target bag')
    move_parser.set_defaults(func=move)

    args = parser.parse_args()
    args.func(args)

    sys.exit(0)


if __name__ == '__main__':
    main()
