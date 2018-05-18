from bat.DatabaseHandler import SQL3Handler
from bat.DirectoryHandler import DirectoryHandler
from bat.ImageHandler import ImageHandler
import logging
import sys

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=r'./BatPlus.log',
                    filemode='w')
# define a stream that will show log level > ERROR on screen also
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


def main():
    if len(sys.argv) == 1:
        files = DirectoryHandler(r'.\test')
    elif len(sys.argv) == 2:
        files = DirectoryHandler(sys.argv[1])
    else:
        print("programe paramters confused!")
        return 1
    print("Program is finding dicom files...")
    count = 1
    for _file in files.Dicom_File_Path:
        sys.stdout.write(f"\r{count:d}/{files.Total_Dicom_Quantity:d}: ")
        _image = ImageHandler(_file, window=(70, -5))
        count += 1
        if _image.isImageComplete:
            _image.save_image()
            if _image.Kernel == "Hr40f" and (_image.OriginalCollimation == 16 or 
                                             _image.OriginalCollimation == 1 or 
                                             _image.OriginalCollimation == 32 or 
                                             _image.OriginalCollimation == 64):
                _image.draw_sorted_iq_result(100, 2)
            if _image.Kernel == "Br40f" and ((_image.OriginalCollimation == 16 or 
                                              _image.OriginalCollimation == 32) and
                                             _image.KVP==130):
                _image.draw_sorted_iq_result(100, 2)
            SQL3Handler(_image).insert_data()
    print("Program exits sucesfully.")


if __name__ == '__main__':
    main()