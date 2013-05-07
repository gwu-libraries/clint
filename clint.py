#! ENV/bin/python

import argparse

from inventory import *
import settings


'''
List of potential clint commands

Interacting with Inventory
--------------------------
show collection/item/bag <id>
add collection/item/bag [<id>]
edit collection/item/bag <id>
delete collection/item/bag <id>

Managing Bags
-------------
makebag <dir>
rebag <dir>
copy <id> 
move bag <id>
validate bag <id>
'''

def show(model, id):
    try:
        model = model.capitalize()
        obj = globals()[model](id)
        print obj.to_string()
    except Inventory404, e:
        print 'No record found for %s %s' % (model, id)
        raise
    except Exception, e:
        print 'Error fetching data!\n', e
        raise

"""
def add(model, id):
    response = inventory.post(model, id, **kwargs)
    if response.status_code == 201:
        if not id:
            url = response.headers['Location'] 
            id = url.split('/')[-2:].join('/')
        print 'Successful creation of %s %s' % (model, id)
    else:
        print 'Error adding %s' % model


def edit(model, id, **kwargs):
    response = inventory.patch(model, id, kwargs)
    if response.status_code == 202:
        print 'Successful edit of %s %s' % (model, id)
    else:
        print 'Error editing %s %s' % (model, id)


def delete(model, id):
    response = inventory.delete(model, id)
    if response.status_code == 204:
        print 'Successful deletion of %s %s' % (model, id)
    else:
        print 'Error deleting %s %s' % (model, id)
"""


def main():

    actions = ['show', 'add', 'edit', 'delete']
    models = ['collection', 'project', 'item', 'bag']

    parser = argparse.ArgumentParser(
        description='A command line tool for Inventory operations')
    parser.add_argument('action', choices=actions, default='show',
        help='action or subcommand to perform')
    parser.add_argument('model', choices=models,
        help='type of object to be acted on')
    parser.add_argument('id', default=None,
        help='identifier of the object [optional for the "add" command]')

    try:
        args = parser.parse_args()
        globals()[args.action](args.model, args.id)
    except:
        raise

if __name__ == '__main__':
    main()