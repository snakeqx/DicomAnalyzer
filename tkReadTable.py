import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
import io
import os
import logging
import math
import numpy as np
from PIL import ImageTk, Image
from readtable.readtable import TableData
import matplotlib.pyplot as plt
import matplotlib.lines as lines

logging.basicConfig(level=logging.INFO,
                    format='''%(asctime)s %(filename)s[line:%(lineno)d]%(levelname)s %(message)s''',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=r'./GUI.log',
                    filemode='w')
# define a stream that will show log level > ERROR on screen also
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


class GUI:
    def __init__(self):
        self.CurrentFileName = None
        self.Table = None
        # Tk main loop
        self.Root = tk.Tk()
        self.__addwidget()
        self.Figure = plt.figure()
        self.Root.protocol("WM_DELETE_WINDOW", self.__ask_quit)

    def __ask_quit(self):
        if tkinter.messagebox.askokcancel("Quit", "You want to quit now?"):
            self.Root.quit()

    def __show_empty(self):
        fig = plt.figure(1, clear=True)
        l1 = lines.Line2D([0, 1], [0, 1], transform=fig.transFigure, figure=fig)
        l2 = lines.Line2D([0, 1], [1, 0], transform=fig.transFigure, figure=fig)
        fig.lines.extend([l1, l2])

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        im2 = Image.open(buf)
        photo = ImageTk.PhotoImage(im2)
        self.Plot.configure(image=photo)
        self.Plot.image = photo
        buf.close()

    def __clear_entry(self):
        self.FuseModuleEntry.delete(0.0, tk.END)
        self.FuseSliceEntry.delete(0.0, tk.END)
        return

    def __addwidget(self):
        # widgets
        self.Plot = tk.Label(self.Root)
        self.LoadButton = tk.Button(self.Root, text="Open Table", command=self.__load_table)
        self.RefreshButton = tk.Button(self.Root, text="Refresh", command=self.__show_plot)
        self.FuseSliceEntry = tk.Entry(self.Root, width=5)
        self.FuseSliceLabel = tk.Label(text="Fuse Slice:")
        self.FuseModuleEntry = tk.Entry(self.Root, width=5)
        self.FuseModuleLabel = tk.Label(text="Fuse Module:")
        self.AnalyzeButton = tk.Button(self.Root, text="Analyze", command=self.__analyze)
        # define layout
        current_row = 0
        self.Plot.grid(row=current_row, column=0, columnspan=4)
        current_row += 1
        self.LoadButton.grid(row=current_row, column=1)
        self.RefreshButton.grid(row=current_row, column=2)
        current_row += 1
        self.FuseModuleLabel.grid(row=current_row, column=1)
        self.FuseModuleEntry.grid(row=current_row, column=2)
        self.FuseModuleEntry.insert(0, "2")
        current_row += 1
        self.FuseSliceLabel.grid(row=current_row, column=1)
        self.FuseSliceEntry.grid(row=current_row, column=2)
        self.FuseSliceEntry.insert(0, "2")
        current_row += 1
        self.AnalyzeButton.grid(row=current_row, column=0, columnspan=4)
        self.__show_empty()

    def __load_table(self):
        self.CurrentFileName = tk.filedialog.askopenfilename()
        logging.info("Input file:" + self.CurrentFileName)
        self.Table = TableData(self.CurrentFileName)
        if self.Table.isFileAnalyzeComplete is False:
            logging.error("Input File is not correct!")
            return
        self.__show_plot()

    def __show_plot(self):
        try:
            module_sep = int(self.FuseModuleEntry.get().strip("\n"))
            slice_sep = int(self.FuseSliceEntry.get().strip("\n"))
        except Exception as e:
            logging.error(str(e))
            return
        data = self.Table.simplize_table(module_sep=module_sep, slice_sep=slice_sep)
        # plot the data
        plt.figure(1, clear=True)
        for i in range(0, data.shape[1]):
            plt.plot(data[:, i])
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        im2 = Image.open(buf)
        photo = ImageTk.PhotoImage(im2)
        self.Plot.configure(image=photo)
        # Known bug in tkinter, save the reference again!
        self.Plot.image = photo
        buf.close()

    def __analyze(self):
        if self.Table is None:
            logging.error("Table file is not initialized.")
            return
        if self.Table.isFileAnalyzeComplete is False:
            logging.error("Table file is not initialized.")
            return
        # calculate data
        try:
            slice_sep = int(self.FuseSliceEntry.get().strip("\n"))
            channel = self.Table.sort_channel(fus_slice=slice_sep)
            near = self.Table.sort_nearest_neighbor(fus_slice=slice_sep)
            center = self.Table.sort_center(fus_slice=slice_sep)
            mirror = self.Table.sort_mirror(fus_slice=slice_sep)
        except Exception as e:
            logging.error(str(e))
            return
        # plot data
        plt.figure(2, clear=True, figsize=(16, 9), dpi=300)
        plt.rcParams.update({'figure.autolayout': True})
        plt.subplot(221)
        for i in range(0, channel.shape[1]):
            plt.plot(channel[:, i])
        plt.title('Channel')

        plt.subplot(222)
        for i in range(0, near.shape[1]):
            plt.plot(near[:, i])
        plt.title('Nearest Neighbor')

        plt.subplot(223)
        for i in range(0, center.shape[1]):
            plt.plot(center[:, i])
        plt.title('Center')

        plt.subplot(224)
        for i in range(0, mirror.shape[1]):
            plt.plot(mirror[:, i])
        plt.title('Mirror')
        # convert to image to show
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        im = Image.open(buf)
        photo = ImageTk.PhotoImage(im)

        # create child window to show plot
        toplevel2 = tk.Toplevel(self.Root)
        toplevel2.wm_title("Sub Window")
        label2 = tk.Label(toplevel2, image=photo)
        # Known bug, save the reference again!
        label2.photo = photo
        label2.pack()
        return



if __name__ == '__main__':
    ui = GUI()
    ui.Root.mainloop()
    ui.Root.destroy()
