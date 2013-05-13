#! ENV/bin/python

import argparse

from inventory import Machine, Collection, Project, Item, Bag, _delete
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

def show(model, id):
    try:
        obj = globals()[model.capitalize()](id)
        print obj.to_string()
    except Inventory404, e:
        print 'No record found for %s %s' % (model, id)
    except Exception, e:
        print 'Error fetching data!\n', e


def add(model):
    try:
        obj = build_new_obj(model)
        print '%s Created!\n' % model.capitalize()
        print obj.to_string()
    except Exception, e:
        print 'Error creating record!\n', e
        raise


def edit(model, id, **kwargs):
    try:
        obj = globals()[model.capitalize()](id)
        edit_obj(obj)
        print '\n%s Edited!\n' % model.capitalize()
        print obj.to_string()
    except Inventory404, e:
        print 'No record found for %s %s' % (model, id)
    except Exception, e:
        print 'Error editing record!\n', e


def delete(model, id):
    response = _delete(model, id)
    if response.status_code == 204:
        print 'Successful deletion of %s %s' % (model, id)
    else:
        print 'Error deleting %s %s' % (model, id)


def build_new_obj(model):
    obj = globals()[model.capitalize()]()
    print 'Enter field values for new %s' % model
    for attr, opts in obj.writeopts():
        if opts:
            optlist = ', '.join(['%s=%s' % (k, v) for k, v in opts])
            prompt = '%s [Options: %s]: ' % (attr, optlist)
        else:
            prompt = '%s: ' % attr
        value = raw_input(prompt)
        setattr(obj, attr, value)
    return obj.save()

def edit_obj(obj):
    print obj.to_string()
    print '\nEditable Fields'
    for attr, opts in obj.writeopts():
        if opts:
            optlist = ', '.join(['%s=%s' % (k, v) for k, v in opts])
            prompt = '%s [Options: %s]: ' % (attr, optlist)
        else:
            prompt = '%s: ' % attr
        value = raw_input(prompt)
        setattr(obj, attr, value)
    return obj.save()

def main():

    actions = ['show', 'add', 'edit', 'delete', 'list']
    models = ['machine', 'collection', 'project', 'item', 'bag']

    parser = argparse.ArgumentParser(
        description='A command line tool for Inventory operations')
    parser.add_argument('action', choices=actions,
        help='action or subcommand to perform')
    parser.add_argument('model', choices=models,
        help='type of object to be acted on')
    parser.add_argument('-i', '--id', default=None,
        help='identifier of the object [optional for the "add" command]')

    try:
        args = parser.parse_args()
        kwargs = {}
        keys = [k for k in vars(args).keys() if getattr(args, k) and k != 'action']
        for key in keys:
                kwargs[key] = getattr(args, key)
        globals()[args.action](**kwargs)
    except:
        raise

if __name__ == '__main__':
    main()