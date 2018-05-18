import sqlite3
import logging
import numpy as np
from bat.ImageHandler import ImageHandler


class SQL3Handler:
    """
    Create a Sqlite3 handler to store the data.
    for the integration result, it will be converted to string and then store into database.
    So when extracting data, the string should be converted back to list or numpy array before doing calculation
    """
    Integration_Split = ','
    Database_Name = "BandAssessment.sqlite3.db"

    def __init__(self, dicom_image: ImageHandler):
        self.DicomImage = dicom_image
        logging.debug(r"Run into SQL3Handler")
        try:
            con = sqlite3.connect(self.Database_Name)
        except sqlite3.Error as e:
            logging.debug(str(e))
            return
        logging.debug(r"Database connected")
        sql_cursor = con.cursor()
        sql_string = '''create table BandAssessments(
                           uid text primary key,
                           modality text,
                           serial_number integer,
                           kvp real,
                           current integer,
                           kernel text,
                           total_collimation real,
                           slice_thickness real,
                           slice_mode text,
                           instance integer,
                           integration_result text,
                           comment text);'''
        try:
            sql_cursor.execute(sql_string)
        except sqlite3.Error as e:
            logging.debug(str(e))
            return
        logging.debug(r"create table done.")
        con.close()

    def insert_data(self):
        try:
            con = sqlite3.connect(self.Database_Name)
        except sqlite3.Error as e:
            logging.debug(str(e))
            return
        # convert numpy into string to store in sqlite3
        integration_result = []
        for x in self.DicomImage.Image_Median_Filter_Result:
            integration_result.append(str(x))
        int_result_string = self.Integration_Split.join(integration_result)
        # set up for store in sql
        sql_cursor = con.cursor()
        sql_string = r"insert into BandAssessments values (?,?,?,?,?,?,?,?,?,?,?,?);"
        try:
            logging.debug(str(self.DicomImage.Uid))
            sql_cursor.execute(sql_string,
                               (self.DicomImage.Uid,
                                self.DicomImage.Modality,
                                self.DicomImage.SerialNumber,
                                self.DicomImage.KVP,
                                self.DicomImage.Current,
                                self.DicomImage.Kernel,
                                self.DicomImage.TotalCollimation,
                                self.DicomImage.SliceThickness,
                                str(self.DicomImage.TotalSlice) + "x" + str(self.DicomImage.SliceThickness),
                                self.DicomImage.Instance,
                                int_result_string,
                                "n.a."))
        except sqlite3.Error as e:
            logging.error(str(e))
            con.close()
            return
        con.commit()
        logging.info(r"Insert record done.")
        con.close()

    def read_data(self):
        try:
            con = sqlite3.connect(self.Database_Name)
        except sqlite3.Error as e:
            logging.debug(str(e))
            return
        sql_cursor = con.cursor()
        sql_string = r"select integration_result from BandAssessment"
        sql_cursor.execute(sql_string)
        data = sql_cursor.fetchone()[0]
        str_result = data.split(self.Integration_Split)
        float_result = []
        for x in str_result:
            float_result.append(float(x))
        np_result = np.array(float_result)
        print(type(np_result))
        print(np_result)
        con.close()
        # End of class SQL3Handler:
        ##############################################################
