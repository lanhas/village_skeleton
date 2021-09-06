import cv2
import numpy as np
from enum import Enum
from PIL import Image

from PyQt5.QtWidgets import QFileDialog, QApplication, QMessageBox
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor


class EventType(Enum):
    """
    事件类型
    """
    noneType = 1        # 禁用鼠标事件
    drawOutline = 2     # 手动绘制边界线
    loadOutline = 3     # 加载边界线
    drawRoad = 4        # 道路绘制
    extractColor = 5    # 提取颜色

class OutlineColor(Enum):
    """
    边界线颜色，用于提取轮廓线
    """
    red = 1
    orange = 2
    yellow = 3
    green = 4
    cyan = 5
    blue = 6
    purple = 7
    black = 8
    gray = 9
    white = 10

# 颜色字典，用于确定取色结果属于哪种颜色((颜色下界), (颜色上界))、
colorDict = {'red_1': ((0, 43, 46), (10, 255, 255)), 
             'red_2': ((156, 43, 46), (180, 255, 255)),
             'orange': ((11, 43, 46), (25, 255, 255)),
             'yellow': ((26, 43, 46), (34, 255, 255)),
             'green': ((35, 43, 46), (77, 255, 255)),
             'cyan': ((78, 43, 46), (99, 255, 255)),
             'blue': ((100, 43, 46), (124, 255, 255)),
             'purple': ((125, 43, 46), (155, 255, 255)),
             'black': ((0, 0, 0), (180, 255, 46)),
             'gray': ((0, 0, 46), (180, 43, 220)),
             'white': ((0, 0, 221), (180, 30, 255)),
            }

class BaseMainWindow(QtWidgets.QMainWindow):
    """对QDialog类重写，实现一些功能"""

    def closeEvent(self, event):
        """
        重写closeEvent方法，实现dialog窗体关闭时执行一些代码
        :param event: close()触发的事件
        :return: None
        """
        reply = QMessageBox.question(self, '本程序',
                                        "是否要退出界面？",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

def getOutlineMask(image, outlineColor):
    """
    根据轮廓线的颜色，提取出轮廓

    Parameters
    ----------
    image: ndarray
        带有边界线的图像
    outlineColor: enum
        轮廓线线的颜色

    Return
    ------
    result: ndarray
        轮廓线掩膜，单通道图像，线条位置为1，背景为0
    """
    # 转为hsv图像
    im_hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    # 结果初始化
    result = np.zeros_like(image[:, :, 0], dtype=np.uint8)
    if outlineColor == OutlineColor.red:
        # cv2.inRange函数，根据颜色范围,得到该范围内颜色的位置
        red_location1 = cv2.inRange(im_hsv, colorDict['red_1'][0], colorDict['red_1'][1])==255
        red_location2 = cv2.inRange(im_hsv, colorDict['red_2'][0], colorDict['red_2'][1])==255
        result[np.logical_or(red_location1, red_location2)] = 1
    elif outlineColor == OutlineColor.orange:
        result[cv2.inRange(im_hsv, colorDict['orange'][0], colorDict['orange'][1])==255] = 1
    elif outlineColor == OutlineColor.yellow:
        result[cv2.inRange(im_hsv, colorDict['yellow'][0], colorDict['yellow'][1])==255] = 1
    elif outlineColor == OutlineColor.green:
        result[cv2.inRange(im_hsv, colorDict['green'][0], colorDict['green'][1])==255] = 1
    elif outlineColor == OutlineColor.cyan:
        result[cv2.inRange(im_hsv, colorDict['cyan'][0], colorDict['cyan'][1])==255] = 1
    elif outlineColor == OutlineColor.blue:
        result[cv2.inRange(im_hsv, colorDict['blue'][0], colorDict['blue'][1])==255] = 1
    elif outlineColor == OutlineColor.purple:
        result[cv2.inRange(im_hsv, colorDict['purple'][0], colorDict['purple'][1])==255] = 1
    elif outlineColor == OutlineColor.black:
        result[cv2.inRange(im_hsv, colorDict['black'][0], colorDict['black'][1])==255] = 1
    elif outlineColor == OutlineColor.gray:
        result[cv2.inRange(im_hsv, colorDict['gray'][0], colorDict['gray'][1])==255] = 1
    elif outlineColor == OutlineColor.white:
        result[cv2.inRange(im_hsv, colorDict['white'][0], colorDict['white'][1])==255] = 1
    return result

def image_blend(image, areaMask, alpha, beta, gamma) -> Image:
    """
    将图片内的前背景按一定比例区分

    Parameters
    ----------
    image: ndarray
    areaMask: ndarray
        区域掩膜
    alpha: float
        前景区的融合比例
    beta: float
        背景区的融合比例
    gamma: 透明度

    Return
    ------
    result: ndarray
        融合后的结果
    """
    foreground = image
    background = image.copy()
    # 如果掩膜是单通道图像，先将其转为三通道
    if len(areaMask.shape) == 2:
        for i in range(3):
            foreground[:, :, i][areaMask == 0] = 0
            background[:, :, i][areaMask > 0] = 0
    result = cv2.addWeighted(foreground, alpha, background, beta, gamma)
    return result

def img_addition(image, areaMask, axisColor):
    """
    为图片内掩膜区域上色

    Parameters
    ----------
    image: ndarray
    areaMask: ndarray
        区域掩膜
    axisColor: tuple
        颜色，(r, g, b)

    Return
    ------
    image: ndarray
    """
    image[:, :, 0][areaMask > 0] = axisColor[0]
    image[:, :, 1][areaMask > 0] = axisColor[1]
    image[:, :, 2][areaMask > 0] = axisColor[2]
    return image

def pil2pixmap(image):
    """
    将PIL Image类型转为Qt QPixmap类型
    """
    if image.mode == "RGB":
        r, g, b = image.split()
        image = Image.merge("RGB", (b, g, r))
    elif  image.mode == "RGBA":
        r, g, b, a = image.split()
        image = Image.merge("RGBA", (b, g, r, a))
    elif image.mode == "L":
        image = image.convert("RGBA")
    # Bild in RGBA konvertieren, falls nicht bereits passiert
    im2 = image.convert("RGBA")
    data = im2.tobytes("raw", "RGBA")
    qim = QtGui.QImage(data, image.size[0], image.size[1], QtGui.QImage.Format_ARGB32)
    pixmap = QtGui.QPixmap.fromImage(qim)
    return pixmap

def ndarray2pixmap(ndarray):
    """
    将ndarray类型转为QPixmap类型
    """
    if len(ndarray.shape) == 3:
        height, width, channels = ndarray.shape
        bytesPerLine = 3 * width
        qImg = QImage(ndarray.data, width, height, bytesPerLine, QImage.Format_RGB888)
        qpix = QPixmap(qImg)
    else:
        height, width = ndarray.shape
        bytesPerLine = 3 * width
        qImg = QImage(ndarray.data, width, height, bytesPerLine, QImage.Format_RGB32)
        qpix = QPixmap(qImg)
    return qpix

def dilate_iter(image,villageMask, iter_num: int, kernelSize):
    image = image.astype('uint8')
    img_scope = np.array(villageMask)
    temp_img = image
    kernel = np.ones((kernelSize, kernelSize), np.uint8)
    kernel2 = np.ones((3, 3), np.uint8)
    img = cv2.dilate(temp_img, kernel2, iterations=2)
    imgs = [img]
    for i in range(iter_num):
        img = cv2.dilate(temp_img, kernel, iterations=1)
        img[img_scope == 0] = 0
        imgs.append(img)
        temp_img = img
    imgs.append(img_scope)
    imgs.reverse()
    return imgs

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    dem_dbs = Image.open(r'utils\imgaug\data\shan.jpg')
    box = (0, 0, 400, dem_dbs.size[1])
    result = dem_dbs.crop(box)
    print(result.size)
    result.show()

