# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
Global command-line flags for configuration, plus a wrapper around gflags.
In the future, we may extend this to use either cement, or the nova
gflags extensions.
"""

# pylint: disable=W0622,W0611

from gflags import DEFINE_boolean
from gflags import DEFINE_enum
from gflags import DEFINE_integer
from gflags import DEFINE_string
from gflags import FLAGS


DEFINE_boolean('help', None, 'Show this help')
DEFINE_boolean('version', None, 'Show version information')

DEFINE_string('config_file', None, 'OpenQuake configuration file')
DEFINE_enum('output_type', 'db', ['db', 'xml'],
                  'Computation result output type')

DEFINE_boolean(
    'list_calculations', None,
    'Print a table of completed (successful and failed) calculations')

DEFINE_integer('list_outputs', None,
    'List computed outputs for the given calculation ID. '
    '\n\nExamples:'
    '\n\t--list_outputs 17'
    '\n\t--list_outputs=17')

DEFINE_integer('export', None,
    'Export the given output to the specified target dir. The `--target_dir`'
    ' parameter is required.'
    '\n\nExamples:'
    '\n\t--export 287 --target_dir /home/currentuser/calc_results/'
    '\n\t--export=287 --target_dir /home/currentuser/calc_results/'
    '\n\t--export=287 --target_dir=/home/currentuser/calc_results/')
DEFINE_string('target_dir', None,
    'Specify with the `--export` option to indicate export result location.')

DEFINE_string('debug', 'warn',
    'Turns on debug logging and verbose output.'
    ' One of debug, info, warn, error, critical.')

# These are added by default by gflags, but we don't need them
del FLAGS.helpshort
del FLAGS.helpxml


def get_flags_help():
    """Generates a help string for all known flags."""
    help_items = []

    # We don't use gflags own str(FLAGS) because we need some more control:
    #  - we don't want gflags own SPECIAL flags (e.g. --undefok)
    #  - we don't want a breakdown per module
    # pylint: disable=W0212
    FLAGS._FlagValues__RenderFlagList(FLAGS.FlagDict().values(), help_items)

    def cleanup(help):
        "Removes the confusing --no prefix from boolean flags"
        if help.startswith('  --[no]'):
            return '  --' + help[8:]
        else:
            return help

    return '\n'.join([cleanup(help) for help in help_items])
