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
                    format='''%(asctime)s %(filename)s[line:%(lineno)d]
                              %(levelname)s %(message)s''',
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
        fig = plt.figure()
        l1 = lines.Line2D([0, 1], [0, 1],
                          transform=fig.transFigure, 
                          figure=fig)
        l2 = lines.Line2D([0, 1], [1, 0],
                          transform=fig.transFigure,
                          figure=fig)
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
        # canvas
        self.Plot = tk.Label(self.Root)
        self.LoadButton = tk.Button(self.Root, text="Open Table",
                                    command=self.__load_table)
        self.RefreshButton = tk.Button(self.Root, text="Refresh",
                                       command=self.__show_plot)
        self.FuseSliceEntry = tk.Entry(self.Root, width=5)
        self.FuseSliceLabel = tk.Label(text="Fuse Slice:")
        self.FuseModuleEntry = tk.Entry(self.Root, width=5)
        self.FuseModuleLabel = tk.Label(text="Fuse Module:")
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
        data = self.Table.SimplizeTable(module_sep=module_sep,
                                        slice_sep=slice_sep)      
        fig = plt.figure()
        for i in range(0, data.shape[1]):
            plt.plot(data[:, i])

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        im2 = Image.open(buf)
        photo = ImageTk.PhotoImage(im2)
        self.Plot.configure(image=photo)
        self.Plot.image = photo
        buf.close()


if __name__ == '__main__':
    ui = GUI()
    ui.Root.mainloop()
    ui.Root.destroy()
