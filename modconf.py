# modconf.py
# Lillian Lemmer <lillian.lynn.lemmer@gmail.com>
#
# This module is part of modconf and is released under the
# MIT license: http://opensource.org/licenses/MIT

"""modconf.py: modem configuration

Usage:
  modconf.py <modem_type> <username> <password> <superadmin_password>
  modconf.py --supported
  modconf.py (-h | --help)
  modconf.py --version

Options:
  --supported   Show supported modems.
  -h --help     Show this screen.
  --version     Show version.

"""

import os
import sys
import string
import configparser
from random import randint

import crypt  # pure-python override (we generate on Windows, too!)
import docopt

__VERSION__ = "0.1"


SUPPORTED_MODEM_TYPES = (
                         'bullet',
                         'bullethp',
                         'loco',
                         'm',
                         'nano',
                         'pico',
                         'ps',
                         'all',
                        )


if __name__ == '__main__':
    arguments = docopt.docopt(__doc__, version='modconf ' + __VERSION__)
    modem_types_supported_readable = ', '.join(SUPPORTED_MODEM_TYPES)
    
    # are we simply displaying supported modems?
    if arguments['--supported']:
        print('Modem types supported: ' + modem_types_supported_readable)
        sys.exit()
    
    # check validity of declared modem type
    if arguments['<modem_type>'] not in SUPPORTED_MODEM_TYPES:
        message = ('Modem type not supported: ' + arguments['<modem_type>'] +
                   ' (must be one of: ' + modem_types_supported_readable + ')')
    
    # get modconf settings
    config = configparser.ConfigParser()
    config.read('settings.ini')
    
    # salt the user and superadmin passwords
    salt_chars = './' + string.ascii_letters + string.digits
    salt = salt_chars[randint(0, 63)] + salt_chars[randint(0, 63)]
    salted_password = crypt.crypt(arguments['<password>'], salt)
    superadmin_password = arguments['<superadmin_password>']
    salted_superadmin_password = crypt.crypt(superadmin_password, salt)
    
    # read corresponding config template for <modem_type> into string
    modem_config_template_dir = config['general']['modem_config_template_dir']
    modem_config_template_filename = arguments['<modem_type>'] + '.cfg'
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
                              arguments['<modem_type>'] + '.cfg')
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
