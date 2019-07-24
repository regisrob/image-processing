from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


class ImageProcessingError(Exception):
    pass

class KakaduError(ImageProcessingError):
    pass

class OpenJpegError(ImageProcessingError):
    pass

class ValidationError(ImageProcessingError):
    pass
