import os

from fabric.operations import put
from fabric.api import run, quiet, env, cd

import settings
import json
import csv
import bagit

from xlrd import open_workbook

env.always_use_pty = False
item_id = ''

BAG_TYPE = {
    '1': 'Access',
    '2': 'Preservation',
    '3': 'Export'
    }


def create_bag(bag_path, bag_name, bag_type, machine_id, item_id):
    if not os.path.exists(bag_path):
        raise IOError("Invalid directory '%s'" % bag_path)
    if not os.access(bag_path, os.R_OK) and not not os.access(bag_path, os.W_OK):
        raise IOError("Insufficient permissions '%s'" % bag_path)
    with cd(settings.CLINT_INSTALLATION_PATH):
        bag_cmd = [settings.CLINT_INSTALLATION_PATH + 'clint', 'bag', bag_path,
                   '-n', bag_name,
                   '-t', bag_type,
                   '-m', str(machine_id),
                   '-i', item_id]
        run("source ENV/bin/activate")
        run(" ".join(bag_cmd))


def register_item(title, base_name, collection_id, item_type, notes='', access_loc=''):
    global item_id
    with cd(settings.CLINT_INSTALLATION_PATH):
        register_cmd = [settings.CLINT_INSTALLATION_PATH + 'clint', 'add',
                        'item',
                        '-t', '"' + title + '"',
                        '-l', '"' + base_name + '"',
                        '-c', collection_id,
                        '-o', item_type]
        if notes:
            register_cmd.append('-n')
            register_cmd.append("'" + notes + "'")
        if access_loc:
            register_cmd.append('-a')
            register_cmd.append("'" + access_loc + "'")

        run("source ENV/bin/activate")
        result = run(" ".join(register_cmd))
        index = result.find('id:')
        index2 = result.find('\n', index)
        item_id = result[index+4:index2]


def add_bag(bag_name, bag_type, bag_path, machine_id, item_id):
    with cd(settings.CLINT_INSTALLATION_PATH):
        bag_cmd = [settings.CLINT_INSTALLATION_PATH + 'clint', 'add', 'bag',
                   '-n', bag_name,
                   '-p', bag_path,
                   '-m', machine_id,
                   '-t', bag_type,
                   '-i', item_id
                   ]
        run("source ENV/bin/activate")
        run(" ".join(bag_cmd))


def validate_bag(bag_path):
    with cd(settings.CLINT_INSTALLATION_PATH):
        bag_cmd = [settings.CLINT_INSTALLATION_PATH + 'clint', 'validate',
                   bag_path]
        run("source ENV/bin/activate")
        run(" ".join(bag_cmd))


def process_bag(name, local_id, col_id, item_type, b_type, b_path, mach_id, b_name, item_notes='', item_access_loc=''):
    global item_id
    register_item(name, local_id, col_id, item_type, item_notes, item_access_loc)
    add_bag(b_name, b_type, b_path, mach_id, item_id)
    validate_bag(b_path)


def bag_and_register(item_name, local_id, collection_id, item_type,
                     bag_name, bag_path, bag_type, machine_id, item_notes='',
                     item_access_loc=''):
    global item_id
    register_item(item_name, local_id, collection_id, item_type)
    create_bag(bag_path, bag_name, bag_type, machine_id, item_id)
    validate_bag(bag_path)


def verify_path_is_bag(bag_path):
    try:
        bag = bagit.Bag(bag_path)
        return True
    except:
        return False


def import_collection(filename):
    try:
        item_name = local_id = collection_id = item_type = bag_type = \
            bag_path = machine_id = bag_name = item_notes = \
            item_access_loc = ''
        file_extension = os.path.splitext(filename)[1]
        if file_extension == '.csv':
            reader = csv.DictReader(open(filename))
            for row in reader:
                collection_id = row['Collection ID']
                item_name = row['Item Name']
                local_id = row['Local ID']
                item_type = row['Item Type']
                item_notes = row['Item Notes']
                item_access_loc = row['Item Access Location']
                bag_name = row['Bag Name']
                bag_path = row['Bag Path']
                bag_type = row['Bag Type']
                machine_id = row['Machine ID']
                if(verify_path_is_bag(bag_path)):
                    process_bag(name=item_name, local_id=local_id,
                                col_id=collection_id, item_type=item_type,
                                b_type=bag_type, b_path=bag_path,
                                mach_id=machine_id, b_name=bag_name)
                else:
                    bag_and_register(item_name, local_id, collection_id, item_type,
                                     bag_name, bag_path, bag_type, machine_id,
                                     item_notes, item_access_loc)
                print 'Successfully added Bag: ' + row['Bag Name']

        elif file_extension in ['.xls', '.xlsx']:
            excel_file = open_workbook(filename)
            for sheet_name in excel_file.sheet_names():
                sheet = excel_file.sheet_by_name(sheet_name)
                for curr_row in range(1, sheet.nrows):
                    row_values = sheet.row_values(curr_row)
                    collection_id = row_values[0]
                    item_name = row_values[1]
                    local_id = row_values[2]
                    item_type = row_values[3]
                    item_notes = row_values[4]
                    item_access_loc = row_values[5]
                    bag_name = row_values[6]
                    bag_path = row_values[7]
                    bag_type = row_values[8]
                    machine_id = row_values[9]
                    if(verify_path_is_bag(bag_path)):
                        process_bag(name=item_name, local_id=local_id,
                                    col_id=collection_id, item_type=item_type,
                                    b_type=bag_type, b_path=bag_path,
                                    mach_id=machine_id, b_name=bag_name)
                    else:
                        bag_and_register(item_name, local_id, collection_id, item_type,
                                         bag_name, bag_path, bag_type, machine_id, item_notes,
                                         item_access_loc)
                    print 'Successfully added Bag: ' + bag_name
        else:
            print 'Invalid file: ' + filename
    except Exception, e:
        print 'Error: ' + str(e)


def rsync(local, remote, sudo=False):
    if not os.path.exists(local):
        raise IOError("Invalid directory '%s'" % local)
    if not os.access(local, os.R_OK):
        raise IOError("Cannot read directory '%s'" % local)
    put(local, remote, use_sudo=sudo)


def space_available(local, remote_drive):
    filesize = os.path.getsize(local)
    x = run("df -hP | awk 'NR>1{print $1,$2,$4,$5}' | sed -e's/%//g'")
    # create a list of lists with first item being the drive
    # second item being the total space
    # and the third item being free space
    drives = [y.split() for y in x.split('\n')]
    for item in drives:
        if item[0] == remote_drive:
            free_space = convert_2_bytes(item[2])
            total_space = convert_2_bytes(item[1])
            percent_free_space = 100 - int(item[3])
            if percent_free_space > settings.FREE_PARTITION_SPACE:
                avail_space = free_space - (settings.FREE_PARTITION_SPACE
                                            / 100) * total_space
                if avail_space > int(filesize):
                    return True
                else:
                    return False
            else:
                return False
    return False


def convert_2_bytes(s):
    symbols = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    letter = s[-1:].strip().upper()
    num = s[:-1]
    assert isFloat(num) and letter in symbols
    num = float(num)
    prefix = {symbols[0]: 1}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    return int(num * prefix[letter])


def is_remote_writable(dest):
    """ Does the normal (non-root) user have access.
    Used to test to see if we need to use sudo.
    """
    if _test('-e', dest):
        return _test('-w', dest)
    else:
        remotedir = os.path.dirname(dest)
        while remotedir != '/':
            if _test('-e', remotedir):
                return _test('-w', remotedir)
            remotedir = os.path.dirname(remotedir)
    return False


def _test(flags, path):
    """ Run arbitrary 'test' command on remote machine.
    """
    with quiet():
        result = run('test %s %s' % (flags, path))
        return result.return_code


def copy_bag(local, remote, remote_drive):
    if space_available(local, remote_drive):
        if is_remote_writable(remote):
            rsync(local, remote)
        else:
            rsync(local, remote, sudo=True)


def make_copies(mach_id, bag_id, remote_path, remote_drive):
    bag_path, bag_type, item_id, bag_name = get_bag_path(bag_id)
    if bag_type is None:
        bag_type = ''
    copy_bag(bag_path, remote_path, remote_drive)
    add_bag(bag_name, bag_type, bag_path, mach_id, item_id)
    validate_bag(remote_path)


def get_machine_url(mach_id):
    with cd(settings.CLINT_INSTALLATION_PATH):
        bag_cmd = [settings.CLINT_INSTALLATION_PATH + 'clint', 'show',
                   'machine', mach_id]
        run("source ENV/bin/activate")
        result = run(" ".join(bag_cmd))
        index = result.find('url:')
        index2 = result.find('\n', index)
        url = result[index+5:index2]
        return url


def get_bag_path(bag_id):
    with cd(settings.CLINT_INSTALLATION_PATH):
        bag_cmd = [settings.CLINT_INSTALLATION_PATH + 'clint -j', 'show',
                   'bag', bag_id]
        run("source ENV/bin/activate")
        result = run(" ".join(bag_cmd))
        result = json.loads(result)
        bag_path = result['absolute_filesystem_path']
        bag_type = BAG_TYPE[result['bag_type']]
        bag_name = result['bagname']
        item_id = result['item']
        ind1 = item_id.rfind('/', 0, len(item_id) - 1)
        ind2 = item_id.rfind('/', 0, ind1-1)
        item_id = item_id[ind2+1: len(item_id) - 1]
        return (bag_path, bag_type, item_id, bag_name)


def isFloat(num):
    """Function to check if the argument is a floating point number or not."""
    try:
        float(num)
        return True
    except:
        return False
