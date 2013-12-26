from fabric.api import task
from fabric.operations import local
from subprocess import call
import sys
import os
from StringIO import StringIO


@task
def register():
    capture = StringIO()
    local('./clint add collection -n "testing_fab1" > test.txt')
    with open('test.txt') as f:
        content = f.readlines()
    id = content[3].split()
    print id[1]


'''@task
def bagit():


@task
def copy_to_storage():


@task
def copy_to_dspace():


@task
def import_to_dspace():'''
