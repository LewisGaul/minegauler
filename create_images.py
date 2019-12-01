#Create the required .ppm images for the minesweeper program.
from PIL import Image
from glob import glob

directory = r'C:\Users\User\Skydrive\Documents\Python\minesweeper'
faces = glob(directory + r'\Images\Faces\*.png')
for path in faces:
    print path[:-4]
    im = Image.open(path)
    im = im.convert('RGB').resize(tuple([20]*2), Image.ANTIALIAS)
    im.save(path[:-4] + '.ppm')
    im.close()
