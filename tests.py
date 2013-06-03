import unittest
from unittest import skipIf

import inventory
import settings
from settings import inventory_sandbox as sandbox


settings.INVENTORY_CREDENTIALS = sandbox


@skipIf(not all([sandbox.get(k) for k in sandbox.keys()]),
    'sandbox inventory not set')
class TestInventoryHTTPMethods(unittest.TestCase):

    def testget(self):
        '''
        This test only works with a prepopulated inventory system.
        Use the fixture data in the inventory repository:
        $: python manage loaddata fake_stuff.json
        '''
        # get a collection
        res1 = inventory._get('collection', '12345/c00000000001')
        self.assertEqual(res1.status_code, 200)
        j1 = res1.json()
        self.assertEqual(j1['name'], 'Fake Collection 1')
        # get a project
        res2 = inventory._get('project', '12345/p000000001')
        self.assertEqual(res2.status_code, 200)
        j2 = res2.json()
        self.assertEqual(j2['name'], 'Fake Project 1')
        # get an item
        res3 = inventory._get('item', '12345/i000000031')
        self.assertEqual(res3.status_code, 200)
        j3 = res3.json()
        self.assertEqual(j3['title'], 'Fake Audio 1')
        # get a bag
        res4 = inventory._get('bag', '12345/i0000000031_ACCESS_BAG')
        self.assertEqual(res4.status_code, 200)
        j4 = res4.json()
        self.assertEqual(j4['item'], '/api/v1/item/12345/i000000031/')

    def testpostanddelete(self):
        # create a collection
        cdata = {"id": "12345/100000000001", "name": "Test Collection 1",
            "description": "A test collection", "manager": "Joshua Gomez",
            "created": "2013-04-25 14:19:01.351058"}
        response1 = inventory._post('collection', **cdata)
        self.assertEqual(response1.status_code, 201)
        # now delete it
        response2 = inventory._delete('collection', '12345/100000000001')
        self.assertEqual(response2.status_code, 204)

    def testbadpost(self):
        # create a collection with a name that is too long
        name = 'name' * 65
        cdata = {"id": "", "manager": "Joshua Gomez", "name": name,
            "description": "A test collection"}
        response1 = inventory._post('collection', **cdata)
        self.assertEqual(response1.status_code, 500)
        # That should really be a 400, but tatypie returns a 500, patch pending

    def testpatch(self):
        cdata = {'description': 'Patch Worked!'}
        response = inventory._patch('collection', '12345/c00000000001', **cdata)
        self.assertEqual(response.status_code, 202)

if __name__ == '__main__':
    unittest.main()
