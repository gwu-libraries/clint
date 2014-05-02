import os

from fabric.operations import put
from fabric.api import run, quiet, env, cd

import settings
import json
import csv

from xlrd import open_workbook

env.always_use_pty = False
item_id = ''

BAG_TYPE = {
    '1': 'Access',
    '2': 'Preservation',
    '3': 'Export'
    }


def create_bag(local, base_name, machine_id, item_id, access_path):
    if not os.path.exists(local):
        raise IOError("Invalid directory '%s'" % local)
    if not os.access(local, os.R_OK) and not not os.access(local, os.W_OK):
        raise IOError("Insufficient permissions '%s'" % local)
    with cd(settings.CLINT_INSTALLATION_PATH):
        bag_cmd = [settings.CLINT_INSTALLATION_PATH + 'clint', 'bag', local,
                   '-n', base_name,
                   '-t', 'preservation',
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


def import_collection(filename):
    try:
        file_extension = os.path.splitext(filename)[1]
        if file_extension == '.csv':
            reader = csv.DictReader(open(filename))
            for row in reader:
                process_bag(name=row['Item Name'], local_id=row['Local ID'],
                            col_id=row['Collection ID'],
                            item_type=row['Item Type'], b_type=row['Bag Type'],
                            b_path=row['Bag Path'], mach_id=row['Machine ID'],
                            b_name=row['Bag Name'], item_notes=row['Item Notes'],
                            item_access_loc=row['Item Access Location'])
                print 'Successfully added Bag: ' + row['Bag Name']

        elif file_extension in ['.xls', '.xlsx']:
            excel_file = open_workbook(filename)
            for sheet_name in excel_file.sheet_names():
                sheet = excel_file.sheet_by_name(sheet_name)
                for curr_row in range(1, sheet.nrows):
                    row_values = sheet.row_values(curr_row)
                    process_bag(col_id=row_values[0], name=row_values[1],
                                local_id=row_values[2], item_type=row_values[3],
                                item_notes=row_values[4],
                                item_access_loc=row_values[5],
                                b_name=row_values[6], b_path=row_values[7],
                                b_type=row_values[8],
                                mach_id=str(int(row_values[9])))
                    print 'Successfully added Bag: ' + row_values[6]

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
    assert num.isdigit() and letter in symbols
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
