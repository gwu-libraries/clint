#! ENV/bin/python

import argparse
from datetime import datetime
import os
from pprint import pprint
import readline
import shutil

import bagit

from inventory import Machine, Collection, Project, Item, Bag, BagAction
import inventory as inv
import settings


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
models = ['machine', 'collection', 'project', 'item', 'bag']
orig_item_types = ['book', 'microfilm', 'audio', 'video', 'mixed',
    'other']
bag_types = ['access', 'preservation', 'export']


def ls(args):
    # add params to filter by foreignkey models
    params = {}
    for model in models:
        if model in args:
            val = getattr(args, model)
            if val is not None and val != '':
                params[model] = val
    res = inv._get(model=args.model, params=params)
    objects = res.json().get('objects', None)
    if not objects:
        print 'No %ss found' % args.model
    else:
        for index, obj in enumerate(objects, start=1):
            print '-----%s-----' % index
            if 'bagname' in obj.keys():
                print 'bagname: %s' % obj.pop('bagname')
            else:
                print 'id: %s'  % obj.pop('id')
            if 'name' in obj.keys():
                print 'name: %s' % obj.pop('name')
            elif 'title' in obj.keys():
                print 'title: %s'  % obj.pop('title')
            for k in sorted(obj.keys()):
                print '%s: %s' % (k, obj[k])
        print '----------\n%s total %ss' % (len(objects),args.model)


def show(args):
    try:
        if args.local_id:
            obj = globals()[args.model.capitalize()](local_id=args.id)
        else:
            obj = globals()[args.model.capitalize()](args.id)
        print obj.to_string()
    except inv.Inventory404, e:
        print 'No record found for %s %s' % (args.model, args.id)
    except Exception, e:
        print 'Error fetching data!\n', e


def add(args):
    try:
        obj = globals()[args.model.capitalize()]()
        vals = [a for a in obj.readwrite() if getattr(args, a, None) is not None]
        for attr in vals:
            setattr(obj, attr, getattr(args, attr))
        # if no optional args passed, get metadata from user
        if vals == []:
            user_build_new_obj(obj, args.model)
        obj.save()
        print '%s Created!\n' % args.model.capitalize()
        print obj.to_string()
    except inv.Inventory404, e:
        print 'Error creating record: %s' % e.msg


def edit(args):
    try:
        if 'localid' in args and args.localid:
            obj = globals()[args.model.capitalize()](local_id=args.localid)
        else:
            obj = globals()[args.model.capitalize()](args.id)
        print obj.to_string()
    except inv.Inventory404, e:
        print 'No record found for %s %s' % (args.model, args.id)
        return
    try:
        edits = [a for a in obj.readwrite() if getattr(args, a, None) is not None]
        for attr in edits:
            setattr(obj, attr, getattr(args, attr))
        # if no optional args passed, get metadata from user
        if edits == []:
            user_edit_obj(obj)
        obj.save()
        print '\n%s Edited!\n' % args.model.capitalize()
        print obj.to_string()
    except inv.Inventory404, e:
        print 'Error editing record: %s' % e.msg


def delete(args):
    response = inv._delete(args.model, args.id)
    if response.status_code == 204:
        print 'Successful deletion of %s %s' % (args.model, args.id)
    else:
        print 'Error deleting %s %s' % (args.model, args.id)


def user_build_new_obj(obj, model):
    print 'Enter field values for new %s' % model
    for attr, opts in obj.writeopts():
        if attr == 'created':
            value = str(datetime.now())
        elif model == 'bag' and attr == 'payload' and obj.payload:
            continue
        else:
            value = get_user_input(obj, attr, opts, no_prefill=True)
        setattr(obj, attr, value)


def user_edit_obj(obj):
    print '\nEditable Fields'
    for attr, opts in obj.writeopts():
        value = get_user_input(obj, attr, opts)
        setattr(obj, attr, value)


def get_user_input(obj, attr, opts, no_prefill=False):
    if opts:
        optlist = ', '.join(['%s=%s' % (k, v) for k, v in opts.items()])
        prompt = '%s [Options: %s]: ' % (attr, optlist)
    else:
        prompt = '%s: ' % attr
    if no_prefill or not getattr(obj, attr):
        prefill = ''
    else:
        if attr in obj.relations:
            prefill = getattr(obj, attr).id
        else:
            prefill = getattr(obj, attr)
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
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
    try:
        # first create the bag
        bag = bagit.make_bag(args.path)
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
            addb.add_argument('-n', '--bagname', help='Identifier/name of the bag')
            addb.add_argument('-t', '--bagtype', choices=bag_types,
                help='Type of bag')
            addb.add_argument('-p', '--path', help='Path to bag from server root')
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
            vals = [a for a in obj.readwrite() if getattr(addbargs, a, None) is not None]
            print 'vals: %s' % vals
            for attr in vals:
                setattr(obj, attr, getattr(addbargs, attr))
        # otherwise prompt the user
        else:
            user_build_new_obj(obj, 'bag')
        obj.save()
        # adjust the bagname based on arguments
        dirname, bagname = os.path.split(args.path)
        if obj.bagname and obj.bagname != bagname:
            newpath = os.path.join(dirname, obj.bagname.replace('/', '_'))
            shutil.move(args.path, newpath)
            obj.path = newpath
        obj.save()
        print obj.to_string()
    except OSError:
        print 'Bag already exists'
        ans = ''
        while ans.upper() not in ['Y', 'N', 'YES', 'NO']:
            ans = raw_input('Shall I update it (rebag)? [yes/no] ')
        if ans.upper() in ['Y', 'YES']:
            rebag(args)
    except Exception, e:
        print 'Error making bag\n%s' % e
        raise


def rebag(args):
    # Ideally, this behavior should be included in the bagit.py package
    # remove bag info and manifest files
    bagpath = args.path
    bagname = os.path.basename(bagpath)
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
    obj = Bag(bagname=bagname)
    obj._load_properties()
    # load payload
    obj.payload = build_bag_payload(bag, bagpath)
    obj.save()
    action = BagAction(bag=bagname, timestamp=str(datetime.now()),
        action='1', note='initiated by clint')
    action.save()
    print 'Action recorded in Inventory'


def validate(args):
    bag = bagit.Bag(args.path)
    if bag.is_valid():
        print 'Bag is valid!'
        bagname = os.path.basename(args.path)
        action = BagAction(bag=bagname, timestamp=str(datetime.now()),
            action='3', note='initiated by clint')
        action.save()
        print 'action id: %s' % action.id
        print action.to_string()
    else:
        print 'Bag is NOT valid'


def copy(args):
    pass


def move(args):
    print 'Move operations not supported yet'


def main():
    # create clint level parser
    parser = argparse.ArgumentParser(
        description='A command line tool for Inventory operations')
    subparsers = parser.add_subparsers()
    # add subparsers for each command

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
    list_parser = subparsers.add_parser('list', help='List objects in the inventory')
    list_parser.set_defaults(func=ls)
    # add subparsers for each kind of object
    listsubpar = list_parser.add_subparsers()
    # list collection
    listc = listsubpar.add_parser('collection', help='List collections in Inventory')
    listc.add_argument('-n', '--name', help='Name of the Collection')
    listc.add_argument('-d', '--description',
        help='Description of the Collection')
    listc.add_argument('-m', '--manager', help='Manager of the Collection')
    listc.add_argument('--model', default='collection')
    # add project
    listp = listsubpar.add_parser('project', help='Add a project to Inventory')
    listp.add_argument('-n', '--name', help='Name of the project')
    listp.add_argument('-m', '--manager', help='Manager of the project')
    listp.add_argument('-c', '--collection',
        help='ID of the collection this project feeds')
    listp.add_argument('--model', default='project')
    # add item
    listi = listsubpar.add_parser('item', help='Add an item to Inventory')
    listi.add_argument('-t', '--title', help='Title of the item')
    listi.add_argument('-l', '--localid', help='Alt/local ID of the item')
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
    listb.add_argument('-t', '--bagtype', choices=bag_types,
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
    addc.add_argument('-m', '--manager', help='Manager of the Collection')
    addc.add_argument('--model', default='collection')
    # add project
    addp = addsubpar.add_parser('project', help='Add a project to Inventory')
    addp.add_argument('-n', '--name', help='Name of the project')
    addp.add_argument('-m', '--manager', help='Manager of the project')
    addp.add_argument('-c', '--collection',
        help='ID of the collection this project feeds')
    addp.add_argument('--model', default='project')
    # add item
    addi = addsubpar.add_parser('item', help='Add an item to Inventory')
    addi.add_argument('-t', '--title', help='Title of the item')
    addi.add_argument('-l', '--localid', help='Alt/local ID of the item')
    addi.add_argument('-p', '--project',
        help='Project this item is associated with')
    addi.add_argument('-c', '--collection',
        help='Collection this item is associated with')
    addi.add_argument('-o', '--original-item-type', choices=orig_item_types,
        help='The type of object this digital item came from')
    addi.add_argument('-n', '--notes', help='Notes about the item')
    addi.add_argument('--model', default='item')
    # add bag
    addb = addsubpar.add_parser('bag', help='Add a bag to the Inventory')
    addb.add_argument('-n', '--bagname', help='Identifier/name of the bag')
    addb.add_argument('-t', '--bagtype', choices=bag_types,
        help='Type of bag')
    addb.add_argument('-p', '--path', help='Path to bag from server root')
    addb.add_argument('-y', '--payload', help='Payload of the bag')
    addb.add_argument('-m', '--machine', help='Machine this bag is stored on')
    addb.add_argument('-i', '--item', help='Item this bag is associated with')
    addb.add_argument('-c', '--created',
        help='Timestamp when this bag was created')
    addb.add_argument('--model', default='bag')
    # add machine
    addm = addsubpar.add_parser('machine',
        help='Add a machine to the Inventory')
    addm.add_argument('-n', '--name', help='Name of the machine')
    addm.add_argument('-u', '--url', help='URL of the machine')
    addm.add_argument('-i', '--ip', help='IP address of the machine')
    addm.add_argument('-o', '--notes', help='Notes about the machine')
    addm.add_argument('--model', default='machine')

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
    editc.add_argument('-m', '--manager', help='Manager of the Collection')
    editc.add_argument('--model', default='collection')
    # edit project
    editp = editsubpar.add_parser('project',
        help='Edit a project in the Inventory')
    editp.add_argument('id', help='identifier of the project')
    editp.add_argument('-n', '--name', help='Name of the project')
    editp.add_argument('-m', '--manager', help='Manager of the project')
    editp.add_argument('-c', '--collection',
        help='ID of the collection this project feeds')
    editp.add_argument('--model', default='project')
    # edit item
    editi = editsubpar.add_parser('item',
        help='Edit an item in the Inventory')
    editi.add_argument('-i', '--id', help='identifier of the item')
    editi.add_argument('-t', '--title', help='Title of the item')
    editi.add_argument('-l', '--localid', help='Alt/local ID of the item')
    editi.add_argument('-p', '--project',
        help='Project this item is associated with')
    editi.add_argument('-c', '--collection',
        help='Collection this item is associated with')
    editi.add_argument('-o', '--original-item-type', choices=orig_item_types,
        help='The type of object this digital item came from')
    editi.add_argument('-n', '--notes', help='Notes about the item')
    editi.add_argument('--model', default='item')
    # edit bag
    editb = editsubpar.add_parser('bag', help='Edit a bag in the Inventory')
    editb.add_argument('id', help='Identifier/name of the bag')
    editb.add_argument('-t', '--bagtype', choices=bag_types,
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

    # parser for the "delete" command
    del_parser = subparsers.add_parser('delete',
        help='Delete an object from the Inventory')
    del_parser.add_argument('model', choices=models,
        help='type of object to be acted on')
    del_parser.add_argument('id', default=None,
        help='identifier of the object')
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


if __name__ == '__main__':
    main()
