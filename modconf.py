# modconf.py
# Lillian Lemmer <lillian.lynn.lemmer@gmail.com>
#
# This module is part of modconf and is released under the
# MIT license: http://opensource.org/licenses/MIT

"""modconf.py: modem configuration

Usage:
  modconf.py <username> <password> <superadmin_password> [--mtype=MODEMTYPE]
  modconf.py --supported
  modconf.py --wizard
  modconf.py --clean
  modconf.py (-h | --help)
  modconf.py --version

Arguments:
  MODEMTYPE      See --supported.

Options:
  --wizard       Interactive mode, you will be prompted for args.
  --mtype=MTYPE  Modem type to generate config for. Default: ALL.
  --supported    Show supported modems.
  --clean        Remove all files in output directory.
  -h --help      Show this screen.
  --version      Show version.

"""

import os
import sys
import string
import shutil
import configparser
from random import randint

import docopt

import crypt  # local pure-python; generate passwords on Windows

__VERSION__ = "0.5"


# should actually be glob results of config template directory
# sans file extension
SUPPORTED_MODEM_TYPES = (
                         'ALL',  # MUST be first!
                         'bullet',
                         'bullethp',
                         'loco',
                         'm',
                         'nano',
                         'pico',
                         'ps',
                        )


if __name__ == '__main__':
    arguments = docopt.docopt(__doc__, version='modconf ' + __VERSION__)
    modem_types_supported_readable = ', '.join(SUPPORTED_MODEM_TYPES)

    # get modconf settings
    config = configparser.ConfigParser()
    config.read('settings.ini')

    # collect arguments interactively
    if arguments['--wizard']:
        # TODO: actual sanitization?
        modem_type = input('modem type (hit enter for default [ALL]):')
        modem_type = modem_type or 'ALL'

        username = None
        while not username: username = input('userame: ')

        password = None
        while not password: password = input('password: ')

        sapassword = None
        while not sapassword: sapassword = input('superadmin password: ')

        arguments['--mtype'] = modem_type
        arguments['<username>'] = username
        arguments['<password>'] = password
        arguments['<superadmin_password>'] = sapassword

    # are we simply displaying supported modems?
    if arguments['--supported']:
        print('Modem types supported: ' + modem_types_supported_readable)
        sys.exit()

    # are we cleaning the output_directory set in config?
    elif arguments['--clean']:
        output_dir = os.path.abspath(config['general']['output_dir'])

        try:
            shutil.rmtree(output_dir)
        except FileNotFoundError:
            sys.exit('Does not exist: ' + output_dir)

        sys.exit()

    # check validity of declared modem type
    if arguments['--mtype'] and arguments['--mtype'] not in SUPPORTED_MODEM_TYPES:
        message = ('Modem type not supported: ' + arguments['--mtype'] +
                   ' (must be one of: ' + modem_types_supported_readable + ')')
        sys.exit(message)

    # salt the user and superadmin passwords
    salt_chars = './' + string.ascii_letters + string.digits
    salt = salt_chars[randint(0, 63)] + salt_chars[randint(0, 63)]
    salted_password = crypt.crypt(arguments['<password>'], salt)
    superadmin_password = arguments['<superadmin_password>']
    salted_superadmin_password = crypt.crypt(superadmin_password, salt)

    if arguments['--mtype'] == 'ALL' or arguments['--mtype'] is None:
        configs_to_generate = SUPPORTED_MODEM_TYPES[1:]
    else:
        configs_to_generate = (arguments['--mtype'],)

    for modem_type in configs_to_generate:
        # read corresponding config template for <modem_type> into string
        modem_config_template_dir = config['general']['modem_config_template_dir']
        modem_config_template_filename = modem_type + '.cfg'
        modem_config_template_path = os.path.join(modem_config_template_dir,
                                                  modem_config_template_filename)

        try:

            with open(modem_config_template_path) as f:
                modem_config_template_contents = f.read()

        except IOError:
            sys.exit(modem_config_template_path + " doesn't exist!")

        # create a new configuration by interpolating dictionary of
        # substitutions with the config template.
        #
        # users.1.name={superadmin_username}
        # users.1.password={superadmin_password}
        # users.2.name={username}
        # users.2.password={password}
        # resolv.host.1.name={username}
        # wpasupplicant.profile.1.network.1.anonymous_identity={username}
        # wpasupplicant.profile.1.network.1.identity={username}
        # wpasupplicant.profile.1.network.1.password={unsalted_password}
        superadmin_username = config['general']['superadmin_username']
        substitutions = {
                         'username': arguments['<username>'],
                         'unsalted_password': arguments['<password>'],
                         'password': salted_password,
                         'superadmin_username': superadmin_username,
                         'superadmin_password': salted_superadmin_password,
                        }
        new_config_output = modem_config_template_contents.format(**substitutions)

        config_output_filename = (arguments['<username>'] + '_' +
                                  modem_type + '.cfg')
        config_output_path = os.path.join(config['general']['output_dir'],
                                          config_output_filename)

        # if the output directory doesn't exist, create it!
        if not os.path.exists(config['general']['output_dir']):
            os.makedirs(config['general']['output_dir'])

        # Done! Write new config to output path!
        try:

            with open(config_output_path, 'w') as f:
                f.write(new_config_output)

        except IOError:
            sys.exit('Cannot output to: ' + config_output_path)

