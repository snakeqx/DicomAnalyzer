import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import io
import os
import logging
import math
from PIL import ImageTk, Image
from bat.ImageHandler import ImageHandler
from bat.RingConfig import SomatomGo
import matplotlib.pyplot as plt

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
        self.Center = 256
        self.IndicateCircle = None
        self.IsImageLoaded = False
        self.IsSystemLoaded = False
        self.Image = None
        self.ImageRaw = None
        self.System = None
        self.CurrentFile = None
        # Tk main loop
        self.Root = tk.Tk()
        self.__add_widget()
        self.Root.protocol("WM_DELETE_WINDOW", self.__ask_quit)

    def __ask_quit(self):
        if tkinter.messagebox.askokcancel("Quit", "You want to quit now?"):
            self.Root.quit()

    def __add_widget(self):
        # canvas
        self.Canvas = tk.Canvas(self.Root, height=512, width=512)
        self.Canvas.bind('<Button-1>', self.click_on_image)
        self.LoadButton = tk.Button(self.Root, text="Open Dicom",
                                    command=self.load_image)
        self.RefreshButton = tk.Button(self.Root, text="Refresh",
                                       command=self.show_image)
        self.AnalyzeButton = tk.Button(self.Root, text="Analyze",
                                       command=self.analyze_image)
        self.ResultText = tk.Text(self.Root, height=5)
        self.WindowWidthLabel = tk.Label(text="Window Width:")
        self.WindowWidthText = tk.Entry(self.Root, width=5)
        self.WindowCenterLabel = tk.Label(text="Window Center")
        self.WindowCenterText = tk.Entry(self.Root, width=5)
        # define layout
        current_row = 0
        self.Canvas.grid(row=current_row, column=0, columnspan=3)
        current_row += 1
        self.LoadButton.grid(row=current_row, column=0)
        self.RefreshButton.grid(row=current_row, column=1)
        current_row += 1
        self.AnalyzeButton.grid(row=current_row, column=0)
        current_row += 1
        self.WindowWidthLabel.grid(row=current_row, column=0)
        self.WindowWidthText.grid(row=current_row, column=1)
        current_row += 1
        self.WindowCenterLabel.grid(row=current_row, column=0)
        self.WindowCenterText.grid(row=current_row, column=1)
        current_row += 1
        self.ResultText.grid(row=current_row, column=0, columnspan=3)

    def analyze_image(self):
        if self.IsImageLoaded is False:
            logging.error("Cannot analyze. Image not initialized yet.")
            return
        im, fig = self.Image.draw_sorted_iq_result(100, 2)
        # Create window 1
        toplevel1 = tk.Toplevel(self.Root)
        toplevel1.wm_title("%s" % self.Image.ScanMode)      
        tkimage = ImageTk.PhotoImage(im)
        label = tk.Label(toplevel1, image=tkimage)
        # TK known bug, must save the canvas.image reference again manually.
        label.photo = tkimage
        label.pack()

        # Create Window 2
        limit_h = fig[0]
        limit_l = fig[1]
        limit_h1 = fig[2]
        limit_l1 = fig[3]
        result = fig[4]
        plt.figure()
        plt.plot(limit_h)
        plt.plot(limit_l)
        plt.plot(limit_h1)
        plt.plot(limit_l1)
        plt.plot(result)

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        im2 = Image.open(buf)
        photo = ImageTk.PhotoImage(im2)
        toplevel2 = tk.Toplevel(self.Root)
        toplevel2.wm_title("%s" % self.Image.ScanMode)
        label2 = tk.Label(toplevel2, image=photo)
        label2.photo = photo
        label2.pack()
        buf.close()
        # If close here, the program will quit
        # If not close, programe will not quit properly
        # TODO
        # plt.close()
        return

    def analyze_system_type(self):
        if self.IsImageLoaded is not True:
            logging.error("Image not initilized!")
            return
        system_string = self.Image.Modality
        if system_string == "SOMATOM go.Up":
            self.System = SomatomGo()  # default setting
        elif system_string == "SOMATOM go.Now":
            self.System = SomatomGo()  # default setting
        elif system_string == "SOMATOM go.All":
            self.System = SomatomGo()  # default setting
        elif system_string == "SOMATOM go.Top":
            self.System = SomatomGo(f=535, m=27.9, n=22.7,
                                    centralbeam=463.25,
                                    nmax=840, modchan=20,
                                    name="Top")
        else:
            self.IsSystemLoaded = False
        self.IsSystemLoaded = True

    def clear_text(self):
        self.ResultText.delete(0.0, tk.END)
        return

    def get_window(self):
        default_window = (70, -5)
        width_str = self.WindowWidthText.get().strip("\n")
        center_str = self.WindowCenterText.get().strip("\n")
        try:
            width_int = int(width_str)
            center_int = int(center_str)
        except Exception as e:
            logging.error(str(e))
            logging.warning("default windowing (WW, WC) is used:" +
                            str(default_window))
            self.WindowWidthText.insert(0, default_window[0])
            self.WindowCenterText.insert(0, default_window[1])
            return default_window
        return width_int, center_int

    def load_image(self):
        _filename = tk.filedialog.askopenfilename()
        logging.info("input filename="+_filename)
        self.clear_text()
        # judge if input file is correct
        if not os.path.isfile(_filename):
            self.ResultText.insert(tk.INSERT, _filename +
                                   " Input is not a file!!!")
            return
        logging.info("finally, filename="+_filename)
        self.CurrentFile = _filename
        self.show_image()

    def show_image(self):
        # Initial Dicom Image and show Image on canvas
        window = self.get_window()
        self.Image = ImageHandler(self.CurrentFile, window=window)
        if self.Image.isImageComplete is False:
            logging.error("Image Initialized failed.")
            return
        self.ImageRaw = self.Image.show_image()
        logging.info(str(self.ImageRaw))
        tkimage = ImageTk.PhotoImage(self.ImageRaw)
        tkimageid = self.Canvas.create_image(0, 0, anchor=tk.NW, image=tkimage)
        # TK known bug, must save the canvas.image reference again manually.
        self.Canvas.image = tkimage
        logging.info("TK Image ID =" + str(tkimageid))
        self.IsImageLoaded = True
        self.clear_text()
        dicom_info = str(self.Image.Modality) + ':' \
            + str(self.Image.SerialNumber) + '\t' \
            + str(self.Image.SoftwareVersion) + '\n' \
            + str(self.Image.ScanMode)
        self.ResultText.insert(tk.INSERT, dicom_info)
        return

    def click_on_image(self, event):
        self.clear_text()
        if self.IsImageLoaded is True:
            logging.info("Mouse position in image:(%s, %s)"
                         % (event.x, event.y))
        else:
            logging.info("Image not loaded!")
            return

        # calculate distance
        x = event.x
        y = event.y
        dist_pix = math.sqrt((x-self.Center)**2 + (y-self.Center)**2)
        distance = round(dist_pix * self.Image.PixSpace[0])
        # calculate channel
        self.analyze_system_type()
        if self.IsSystemLoaded is False:
            logging.info("Un-supported system type.")
            self.ResultText.insert(tk.INSERT, "Un-supported system type.")
            return
        channel = self.System.calculate_channel(distance)
        # convert channel to module
        if channel[0] is not None:
            module1 = math.ceil(channel[0] / self.System.ChannelPerModule)
        else:
            module1 = None
        if channel[1] is not None:
            module2 = math.ceil(channel[1] / self.System.ChannelPerModule)
        else:
            module2 = None
        # orgnizing string
        output_string = "Distance to Image center is:" + \
            str(distance) + "mm;\n" + \
            "Channel 1=" + str(channel[0]) + \
            " Module 1 = " + str(module1) + "\n" + \
            "Channel 2=" + str(channel[1]) + \
            " Module 2 = " + str(module2)
        self.ResultText.insert(tk.INSERT, output_string)
        self.draw_indication_circle(dist_pix)
        return

    def draw_indication_circle(self, radius):
        radius = round(radius)
        x1 = self.Center - radius
        y1 = self.Center - radius
        x2 = self.Center + radius
        y2 = self.Center + radius
        if self.IndicateCircle is not None:
            self.Canvas.delete(self.IndicateCircle)
            self.IndicateCircle = None
        self.IndicateCircle = self.Canvas.create_oval(x1, y1, x2, y2,
                                                      outline="red", width=1)
        logging.info(str(self.IndicateCircle))
        return


if __name__ == '__main__':
    ui = GUI()
    ui.Root.mainloop()
