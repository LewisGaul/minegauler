import os
import Tkinter as tk
from PIL import Image as PILImage, ImageTk
import pygame

from constants import *
from utils import direcs


class Gui(tk.Tk, object):
    def __init__(self):
        super(Gui, self).__init__()
        self.make_minefield()
        self.geometry("215x300")

    def make_minefield(self):
        def draw():
            pygame.draw.circle(screen, (0,0,0), (50,50), 20)
            pygame.display.update()
            # self.update()
        self.board = tk.Canvas(self, bg='blue', highlightthickness=0)
        self.board.grid()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        os.environ['SDL_WINDOWID'] = str(self.board.winfo_id())
        if PLATFORM == 'win32':
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        screen = pygame.display.set_mode((500, 500))
        screen.fill(pygame.Color(155,255,255))
        pygame.display.init()
        pygame.display.update()
        def update():
            pygame.display.update()
            self.after(0, update)
        # self.after(0, update)

        button = tk.Button(self, text='draw', command=draw)
        button.grid(column=3)
        # self.frame_imgs = dict()
        # self.frame_imgs['nw'] = ImageTk.PhotoImage(
        #     PILImage.open('../images/frame_topleft.png'))
        # self.frame_imgs['s'] = ImageTk.PhotoImage(
        #     PILImage.open('../images/frame_bottom.png'))
        # self.frame_imgs['e'] = ImageTk.PhotoImage(
        #     PILImage.open('../images/frame_right.png'))
        # self.frame_imgs['se'] = ImageTk.PhotoImage(
        #     PILImage.open('../images/frame_corner.png'))
        # self.board.create_image(0, 0, image=self.frame_imgs['nw'], anchor='nw')
        # self.board.create_image(0, 210, image=self.frame_imgs['s'],
        #     anchor='nw')
        # self.board.create_image(410, 0, image=self.frame_imgs['e'],
        #     anchor='nw')
        # self.board.create_image(410, 210, image=self.frame_imgs['se'],
        #     anchor='nw')
        # for i in range(20):
        #     for j in range(10):
        #         self.board.create_rectangle(10+20*i, 10+20*j, 10+20*(i+1),
        #             10+20*(j+1), fill='#00%02x%02x'%(10*i, 10*j), width=0)
        #     self.board.create_text(10+20*i+10, 10+50, text=i)

        sbx = tk.Scrollbar(self, command=self.board.xview, orient='horizontal')
        sbx.grid(row=1, column=0, sticky='ew')
        sby = tk.Scrollbar(self, command=self.board.yview)
        sby.grid(row=0, column=1, sticky='ns')
        self.board.config(xscrollcommand=sbx.set, yscrollcommand=sby.set,
            scrollregion=(0, 0, 420, 220))




if __name__ == '__main__':
    g = Gui()
    while True:
        g.mainloop()
        g.after(0, pygame.display.update)

    # root = tk.Tk()
    # f = tk.Frame(root, bd=10, relief='ridge', width=10, height=10)
    # f.pack()
    # tk.Label(f, text='hello', bg='red').pack()
    # root.mainloop()