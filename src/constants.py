import sys

VERSION = '1.2.1'
PLATFORM = sys.platform
# Use platform to determine which button is right-click.
RIGHT_BTN_NUM = 2 if PLATFORM == 'darwin' else 3
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
    'first_success': True,
    'per_cell': 1,
    'detection': 1,
    'drag_select': False,
    'btn_size': 16, #pixels
    'name': '',
    'styles': {
        'buttons': 'standard',
        'numbers': 'standard',
        'images': 'standard'
        }
    }

nr_mines = {
    'b':  10,
    'i':  40,
    'e':  99,
    'm': 200
    }