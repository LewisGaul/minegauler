"""Used to update the highscores from direc."""

import time as tm

directory1 = r'C:\Users\User\Skydrive\Documents\Python\minesweeper'
directory2 = r'C:\Users\Guest\Saved Games\minesweeper'
def update_highscores():
    highscores1 = dict()
    highscores2 = dict()
    for d in ['Beginner', 'Intermediate', 'Expert']:
        with open(directory1 + '\\' + d + r'\highscores6.txt', 'r') as f:
            highscores1.update(eval(f.read()))
        with open(directory2 + '\\' + d + r'\highscores6.txt', 'r') as f:
            highscores2.update(eval(f.read()))
    for (settings, v) in highscores1.iteritems():
        try:
            v += [d for d in highscores2[settings] if d['Date'] not in map(lambda x: x['Date'], v)]
            v = sorted(v, key=lambda x: tm.strptime(x['Date'], '%d %b %Y %X'))
        except KeyError:
            pass
    for settings in set(highscores2.keys()) - set(highscores1.keys()):
        highscores1[settings] = highscores2[settings]
    return highscores1

trial = ('b', 1, 1, 'off', 1)
h = dict()
for d in ['Beginner', 'Intermediate', 'Expert']:
    with open(directory1 + '\\' + d + r'\highscores6.txt', 'r') as f:
        h.update(eval(f.read()))
