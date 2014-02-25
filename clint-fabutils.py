import os

from fabric.operations import put
from fabric.api import run, quiet, env

import settings

env.always_use_pty = False


def create_bag(local, base_name, machine_id, item_id, access_path):
    if not os.path.exists(local):
        raise IOError("Invalid directory '%s'" % local)
    if not os.access(local, os.R_OK) and not not os.access(local, os.W_OK):
        raise IOError("Insufficient permissions '%s'" % local)
    bag_cmd = ['./clint', 'bag', local,
               '-n', base_name,
               '-t', 'preservation',
               '-m', str(machine_id),
               '-i', item_id,
               '-p', access_path]
    run("%s" % bag_cmd)


def register_item(title, base_name, collection_id, item_type):
    register_cmd = ['./clint', 'add', 'item',
                    '-t', title,
                    '-l', base_name,
                    '-c', collection_id,
                    '-o', item_type]
    run("%s" % register_cmd)


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
