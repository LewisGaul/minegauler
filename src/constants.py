import sys

VERSION = '1.2.1'
PLATFORM = sys.platform
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
COLOURED = 'coloured' #necessary?

##Drag-select flagging type
UNFLAG = 'unflag'
FLAG = 'flag'

##Game states
READY = 'ready'
ACTIVE = 'active'
WON = 'won'
LOST = 'lost'
INACTIVE = 'inactive'
COLOURED = 'coloured'
CREATE = 'create'

##Minefield origins
OFFICIAL = 'official'
REGULAR = 'regular'
KNOWN = 'known'

NR_COLOURS = {
    1:  'blue',
    2:  '#%02x%02x%02x'%(  0,128,  0),
    3:  'red',
    4:  '#%02x%02x%02x'%(  0,  0,128),
    5:  '#%02x%02x%02x'%(128,  0,  0),
    6:  '#%02x%02x%02x'%(  0,128,128),
    7:  'black',
    8:  '#%02x%02x%02x'%(128,128,128),
    9:  '#%02x%02x%02x'%(192,192,  0),
    10: '#%02x%02x%02x'%(128,  0,128),
    11: '#%02x%02x%02x'%(192,128, 64),
    12: '#%02x%02x%02x'%( 64,192,192),
    13: '#%02x%02x%02x'%(192,128,192),
    14: '#%02x%02x%02x'%(128,192, 64),
    15: '#%02x%02x%02x'%(128, 64,192)
    }