import unittest
from unittest import skipIf

import inventory as inv
from inventory import parse_id
import settings
from settings import inventory_sandbox as sandbox


settings.INVENTORY_CREDENTIALS = sandbox


@skipIf(not all([sandbox.get(k) for k in sandbox.keys()]),
    'sandbox inventory not set')
class TestInventoryHTTPMethods(unittest.TestCase):
    '''
    These tests require a live sandbox inventory to communicate with
    '''

    def setUp(self):
        '''setUp is also a test of the post method'''
        # create a machine object
        mdata = {"url": "http://storage1.gwu.edu", "name": "Test Machine 1"}
        res1 = inv._post('machine', **mdata)
        self.assertEqual(res1.status_code, 201)
        self.machine_id = parse_id(res1.headers['location'])
        # create a collection object
        cdata = {"name": "Test Collection 1", "created": "2013-06-01",
            "description": "testy", "manager": "Lemmy Kilmeister",
            "access_loc": "http://diglib.gwu.edu/collection/1"}
        res2 = inv._post('collection', **cdata)
        self.assertEqual(res2.status_code, 201)
        self.collection_id = parse_id(res2.headers['location'])
        # create a project object
        pdata = {"name": "Test Project 1", "manager": "Mike Patton",
            "collection": parse_id(res2.headers['location'], uri=True),
            "start_date": "2013-06-01",
            "end_date": "2013-07-01"}
        res3 = inv._post('project', **pdata)
        self.assertEqual(res3.status_code, 201)
        self.project_id = parse_id(res3.headers['location'])
        # create an item object
        idata = {"title": "Test Item 1", "local_id": "123456789",
            "collection": parse_id(res2.headers['location'], uri=True),
            "project": parse_id(res3.headers['location'], uri=True),
            "created": "2013-06-01",
            "original_item_type": "1", "notes": "nonoteworthynotes",
            "access_loc": "http://diglib.gwu.edu/item/1"}
        res4 = inv._post('item', **idata)
        self.assertEqual(res4.status_code, 201)
        self.item_id = parse_id(res4.headers['location'])
        # create a bag object
        bdata = {"bagname": "Test Bag 1", "created": "2013-06-01",
            "item": parse_id(res4.headers['location'], uri=True),
            "machine": parse_id(res1.headers['location'], uri=True),
            "path": "mount1/bag1", "bag_type": "1"}
        res5 = inv._post('bag', **bdata)
        self.assertEqual(res5.status_code, 201)
        self.bag_id = parse_id(res5.headers['location'])

    def tearDown(self):
        '''tearDown is also a test of the delete method'''
        # delete all objects created in setUp
        # go in reverse order until cascade rules have been removed from inventory
        res5 = inv._delete('bag', self.bag_id)
        self.assertEqual(res5.status_code, 204)
        res4 = inv._delete('item', self.item_id)
        self.assertEqual(res4.status_code, 204)
        res3 = inv._delete('project', self.project_id)
        self.assertEqual(res3.status_code, 204)
        res2 = inv._delete('collection', self.collection_id)
        self.assertEqual(res2.status_code, 204)
        res1 = inv._delete('machine', self.machine_id)
        self.assertEqual(res1.status_code, 204)

    def testget(self):
        # get a machine
        res1 = inv._get('machine', self.machine_id)
        self.assertEqual(res1.status_code, 200)
        j1 = res1.json()
        self.assertEqual(j1['name'], 'Test Machine 1')
        # get a collection
        res2 = inv._get('collection', self.collection_id)
        self.assertEqual(res2.status_code, 200)
        j2 = res2.json()
        self.assertEqual(j2['name'], 'Test Collection 1')
        # get a project
        res3 = inv._get('project', self.project_id)
        self.assertEqual(res3.status_code, 200)
        j3 = res3.json()
        self.assertEqual(j3['name'], 'Test Project 1')
        # get an item
        res4 = inv._get('item', self.item_id)
        self.assertEqual(res4.status_code, 200)
        j4 = res4.json()
        self.assertEqual(j4['title'], 'Test Item 1')
        # get a bag
        res5 = inv._get('bag', self.bag_id)
        self.assertEqual(res5.status_code, 200)
        j5 = res5.json()
        self.assertEqual(j5['objects'][0]['item'], '/api/v1/item/%s/' % self.item_id)

    def testput(self):
        pass

    def testpatch(self):
        pass

    def testbadpost(self):
        # create a collection with a name that is too long
        name = 'name' * 65
        cdata = {"id": "", "manager": "Joshua Gomez", "name": name,
            "description": "A test collection"}
        response1 = inv._post('collection', **cdata)
        self.assertEqual(response1.status_code, 500)
        # That should really be a 400, but tastypie returns a 500, patch pending

    """
    def testpatch(self):
        cdata = {'description': 'Patch Worked!'}
        response = inventory._patch('collection', '12345/c00000000001', **cdata)
        self.assertEqual(response.status_code, 202)
    """

if __name__ == '__main__':
    unittest.main()
