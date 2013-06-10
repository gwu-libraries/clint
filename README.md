clint
=====

Command Line INventory Tool
---------------------------

This project is intended to work in concert with the inventory system, held at https://github.com/gwu-libraries/inventory

It is a command line tool for the management of inventory and storage systems.  It will offer commands to add and edit collections, projects, items, and bags in the inventory system.

Installation
------------

Part I - Initial dependencies

1. Install Git if not already installed

        $ sudo apt-get install git-core

2. Install virtualenv if not already installed

        $ sudo apt-get install python-setuptools
        $ sudo easy_install virtualenv

Part II - Download the project

3. Change to your designated directory

        $ cd /<projects dir>

4. Pull down the project from github

        (GW staff only)
        $ git clone git@github.com:gwu-libraries/inventory.git

        (everyone else)
        $ git clone https://github.com/gwu-libraries/inventory.git

5. Create virtual Python environment for the project

        $ cd clint
        $ virtualenv --no-site-packages ENV

6. Activate your virtual environment

        $ source ENV/bin/activate

7. install other python dependencies

        (ENV)$ pip install -r requirements.txt

Part III - Configure your instance

8. Copy the local settings template to an active file

        (ENV)$ cp local_settings.py.template local_settings.py

9. Update the values in the local_settings file to point to your production and sandbox instances of Inventory

        (ENV)$ vim local_settings.py

Your ready to use it


Usage
-----

For help with all commands and subcommands use the --help flag

        (ENV)$ ./clint --help
        (ENV)$ ./clint add --help
        (ENV)$ ./clint show --help
        (ENV)$ ./clint bag --help

To see an object from the inventory use the 'show' command

        (ENV)$ ./clint show item 12345/cwef6w7tfw7w


To create new objects in the inventory use the 'add' command.  It must be followed by the type of object you wish to add (collection, project, item, bag, machine). You will be prompted to enter the metadata values for it one at a time.

        (ENV)$ ./clint add collection

Or, you can pass the values inline using flags

        (ENV)$ ./clint add collection --name "Collection 1"

To see the fields that can be passed for a particular type of object use the 'help' flag

        (ENV)$ ./clint add item --help


To edit objects, use the edit command:

        (ENV)$ ./clint edit item 12345/cwef6w7tfw7w

You will be prompted to edit each metadat field one at a time. The current values will be displayed in the prompt, but can be erased.

As with the 'add' command, you can pass the values inline with flags

        (ENV)$ ./clint edit collection --manager "Josh"


To delete an object from inventory use the delete command.

        (ENV)$ ./clint delete item 12345/cwef6w7tfw7w

Note that for bags, this will not remove the bag from the server, just its metadata from the inventory system.

Bag Operations

To bag a set of files use the 'bag' command

        (ENV)$ ./clint bag dir/to/new/bag

Once the bag has been made you will be prompted to supply inventory with the proper metadata.  The metadata can be passed inline.  Use the --help flag to see the available fields.

If a bag has had new files added to it and you want to update the manifest use the 'rebag' command.

        (ENV)$ ./clint rebag dir/to/existing/bag

If you want to validate a bag use the validate command

        (ENV)$ ./clint validate dir/to/new/bag

The copy and move commands are not yet implemented