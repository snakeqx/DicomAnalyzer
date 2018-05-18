import logging
import io
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from PIL import ImageFilter
from PIL import ImageDraw
import math
from bat.DicomHandler import DicomHandler


class ImageHandler(DicomHandler):
    """
    ImageHandler class is a heritage of DicomHandler class.
    The ImageHandler class can provide more functions
    based on the DicomHandler class
    to deal with image related calculation.
    """

    def __init__(self, filename, window=(50, 0)):
        """
        Initialization function
        :param filename: input dicom file name including path
        """
        self.isImageComplete = False
        try:
            # call super to init DicomHandler class first
            super(self.__class__, self).__init__(filename)
        except Exception as e:
            logging.error(str(e))
        if not self.isComplete:
            logging.warning(r"Dicom class initialed failed. Procedure quited.")
            return

        try:
            # Convert to HU unit
            self.ImageHU = self.RawData * self.Slop + self.Intercept
            self.ImageRaw = self.ImageHU.copy()
            self.rescale_image(window)
            # center is always in format (row, col)
            # Radius is always in format (radius in pixel, radius in cm)
            self.Center, self.Radius = self.calc_circle
            self.Center = (256, 256)
            # define circular integration result
            self.Image_Integration_Result = np.zeros(self.Radius[0])
            self.Image_Median_Filter_Result = np.zeros(self.Radius[0])
            # main calculation
            self.integration()
        except Exception as e:
            logging.error(str(e))
            return
        # set the flag to indicate initializing done
        self.isImageComplete = True
        logging.info(r"Image initialed OK.")

    def rescale_image(self, window: tuple):
        """
        rescale the image to set the data in range (0~255)
        :param window: a tuple pass in as (window width, window center)
        :return: return a np array as rescaled image
        """
        raw_data = self.ImageHU.copy()
        window_upper = window[1] + window[0] / 2
        window_lower = window[1] - window[0] / 2
        # make filter according to center and width
        upper_filter = raw_data > window_upper
        raw_data[upper_filter] = window_upper  # set upper value
        lower_filter = raw_data < window_lower
        raw_data[lower_filter] = window_lower  # set lower value
        # rescale the data to 0~255
        min_hu_image = raw_data.min()
        max_hu_image = raw_data.max()
        if min_hu_image == max_hu_image:
            self.ImageRaw = (raw_data - min_hu_image) * 255
        else:
            # rescale the image to fit 0~255
            self.ImageRaw = (raw_data - min_hu_image) * 255 \
                / (max_hu_image - min_hu_image)

    @property
    def calc_circle(self):
        """
        Calculate the image center and radius
        the method is simple
        from up/down/left/right side to go into center
        the 1st number is > mean value, it's the edge
        calculate the distance from th edge to center
        :return: return 2 tuples which are image center and radius
        (center row, center col),(radius in pixel, radius in cm)
        """
        # set up some local variables
        is_abnormal = False
        center_col = self.Size[1] // 2
        center_row = self.Size[0] // 2
        left_distance = 0
        right_distance = 0
        up_distance = 0
        low_distance = 0
        max_allowed_deviation = 20
        # Using PIL to find edge and convert back to np array
        # This will make calculation more accuracy
        filtered_image = np.array(
            Image.fromarray(self.ImageRaw)
                           .convert("L")
                           .filter(ImageFilter.FIND_EDGES)
        )

        # start to calculate center col
        for left_distance in range(1, self.Size[1]):
            if filtered_image[center_row, left_distance] != 0:
                break
        for right_distance in range(1, self.Size[1]):
            if filtered_image[center_row, self.Size[1] - right_distance] != 0:
                break
        center_col += (left_distance - right_distance) // 2
        logging.debug(r"Center Col calculated as: " + str(center_col))
        # if the calculated center col deviated too much
        if (self.Size[0] // 2 + max_allowed_deviation) \
           < center_col < \
           (self.Size[0] // 2 - max_allowed_deviation):
            logging.warning(r"It seems abnormal when calculate Center Col" +
                            r", use image center now!")
            center_col = self.Size[1] // 2
            is_abnormal = True

        # start to calculate center row
        for up_distance in range(1, self.Size[0]):
            if filtered_image[up_distance, center_col] != 0:
                break
        for low_distance in range(1, self.Size[0]):
            if filtered_image[self.Size[0] - low_distance, center_col] != 0:
                break
        center_row += (up_distance - low_distance) // 2
        logging.debug(r"Center Row calculated as: " + str(center_row))
        # if the calculated center row deviated too much
        if (self.Size[1] // 2 + max_allowed_deviation) < center_row < (self.Size[1] // 2 - max_allowed_deviation):
            logging.warning(r"It seems abnormal when calculate Center row, use image center now!")
            center_row = self.Size[0] // 2
            is_abnormal = True

        # set different radius according to normal/abnormal situation
        if is_abnormal is False:
            radius = (self.Size[0] - left_distance - right_distance) // 2
            diameter_in_cm = radius * self.PixSpace[0] * 2
            logging.debug(str(radius) + r"pix (radius), " + str(diameter_in_cm) +
                          r"cm(diameter)<==Calculated phantom diameter")
            # standardize the radius
            if diameter_in_cm < 250:
                radius = 233
                logging.debug(str(radius) + r"pix" + r", which is: " +
                              str(radius * self.PixSpace[0] * 2) + r"cm <==Radius Readjusted")
            else:
                radius = 220
                logging.debug(str(radius) + r"pix" + r", which is: " +
                              str(radius * self.PixSpace[0] * 2) + r"cm <==Radius Readjusted")
        else:
            logging.warning(r"Calculated center is abnormal, use 50 as radius!")
            radius = 50
            diameter_in_cm = radius * self.PixSpace[0]

        return (center_row, center_col), (radius, diameter_in_cm)

    def bresenham(self, center: tuple, radius: int):
        """
        Draw circle by bresenham method. And calculate the sum.
        :param center: a tuple to indecate center as (row, col)
        :param radius: set the radius of the calculated circle
        :return: return a tuple as (integration_result, count)
        """
        x = 0
        y = radius
        d = 3 - 2 * radius
        count = 0
        integration_result = 0.0
        while x < y:
            integration_result += self.ImageHU[center[0] - y, center[1] + x]
            integration_result += self.ImageHU[center[0] + y, center[1] + x]
            integration_result += self.ImageHU[center[0] - y, center[1] - x]
            integration_result += self.ImageHU[center[0] + y, center[1] - x]
            integration_result += self.ImageHU[center[0] - x, center[1] + y]
            integration_result += self.ImageHU[center[0] - x, center[1] - y]
            integration_result += self.ImageHU[center[0] + x, center[1] + y]
            integration_result += self.ImageHU[center[0] + x, center[1] - y]
            count += 8
            if d < 0:
                d = d + 4 * x + 6
            else:
                d = d + 4 * (x - y) + 10
                y -= 1
            x += 1
        return integration_result, count

    def roi_measure(self, center: tuple, radius):
        """
        Use self.bresenham multiple times to get sum of all pixel value and the total count.
        Then sum of pixcel value / total counts = mean hu value that is the mean HU in the circular ROI
        :param center: a tuple indicates where the circle center is as (row, col)
        :param radius: the radius in PIXEL
        :return: The mean HU value of the ROI
        """
        result_hu = 0
        result_count = 0
        for index in range(1, radius):
            _result = self.bresenham(center, index)
            result_hu += _result[0]
            result_count += _result[1]
        return result_hu / result_count

    def find_center_roi_min(self, radius, deviation):
        """
        Use a defined circle with radius to measure the HU value. And moving around the circle
        position in deviation range to find where the minum HU value is.
        :param radius: The radius of circular ROI in PIXEL
        :param deviation: The Square range to let the circle moving around.
        :return: return a tuple as (min result, min position) where a min position is a tuple as (row, col)
        """
        # initialize local variables
        result_min = self.roi_measure(self.Center, 10)
        min_row = self.Center[0]
        min_col = self.Center[1]
        result_temp = []
        # start to find the min HU value
        for index_row in range(self.Center[0] - deviation, self.Center[0] + deviation):
            for index_col in range(self.Center[1] - deviation, self.Center[1] + deviation):
                result = self.roi_measure((index_row, index_col), radius)
                result_temp.append(result)
                if result < result_min:
                    result_min = result       
                    min_row = index_row
                    min_col = index_col
        # pack the min value position in image
        min_position = (min_row, min_col)
        return result_min, min_position

    def circular_bresenham(self, center: tuple, radius: int, radius_inner: int):
        """
        1st define a circle with center (row, col) and a radius in PIXEL. Then on each point on the edge of the
        defined circle, a ROI with radius_inner in PIXEL will be measured.
        :param center: The defined circle center
        as a tuple (row, col)
        :param radius: The radius of the defined circle
        :param radius_inner: the radius of the
        ROI measurement on each point of the defined circle's edge.
        :return: return 2 values. 1) circular_result as a
        list of the HU value. 2) a list contains position as (row, col) of each point
        """
        x = 0
        y = radius
        d = 3 - 2 * radius
        circular_result = []
        circular_pos = []
        while x < y:
            circular_result.append(self.roi_measure((center[0] - y, center[1] + x), radius_inner))
            circular_result.append(self.roi_measure((center[0] + y, center[1] + x), radius_inner))
            circular_result.append(self.roi_measure((center[0] - y, center[1] - x), radius_inner))
            circular_result.append(self.roi_measure((center[0] + y, center[1] - x), radius_inner))
            circular_result.append(self.roi_measure((center[0] - x, center[1] + y), radius_inner))
            circular_result.append(self.roi_measure((center[0] - x, center[1] - y), radius_inner))
            circular_result.append(self.roi_measure((center[0] + x, center[1] + y), radius_inner))
            circular_result.append(self.roi_measure((center[0] + x, center[1] - y), radius_inner))
            # record the position to draw afterward
            circular_pos.append(([center[0] - y, center[1] + x]))
            circular_pos.append(([center[0] + y, center[1] + x]))
            circular_pos.append(([center[0] - y, center[1] - x]))
            circular_pos.append(([center[0] + y, center[1] - x]))
            circular_pos.append(([center[0] - x, center[1] + y]))
            circular_pos.append(([center[0] - x, center[1] - y]))
            circular_pos.append(([center[0] + x, center[1] + y]))
            circular_pos.append(([center[0] + x, center[1] - y]))
            if d < 0:
                d = d + 4 * x + 6
            else:
                d = d + 4 * (x - y) + 10
                y -= 1
            x += 1
        return circular_result, circular_pos

    def evaluate_iq(self, diameter_in_mm, deviation_in_mm):
        """
        To compare the center min HU and around max HU
        :param diameter_in_mm:
        :param deviation_in_mm:
        :return:
        """
        if not self.isImageComplete:
            logging.warning(r"Image initialed incomplete. Procedure quited.")
            return

        # convert diamter_in_mm into radius in pixel
        # radius = int((diameter_in_mm / self.PixSpace[0]) / 2)
        radius = int((diameter_in_mm/3.14159265)**0.5 / self.PixSpace[0])
        # convert deviation in mm into deviation in pixel
        deviation = int(deviation_in_mm / self.PixSpace[0])

        min_hu, min_pos = self.find_center_roi_min(radius, deviation)
        result, pos = self.circular_bresenham(min_pos, radius * 2, radius)
        max_hu = max(result)
        for i in range(0, len(result)):
            result[i] = result[i] - min_hu

        max_deviation = max(result)
        max_dev_position = pos[result.index(max_deviation)]
        
        # experiment of find theta
        theta = []
        for p in pos:
            y = min_pos[0]-p[0]
            x = p[1]-min_pos[1]
            if x == 0:
                if y > 0:
                    theta.append(90)
                else:
                    theta.append(270)
            elif y == 0:
                if x > 0:
                    theta.append(0)
                if x < 0:
                    theta.append(180)
            else:
                if x > 0 and y > 0:
                    theta.append(int(math.degrees(math.atan(y/x))))
                elif x < 0 < y:
                    theta.append(int((math.degrees(math.atan(y/x))*-1)+90))
                elif x < 0 and y < 0:
                    theta.append(int(math.degrees(math.atan(y/x))+180))
                else:
                    theta.append(int((math.degrees(math.atan(y/x))*-1)+270))
        union_result = []
        for i in range(0, len(result)):
            union_result.append((theta[i], result[i]))
        sorted_result_tuple = sorted(union_result, key=lambda t: t[0])
        sorted_result = []
        for r in sorted_result_tuple:
            sorted_result.append(r[1])
        return (sorted_result, min_hu, max_hu,
                min_pos, max_dev_position,
                deviation, max_deviation, radius)

    def draw_sorted_iq_result(self, diameter_in_mm, deviation_in_mm):
        # call evaluate_iq function to get result
        # a bunch of result must referenced before usage
        # TODO
        # How to simplize the code structure??
        eiq = self.evaluate_iq(diameter_in_mm, deviation_in_mm)
        result = eiq[0]
        min_hu = eiq[1]
        max_hu = eiq[2]
        min_pos = eiq[3]
        max_dev_position = eiq[4]
        deviation = eiq[5]
        max_deviation = eiq[6]
        radius = eiq[7]
        # Prepare to draw the image evaluation fig plot
        # image__filename__fig = "_IqEval_fig.jpeg"
        limit_h = []
        limit_l = []
        limit_h1 = []
        limit_l1 = []
        result_count = len(result)
        warning_thresh_hold = 2.5
        warning_count = 0
        error_thresh_hold = 3.5
        error_count = 0
        for r in result:
            if r >= warning_thresh_hold:
                warning_count += 1
            if r >= error_thresh_hold:
                error_count += 1
            limit_h.append(warning_thresh_hold)
            limit_h1.append(error_thresh_hold)
            limit_l.append(warning_thresh_hold*-1)
            limit_l1.append(error_thresh_hold*-1)
        fig = (limit_h, limit_l, limit_h1, limit_l1, result)
        # plt.figure()
        # plt.plot(limit_h)
        # plt.plot(limit_l)
        # plt.plot(limit_h1)
        # plt.plot(limit_l1)
        # plt.plot(result)

        # buf = io.BytesIO()
        # plt.savefig(buf, format='png')
        # buf.seek(0)
        # Cannot use plt.close()
        # TODO
        # WHY???
        # plt.close()
        
        # prepare to save the evaluation result
        image__filename = "_IqEval.jpeg"
        im = Image.fromarray(self.ImageRaw).convert("L")
        pixel_map = im.load()
        draw = ImageDraw.Draw(im)
        # draw the min center positoin
        pixel_map[min_pos[1], min_pos[0]] = 0
        pixel_map[min_pos[1] + 1, min_pos[0]] = 0
        pixel_map[min_pos[1] - 1, min_pos[0]] = 0
        pixel_map[min_pos[1], min_pos[0] + 1] = 0
        pixel_map[min_pos[1], min_pos[0] - 1] = 0
        # draw the max deviation center position
        pixel_map[max_dev_position[1], max_dev_position[0]] = 0
        pixel_map[max_dev_position[1] + 1, max_dev_position[0]] = 0
        pixel_map[max_dev_position[1] - 1, max_dev_position[0]] = 0
        pixel_map[max_dev_position[1], max_dev_position[0] + 1] = 0
        pixel_map[max_dev_position[1], max_dev_position[0] - 1] = 0
        # draw the Image Center Position
        pixel_map[self.Center[1], self.Center[0]] = 0
        pixel_map[self.Center[1] + 1, self.Center[0]] = 0
        pixel_map[self.Center[1] - 1, self.Center[0]] = 0
        pixel_map[self.Center[1], self.Center[0] + 1] = 0
        pixel_map[self.Center[1], self.Center[0] - 1] = 0
        # Draw circle
        text_pos = deviation
        draw.ellipse((min_pos[1] - radius,
                     min_pos[0] - radius,
                     min_pos[1] + radius,
                     min_pos[0] + radius))
        draw.text((min_pos[1], min_pos[0] + text_pos),
                  "Middle Min HU:" + str(min_hu))
        draw.ellipse((max_dev_position[1] - radius,
                      max_dev_position[0] - radius,
                      max_dev_position[1] + radius,
                      max_dev_position[0] + radius))
        draw.text((max_dev_position[1],
                   max_dev_position[0] + text_pos),
                  "Around Max HU:" + str(max_hu))
        draw.text((200, 100),
                  str("Max HU Deviation:" + str(max_deviation)))
        draw.text((200, 110),
                  str("error rate:" + str(error_count/result_count*100)+"%"))
        draw.text((200, 120),
                  str("warning rate:" + 
                      str(warning_count/result_count*100)+"%"))
        im.save(self.FileName + "_" + self.ScanMode + image__filename, "png")
        return im, fig

    def integration(self):
        """
        Circular integration by using bresenham
        :return: no return. Directly Write self.Image_Integration_Result and
        self.Image_Median_Filter_result
        """
        # calculate circular integration for each radius
        for index in range(1, len(self.Image_Integration_Result)):
            result = self.bresenham(self.Center, index)
            self.Image_Integration_Result[index] = result[0] / result[1]
        # calculate data by using Median
        # for the rest of the data, do the median filter with width
        _width = 8
        for index in range(len(self.Image_Integration_Result) - _width):
            self.Image_Median_Filter_Result[index] = np.median(
                self.Image_Integration_Result[index:index + _width])

    def save_image(self):
        """
        Save the plot for dicom path.
        :return: No return. Save the image at the dicom path
        """
        if not self.isImageComplete:
            logging.warning(r"Image initialed incomplete. Procedure quited.")
            return
        # set up the output file name
        image__filename = ".jpeg"
        image__filename__fig = "_fig.jpeg"
        im = Image.fromarray(self.ImageRaw).convert("L")
        # save image
        try:
            # save image
            im.save(self.FileName + "_" +
                    self.ScanMode +
                    image__filename, "png")
            # draw fig
            plt.plot(self.Image_Median_Filter_Result)
            plt.ylim((-5, 20))
            plt.xlim((0, 250))
            # draw fig image
            plt.savefig(self.FileName + "_" +
                        self.ScanMode +
                        image__filename__fig)
            plt.close()
        except Exception as e:
            logging.error(str(e))
            return
        finally:
            plt.close()

    def show_image(self):
        """
        Return return PIL image with 'L' mode
        :return: return PIL image with 'L' mode
        """
        if not self.isImageComplete:
            logging.warning(r"Image initialed incomplete. Procedure quited.")
            return
        return Image.fromarray(self.ImageRaw).convert("L")

    def show_integration_result(self):
        """
        Return the Integration result with a list
        :return: Return the Integration result with a list
        """
        if not self.isImageComplete:
            logging.warning(r"Image initialed incomplete. Procedure quited.")
            return
        return self.Image_Median_Filter_Result


if __name__ == '__main__':
    print("please do not use it individually unless of debugging.")

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d]' +
                        ' %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S')

    img = ImageHandler('a.dcm')
    img.rescale_image((2, 100))
    img.save_image()
