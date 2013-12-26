import os

from fabric.operations import put
from fabric.api import run, quiet, env

env.always_use_pty = False


def rsync(local, remote, sudo=False):
    if not os.path.exists(local):
        raise IOError("Invalid directory '%s'" % local)
    if not os.access(local, os.R_OK):
        raise IOError("Cannot read directory '%s'" % local)
    put(local, remote, use_sudo=sudo)


def space_available(local, remote_drive):
    filesize = os.path.getsize(local)
    x = run("df -hP | awk 'NR>1{print $1,$4}' | sed -e's/%//g'")
    drives = dict([y.split() for y in x.split('\n')])
    for drive, space in drives.iteritems():
        if drive == remote_drive:
            free_space = convert_2_bytes(space)
            if free_space > int(filesize):
                return True
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
