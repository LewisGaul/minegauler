#Create the required .ppm images for the minesweeper program.

import os.path
from glob import glob

from PIL import Image


directory = os.path.dirname(__file__)
faces = glob(os.path.join(directory, 'Images', 'Faces', '*.png'))
for path in faces:
    print path[:-4]
    im = Image.open(path)
    im = im.convert('RGB').resize(tuple([20]*2), Image.ANTIALIAS)
    im.save(path[:-4] + '.ppm')
    im.close()
