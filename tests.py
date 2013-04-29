import unittest

from inventory import Inventory
from settings import inventory_sandbox as sandbox


class TestInventoryClass(unittest.TestCase):

    def setUp(self):
        self.inv = Inventory(sandbox['user'], sandbox['apikey'],
            sandbox['apiversion'], sandbox['url'], sandbox['port'])

    def testget(self):
        '''
        This test only works with a prepopulated inventory system.
        Use the fixture data in the inventory repository:
        $: python manage loaddata fake_stuff.json
        '''
        # get a collection
        res1 = self.inv.get('collection', '12345/c00000000001')
        self.assertEqual(res1.status_code, 200)
        j1 = res1.json()
        self.assertEqual(j1['name'], 'Fake Collection 1')
        # get a project
        res2 = self.inv.get('project', '12345/p000000001')
        self.assertEqual(res2.status_code, 200)
        j2 = res2.json()
        self.assertEqual(j2['name'], 'Fake Project 1')
        # get an item
        res3 = self.inv.get('item', '12345/i000000031')
        self.assertEqual(res1.status_code, 200)
        j3 = res3.json()
        self.assertEqual(j3['title'], 'Fake Audio 1')
        # get a bag
        res4 = self.inv.get('bag', '12345/i0000000031_ACCESS_BAG')
        self.assertEqual(res4.status_code, 200)
        j4 = res4.json()
        self.assertEqual(j4['item'], '/api/v1/item/12345/i000000031/')

    def testpostanddelete(self):
        # create a collection
        cdata = {"id": "12345/100000000001", "name": "Test Collection 1",
            "description": "A test collection", "manager": "Joshua Gomez",
            "created": "2013-04-25 14:19:01.351058"}
        response1 = self.inv.post('collection', **cdata)
        self.assertEqual(response1.status_code, 201)
        # now delete it
        response2 = self.inv.delete('collection', '12345/100000000001')
        self.assertEqual(response2.status_code, 204)

    def testpatch(self):
        cdata = {'description': 'Patch Worked!'}
        response = self.inv.patch('collection', '12345/c00000000001', **cdata)
        self.assertEqual(response.status_code, 202)

if __name__ == '__main__':
    unittest.main()
