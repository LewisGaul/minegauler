import sys

VERSION = '1.2.0'
PLATFORM = sys.platform
BIG = 1000
# Boolean to check if app is running from exe package.
IN_EXE = hasattr(sys, 'frozen')