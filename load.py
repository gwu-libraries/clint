#!/usr/bin/env python

"""
 Automate the following:
 
  % ./clint add item -t '143f0024' -l '143f0024' -c '38989/c01bn54c3177' -o other
  % ./clint bag /vol/staging/collections-bagged/gw_terror/143f0024 -n 143f0024 -t preservation -m 2 -i "38989/c010198w919x" -p "gw_terror/143f0024"
  % chmod guo+rx /vol/staging/collections-bagged/gw_terror/143f0024/data
  """

from optparse import OptionParser
import os
import subprocess
import time
import traceback

import bagit
 
from lxml import etree
 
PATHS_TO_PROCESS = 10000

if __name__ == '__main__':
    usage = 'usage: %prog [-o ITEMTYPE] COLLECTIONID DIR1 [DIR2 ...]'
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--itemtype', dest='itemtype', metavar='TYPE',
                      default='other', help='type of item')
    parser.add_option('-n', '--numparents', type=int, dest='numparents',
                      default=1,
                      help='number of parent dirs to include in access path')
    parser.add_option('-m', '--machine_id', type=int, dest='machine_id',
                      default=2,
                      help='system id of the storage machine')
    parser.add_option('-d', '--metadata-filename', type=str,
                      dest='metadata_filename',
                      help='name of metadata file to use for title search')
    parser.add_option('-x', '--title-xpath', type=str, dest='title_xpath',
                      help='xpath to use to search metadata_filename for title')
    options, args = parser.parse_args()
    if len(args) < 2:
        parser.error('COLLECTIONID and at least one DIR required')
    collection_id = args.pop(0)
    print 'collection_id:', collection_id
    for path in args[:PATHS_TO_PROCESS]:
        print 'process path:', path
        base_name = os.path.basename(path)
        print 'basename:', base_name
        if options.metadata_filename and options.title_xpath:
            try:
                md_filename = '%s/%s' % (path, options.metadata_filename)
                r = etree.parse(md_filename)
                titles = r.xpath(options.title_xpath)
                if len(titles) == 1:
                    title = titles[0].text
                print 'found title:', title
            except:
                print traceback.print_exc()
                title = base_name
        clint_line = ['./clint', 'add', 'item',
                      '-t', title,
                      '-l', base_name,
                      '-c', collection_id,
                      '-o', options.itemtype]
        print 'clint:', clint_line
        # in 2.7, subprocess.check_output instead of .communicate()
        out = subprocess.Popen(clint_line,
                               stdout=subprocess.PIPE).communicate()[0]
        print 'out:'
        print out
        time.sleep(1)
        for line in out.split('\n'):
            if ' id: ' in line:
                label, item_id = line.strip().split(' ')
                break
        print 'item_id:', item_id
        # now bag the content
        # % ./clint bag /vol/staging/collections-bagged/gw_terror/143f0024
        #       -n 143f0024 -t preservation -m 2 -i "38989/c010198w919x"
        #       -p "gw_terror/143f0024"
        bag = bagit.Bag(path)
        if not bag.is_valid(bag):
            access_path = base_name
            if options.numparents:
                parent_dir = os.path.dirname(path)
                relative_path = parent_dir.split(os.sep)[-options.numparents:]
                relative_path.append(base_name)
                access_path = os.sep.join(relative_path)
            print 'access_path:', access_path
            clint_line = ['./clint', 'bag', path,
                          '-n', base_name,
                          '-t', 'preservation',
                          '-m', str(options.machine_id),
                          '-i', item_id,
                          '-p', access_path]
            print 'clint_line 2:', clint_line
            out = subprocess.Popen(clint_line,
                                   stdout=subprocess.PIPE).communicate()[0]
            print 'out:', out
            time.sleep(1)
        # chmod guo+rx /vol/staging/collections-bagged/gw_terror/143f0024/data
        baginfo_filename = '%s/%s' % (path, 'bag-info.txt')
        with open(baginfo_filename, "a") as myfile:
            myfile.write('collection-id: ' + collection_id)
            myfile.write('item-id: ' + item_id)
            myfile.write('title :' + title)
        payload_path = os.sep.join([path, 'data'])
        print 'payload_path:', payload_path
        os.chmod(payload_path, 0755)
        print 'changed payload mode'
