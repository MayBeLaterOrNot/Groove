import sys

import numpy as np
from PIL import Image
from PIL.ImageFilter import GaussianBlur
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QEnterEvent, QImage, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QToolButton, QWidget
from scipy.ndimage.filters import gaussian_filter


class BlurButton(QToolButton):
    """ 磨砂按钮 """

    def __init__(self, parent, buttonPos: tuple, iconPath, blurPicPath='', buttonSize: tuple = (70, 70), blurRadius=30):
        super().__init__(parent)
        # 保存属性
        self.blurPicPath = blurPicPath
        self.posX, self.posY = buttonPos    # 保存裁剪的图片区域左上角坐标
        self.buttonSize = buttonSize
        self.iconPath = iconPath
        self.blurRadius = blurRadius
        # 背景和磨砂特效
        self.blurPic = None
        # 设置鼠标进入标志位
        self.enter = False
        # 图标
        self.iconPic = QPixmap(self.iconPath).scaled(
            self.buttonSize[0], self.buttonSize[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # 初始化
        self.initWidget()

    def initWidget(self):
        """ 初始化小部件 """
        self.resize(self.buttonSize[0], self.buttonSize[1])
        self.move(self.posX, self.posY)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.__setBlurEffect()

    def __setBlurEffect(self):
        """ 设置磨砂效果 """
        if self.blurPicPath:
            # 裁剪下需要磨砂的部分
            img = Image.open(self.blurPicPath).resize(
                (200, 200))  # type:Image.Image
            img = img.crop((self.posX, self.posY,
                            self.width() + self.posX, self.height() + self.posY))
            img = img.filter(GaussianBlur(self.blurRadius)
                             ).point(lambda x: int(x*0.7))
            self.blurPic = img.toqpixmap()
            self.update()

    def setBlurPic(self, blurPicPath, blurRadius=35):
        """ 设置磨砂图片 """
        self.blurPicPath = blurPicPath
        self.blurRadius = blurRadius
        self.__setBlurEffect()

    def paintEvent(self, e):
        """ 绘制背景 """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)
        # 设置画笔
        painter.setPen(Qt.NoPen)
        # 绘制磨砂背景和图标
        if not self.enter:
            if self.blurPic:
                self.__drawCirclePic(painter, 5, 5, self.width()-10,
                                     self.height() - 10, self.blurPic)
            self.__drawCirclePic(painter, 5, 5, self.width()-10,
                                 self.height() - 10, self.iconPic)
        else:
            if self.blurPic:
                self.__drawCirclePic(painter, 0, 0, self.width(
                ), self.height(), self.blurPic)
            self.__drawCirclePic(painter, 5, 5, self.width()-10,
                                 self.height() - 10, self.iconPic)

    def __drawCirclePic(self, painter, x, y, width, height, pixmap):
        """ 在指定区域画圆 """
        brush = QBrush(pixmap)
        painter.setBrush(brush)
        painter.drawEllipse(x, y, width, height)

    def enterEvent(self, e: QEnterEvent):
        """ 鼠标进入按钮时增大按钮并显示提示条 """
        self.enter = True
        self.update()

    def leaveEvent(self, e):
        """ 鼠标离开按钮时减小按钮并隐藏提示条 """
        self.enter = False
        self.update()
