# coding:utf-8
import sys
import os
from math import sqrt, floor

from colorthief import ColorThief

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QPixmap, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QApplication


class DominantColor:
    """ 获取图像的主色调 """

    def __init__(self, imagePath=''):
        self.imagePath = imagePath
        self.rgb = tuple()

    def getDominantColor(self, imagePath, resType=str):
        """ 获取指定图片的主色调
        Parameters
        ----------
        imagePath : 图片路径\n
        reType : 返回类型，str返回十六进制字符串，否则为rgb元组
        """
        self.imagePath = imagePath
        colorThief = ColorThief(imagePath)
        self.rgb = colorThief.get_color()
        # 对饱和度进行调整
        self.__adjustSaturation()
        # 如果颜色还是太浅就使用默认主题色
        luminance = self.__getLuminance()
        if luminance > 200:
            self.rgb = (53, 108, 138)
        # 根据指定的返回类型决定返回十六进制颜色代码还是元组
        if resType is str:
            rgb = ''.join([hex(i)[2:].rjust(2, '0') for i in self.rgb])
            return rgb
        return self.rgb

    def __getLuminance(self):
        """ 根据rgb获取颜色亮度 """
        r, g, b = self.rgb
        luminance = sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
        return luminance

    def hsv2rgb(self, h, s, v) -> tuple:
        """ hsv空间变换到rgb空间 """
        h60 = h / 60.0
        h60f = floor(h60)
        hi = int(h60f) % 6
        f = h60 - h60f
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        r, g, b = 0, 0, 0
        if hi == 0:
            r, g, b = v, t, p
        elif hi == 1:
            r, g, b = q, v, p
        elif hi == 2:
            r, g, b = p, v, t
        elif hi == 3:
            r, g, b = p, q, v
        elif hi == 4:
            r, g, b = t, p, v
        elif hi == 5:
            r, g, b = v, p, q
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        return (r, g, b)

    def rgb2hsv(self, r, g, b) -> tuple:
        """ rgb空间变换到hsv空间 """
        r, g, b = r/255.0, g/255.0, b/255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx-mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g-b)/df) + 360) % 360
        elif mx == g:
            h = (60 * ((b-r)/df) + 120) % 360
        elif mx == b:
            h = (60 * ((r - g) / df) + 240) % 360
        s = 0 if mx == 0 else df / mx
        v = mx
        return (h, s, v)

    def __adjustSaturation(self):
        """ 调整饱和度 """
        luminance = self.__getLuminance()
        h, s, v = self.rgb2hsv(*self.rgb)
        factor = 1
        # 根据亮度调整饱和度
        if luminance > 230:
            factor = 4.8
        elif 200 < luminance <= 230:
            factor = 3.3
        elif 180 < luminance <= 200:
            factor = 2.1
        elif 160 < luminance <= 180:
            factor = 1.3
        elif 140 < luminance <= 160:
            factor = 1.2
        elif 127.5 < luminance <= 140:
            factor = 1.1
        s = min(1, factor * s)
        self.rgb = self.hsv2rgb(h, s, v)


class Demo(QWidget):
    """ 测试用例 """

    def __init__(self):
        super().__init__()
        self.dominantColor = DominantColor()
        self.setFixedSize(400, 400)
        self.currentAlbumIndex = 0
        self.albumFolder = 'resource\\Album_Cover'
        self.getPicPaths()
        self.albumCoverLabel = QLabel(self)
        self.albumCoverLabel.setFixedSize(240, 240)
        self.nextPicBt = QPushButton('下一首', self)
        self.lastPicBt = QPushButton('上一首', self)
        # 初始化
        self.__initWidgets()

    def __initWidgets(self):
        """ 初始化小部件 """
        self.setStyleSheet('background:cyan')
        self.albumCoverLabel.move(80, 80)
        self.lastPicBt.move(100, 330)
        self.nextPicBt.move(self.width() - 100 - self.nextPicBt.width(), 330)
        # 信号连接到槽
        self.lastPicBt.clicked.connect(self.updateAlbumCover)
        self.nextPicBt.clicked.connect(self.updateAlbumCover)

    def getPicPaths(self):
        """ 扫描文件夹 """
        self.albumPath_list = []
        dirName_list = os.listdir(self.albumFolder)
        for folder in dirName_list:
            if os.path.isfile(folder):
                continue
            folder = os.path.join(self.albumFolder, folder)
            fileName_list = os.listdir(folder)
            for album in fileName_list:
                if (album.endswith('png') or album.endswith('jpg')):
                    self.albumPath_list.append(os.path.join(folder, album))

    def updateAlbumCover(self):
        """ 更新专辑封面 """
        if self.sender() == self.lastPicBt:
            if self.currentAlbumIndex == 0:
                return
            self.currentAlbumIndex -= 1
        elif self.sender() == self.nextPicBt:
            if self.currentAlbumIndex == len(self.albumPath_list) - 1:
                return
            self.currentAlbumIndex += 1
        albumPath = self.albumPath_list[self.currentAlbumIndex]
        self.albumCoverLabel.setPixmap(QPixmap(albumPath).scaled(
            240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        r, g, b = self.dominantColor.getDominantColor(albumPath, tuple)
        palette = QPalette()
        palette.setColor(self.backgroundRole(), QColor(r, g, b))
        self.setPalette(palette)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = Demo()
    demo.show()
    sys.exit(app.exec_())
