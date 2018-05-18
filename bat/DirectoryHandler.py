#!coding=utf8
import os
import dicom
import logging
import sys


class DirectoryHandler:
    """
    The class will iterate the input directory to find target database file.
    And store each found file full path in a list of string "Database_File_Path"
    """
    Dicom_File_Path = []
    Total_Dicom_Quantity = 0

    def __init__(self, input_directory):
        """
        :param input_directory:
        """
        if input_directory is not None:
            if os.path.isdir(input_directory):
                logging.info(r"Input is a folder.")
            else:
                logging.error(r"input is not a folder. Procedure quited.")
                return
        absolute_path = os.path.abspath(input_directory)
        self.list_files(absolute_path)

    def list_files(self, input_directory):
        """
        :param input_directory:
        :return: no return. Directly write all target files found in Database_File_Path
        """
        dir_list = os.listdir(input_directory)
        for dl in dir_list:
            full_dl = os.path.join(input_directory, dl)
            if os.path.isfile(full_dl):
                try:
                    # try to open the dicom file.
                    _ = dicom.read_file(full_dl)[0x0018, 0x1000].value
                    self.Dicom_File_Path.append(full_dl)
                    self.Total_Dicom_Quantity += 1
                    logging.info(str(full_dl))
                except Exception as e:
                    logging.info(str(full_dl))
                    logging.error(str(e))
            else:
                self.list_files(full_dl)


if __name__ == '__main__':
    print("please do not use it individually unless of debugging.")
