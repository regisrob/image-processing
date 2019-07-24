from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import subprocess
import logging
from image_processing.exceptions import OpenJpegError
from image_processing import utils

DEFAULT_COMPRESS_OPTIONS = [
    '-n', '6', # number of resolutions
    '-c', '[256,256],[256,256],[128,128]', # precinct sizes
    '-t', '512,512', # tile size
    '-p', 'RPCL', # progression order
    '-b', '64,64', # code-block size
    '-SOP', # include SOP marker for each packet
    '-EPH', # include EPH marker after each packet header
    '-TP', 'R' # include tile part markers
]

"""Some default command line options for :func:`~image_processing.openjpeg.OpenJPEG.opj_compress`, without lossy/lossless specified."""

LOSSLESS_OPTIONS = [
    "-r", "1,1,1,1,1,1" # compression ratio values. 1 = lossless (one value per layer)
    #"-r", "1"
]
""":func:`~image_processing.openjpeg.OpenJPEG.opj_compress` command line options which make the compression lossless"""

DEFAULT_LOSSLESS_COMPRESS_OPTIONS = DEFAULT_COMPRESS_OPTIONS + LOSSLESS_OPTIONS
"""Default lossless command line options for :func:`~image_processing.openjpeg.OpenJPEG.opj_compress`"""

LOSSY_OPTIONS = ["-r", '3']
""":func:`~image_processing.openjpeg.OpenJPEG.opj_compress` command line options which make the compression lossy"""


class OpenJpeg(object):
    """
    Python wrapper for jp2 compression and expansion functions in OpenJPEG (https://www.openjpeg.org/)
    """

    def __init__(self, openjpeg_base_path):
        """
        :param openjpeg_base_path: The location of the opj_compress and opj_decompress executables
        """
        self.openjpeg_base_path = openjpeg_base_path
        self.log = logging.getLogger(__name__)
        if not utils.cmd_is_executable(self._command_path('opj_compress')):
            raise OSError("Could not find executable {0}. Check openjpeg is installed and opj_compress exists at the configured path"
                          .format(self._command_path('opj_compress')))
        if not utils.cmd_is_executable(self._command_path('opj_decompress')):
            self.log.error("Could not find executable {0}. Lossless checks will not work. "
                           "Check openjpeg is installed and opj_decompress exists at the configured path"
                          .format(self._command_path('opj_decompress')))

    def _command_path(self, command):
        return os.path.join(self.openjpeg_base_path, command)

    def opj_compress(self, input_filepaths, output_filepath, openjpeg_options):
        """
        Converts an image file supported by openjpeg to jpeg2000
        Bitonal or greyscale image files are converted to a single channel jpeg2000 file

        :param input_filepaths: Either a single filepath or a list of filepaths.
            If given three single channel files, Openjpeg will combine them into a single 3 channel image
        :param output_filepath:
        :param openjpeg_options: command line arguments
        """
        self.run_command('opj_compress', input_filepaths, output_filepath, openjpeg_options)

    def opj_decompress(self, input_filepath, output_filepath, openjpeg_options):
        """
        Converts a jpeg2000 file to tif

        :param input_filepath:
        :param output_filepath:
        :param openjpeg_options: command line arguments
        """
        self.run_command('opj_decompress', input_filepath, output_filepath, openjpeg_options)

    def run_command(self, command, input_files, output_file, openjpeg_options):
        if not isinstance(input_files, list):
            input_files = [input_files]

        # the -i parameter can have multiple files listed
        for input_file in input_files:
            if not os.access(input_file, os.R_OK):
                raise IOError("Could not access image file {0} to convert".format(input_file))

        if not os.access(os.path.abspath(os.path.dirname(output_file)), os.W_OK):
            raise IOError("Could not write to output path {0}".format(output_file))

        input_option = ",".join(["{0}".format(item) for item in input_files])

        command_options = [self._command_path(command), '-i', input_option, '-o', output_file] + openjpeg_options

        print(command_options)

        self.log.debug(' '.join(['"{0}"'.format(c) if ('{' in c or ' ' in c) else c for c in command_options]))

        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise OpenJpegError('OpenJPEG {0} failed on {1}. Command: {2}, Error: {3}'.
                              format(command, input_option, ' '.join(command_options), e))
