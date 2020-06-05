import sys

VERSION = '1.2.2'
if sys.platform == 'win32':
    PLATFORM = 'windows'
elif sys.platform.startswith('linux'):
    PLATFORM = 'linux'
elif sys.platform == 'darwin':
    PLATFORM = 'mac'
else:
    PLATFORM = sys.platform
# Use platform to determine which button is right-click.
RIGHT_BTN_NUM = 2 if PLATFORM == 'mac' else 3
BIG = 1000
# Boolean to check if app is running from exe package.
IN_EXE = hasattr(sys, 'frozen')

##Button states
# Must be a negative integer for use in integer numpy array representing the
# board.
UNCLICKED = -101
MINE = -100
FLAGGED = 'flagged'
CLICKED = 'clicked'

##Drag-select flagging type
UNFLAG = 'unflag'
FLAG = 'flag'
REFRESH = 'refresh'

##Game states
READY = 'ready'
ACTIVE = 'active'
WON = 'won'
LOST = 'lost'
INACTIVE = 'inactive'
CREATE = 'create'

##Minefield origins
OFFICIAL = 'official'
REGULAR = 'regular'
KNOWN = 'known'

nr_colours = {
    1:  'blue',
    2:  '#%02x%02x%02x'%(  0,128,  0),
    3:  'red',
    4:  '#%02x%02x%02x'%(  0,  0,128),
    5:  '#%02x%02x%02x'%(128,  0,  0),
    6:  '#%02x%02x%02x'%(  0,128,128),
    7:  'black',
    8:  '#%02x%02x%02x'%(128,128,128)
    }

default_settings = {
    'diff': 'b',
    'dims': (8, 8),
    'mines': 10,
    'first_success': 1,
    'lives': 1,
    'per_cell': 1,
    'detection': 1,
    'drag_select': False,
    'distance_to': False,
    'btn_size': 16, #pixels
    'name': '',
    'styles': {
        'buttons': 'standard',
        'numbers': 'standard',
        'images': 'standard',
        'frames': 'standard'
        },
    'is_resizable': False
    }

bg_colours = {
    '': (240, 240, 237), #button grey
   'red':  (255,   0,   0),
   'life': (196, 0, 255)
   }

nr_mines = {
    'b': {
        0.5: 10, 1: 10, 1.5: 8, 1.8: 7, 2: 6,
        2.2: 5, 2.5: 5, 2.8: 4, 3: 4
        },
    'i': {
        0.5: 40, 1: 40, 1.5: 30, 1.8: 25,
        2: 25, 2.2: 20, 2.5: 18, 2.8: 16, 3: 16
        },
    'e': {
        0.5: 99, 1: 99, 1.5: 80, 1.8: 65,
        2: 60, 2.2: 50, 2.5: 45, 2.8: 40, 3: 40
        },
    'm': {
        0.5: 200, 1: 200, 1.5: 170, 1.8: 160,
        2: 150, 2.2: 135, 2.5: 110, 2.8: 100, 3: 100
        }
    }