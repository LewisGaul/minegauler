from os.path import join, isfile
import json
import time as tm
from shutil import copy2 as copy_file
from distutils.version import LooseVersion

from constants import *
from utils import direcs, enchs


def get_personal(names):
    names = map(lambda n: n.lower(), names)
    with open(join(direcs['data'], 'highscores.json'), 'r') as f:
        data = json.load(f)
    for k, hscores in data.items():
        data[k] = filter(lambda h: h['name'].lower() in names, hscores)
    return data

def update_format(path, version):
    """Returns data in the new format, ready to be added to current file."""
    version = LooseVersion(version)
    new_data = []
    if version < '1.0' and __name__ == '__main__': #dangerous with eval
        with open(path, 'r') as f:
            old_data = eval(f.read())
        stop = raw_input(
            'Old highscores have no encryption key, include anyway? ' +
            '(Hit Enter for yes, otherwise type something.) ')
        if stop:
            return []
        for settings, old_entry_list in old_data.items():
            for old_entry in old_entry_list:
                if not old_entry.has_key('Zoom'):
                    zoom = 16
                elif old_entry['Zoom'] == 'variable':
                    zoom = None
                else:
                    zoom = round(old_entry['Zoom']*16/100, 0)
                if settings[2] == 1.7:
                    detection = 1.8
                else:
                    detection = settings[2]
                new_entry = {
            'name':         old_entry['Name'],
            'level':        settings[0],
            'lives':        settings[4],
            'per cell':     settings[1],
            'detection':    detection,
            'drag':         True if settings[3] == 'single' else False,
            'distance to':  False,
            'time':         old_entry['Time'],
            '3bv':          old_entry['3bv'],
            '3bv/s':        old_entry['3bv/s'],
            'proportion':   1,
            'flagging':     1 if old_entry['Flagging'] == 'F' else 0,
            'date':         tm.mktime(tm.strptime(
                old_entry['Date'], '%d %b %Y %X')),
            'lives rem':    old_entry['Lives remaining'],
            'first success':old_entry['First success'],
            'zoom':         zoom, # See above
            'coords':       old_entry['Mine coords']}
                new_entry['key'] = encode_highscore(new_entry)
                new_data.append(new_entry)
    else:
        with open(path, 'r') as f:
            old_data = json.load(f)
    if version == '1.0':
        old_data = [h for h in old_data if h['proportion'] == 1 and
            h.has_key('key') and h['lives'] == 1]
        for d in old_data:
            for old, new in [('level', 'diff'), ('per cell', 'per_cell'),
                ('drag', 'drag_select'), ('zoom', 'button_size'),
                ('distance to', 'distance_to'),
                ('lives rem', 'lives_remaining'),
                ('first success', 'first_success')]:
                try:
                    # Replace with new keys.
                    d[new] = d.pop(old)
                except KeyError:
                    d[new] = None #no first success?
    elif version < '1.1.1':
        old_data = [h for h in old_data if h['proportion'] == 1 and
                h.has_key('key') and h['lives'] == 1]
    elif version < '1.1.2':
        old_enchs = lambda h: (
            (sum([c[0]*c[1] for c in h['coords']])
                if h.has_key('coords') else 0) +
            int(10*h['date']/float(h['time'])) +
            int(100*float(h['3bv/s'])) + h['3bv'] -
            reduce(lambda x, y: x + ord(y), h['name'], 0) + 3*h['lives'] +
            int(50*h['detection']) + 7*h['per_cell'] +
            19*int(h['drag_select']) +
            12*int(h['distance_to']) + int(11*(h['proportion'] - 1)))
        old_data = [h for h in old_data if h['key'] == old_enchs(h)]
    elif version < '1.2':
        old_enchs = lambda h: int(
            (sum([c[0]*c[1]**2 for c in h['coords']])
                if h.has_key('coords') else 0) +
            13*h['date']/float(h['time']) +
            100*float(h['3bv/s']) + 16*h['3bv'] -
            reduce(lambda x, y: 3*x + 7*ord(y), h['name'], 0) + 3*h['lives'] +
            50*h['detection'] + 7*h['per_cell'] + 19*int(h['drag_select']) +
            12*int(h['distance_to']))
        old_data = filter(lambda h: h['key'] == old_enchs(h), old_data)
    elif version == '1.2.1': #no highscores in early version 1.2
        new_data = dict()
        # Convert drag-select key from numeric to boolean.
        for k, v in old_data.items():
            settings = k.split(',')
            drag = settings[3]
            if drag in ['0', '1']:
                settings[3] = str(bool(int(drag)))
                k = ','.join(settings)
                for h in v:
                    h['key'] = enchs(h, k)
            new_data.setdefault(k, []).extend(v)
    elif version > '1.2.1':
        new_data = old_data
    if version < '1.2':
        new_data = dict()
        for h in old_data:
            if h['lives'] > 1 or h['per_cell'] > 3 or (
                h.has_key('proportion') and h['proportion'] < 1):
                continue
            # Remove deprecated information.
            for s in ['proportion', 'lives_remaining', 'coords']:
                if h.has_key(s):
                    h.pop(s)
            # Ensure these settings are in boolean format.
            for s in ['distance_to', 'drag_select']:
                h[s] = bool(h[s])
            # Settings - keys are alphabetical.
            settings = ['diff', 'drag_select', 'per_cell', 'lives', 'detection',
                'distance_to']
            key = ','.join(map(lambda s: str(h.pop(s)), sorted(settings)))
            new_data.setdefault(key, []).append(h)
            h['key'] = enchs(h, key)
    return new_data

def include_data(data, check=True, save=True):
    """Include the converted old data in the current data file, which is
    first backed up."""
    copy_file(join(direcs['data'], 'highscores.json'),
        join(direcs['data'], 'highscores_backup{}.json'.format(
            tm.asctime()).replace(':', '.')))
    with open(join(direcs['data'], 'highscores.json'), 'r') as f:
        all_data = json.load(f)
    added = 0
    for k, hscores in data.items():
        all_data.setdefault(k, [])
        cur_hscores = [(h['date'], h['key']) for h in all_data[k]]
        for h in hscores:
            if not check:
                h['key'] = enchs(h, k)
            if (h['date'], h['key']) not in cur_hscores:
                all_data[k].append(h)
                added += 1
        all_data[k].sort(key=lambda x: x['date'])
    print "Added {} data entries.".format(added)
    if save:
        with open(join(direcs['data'], 'highscores.json'), 'w') as f:
            json.dump(all_data, f)
    else:
        return all_data


if __name__ == '__main__':
    while True:
        path = raw_input("Input old data file path:\n")
        if not path:
            break
        elif not isfile(path):
            print "Invalid path."
            continue
        v = raw_input("Input the version number: ")
        if not v:
            v = VERSION
        check = raw_input("Bypass key checking? (Enter for yes) ")
        data = update_format(path, v)
        include_data(data, check)