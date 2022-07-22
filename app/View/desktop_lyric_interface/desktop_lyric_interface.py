# coding:utf-8
import bisect
import sys
from typing import List, Dict

from common.utils import startSystemMove
from common.database.entity import SongInfo
from common.signal_bus import signalBus
from common.style_sheet import setStyleSheet
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve
from components.frameless_window import FramelessWindow
from PyQt5.QtWidgets import QFrame, QLabel, QGraphicsOpacityEffect, QApplication

from .lyric_widget import LyricWidget
from .buttons import Button
from .buttons import ButtonFactory as BF


class DesktopLyricInterface(FramelessWindow):
    """ Desktop lyric interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.isPlay = False
        self.isLocked = False
        self.lyric = None
        self.times = []
        self.currentIndex = -1
        self.songInfo = SongInfo()

        self.container = QFrame(self)
        self.iconButton = BF.create(BF.ICON, self.container)
        self.songLabel = QLabel(self.container)
        self.lastButton = BF.create(BF.PREVIOUS, self.container)
        self.playButton = BF.create(BF.PLAY, self.container)
        self.nextButton = BF.create(BF.NEXT, self.container)
        self.lockButton = BF.create(BF.LOCK, self.container)
        self.settingButton = BF.create(BF.SETTING, self.container)
        self.closeButton = BF.create(BF.CLOSE, self.container)
        self.lyricWidget = LyricWidget(self)

        self.opacityEffect = QGraphicsOpacityEffect(self)
        self.opacityAni = QPropertyAnimation(
            self.opacityEffect, b'opacity', self)

        self.__initWidgets()

    def __initWidgets(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint |
                            Qt.SubWindow | Qt.WindowStaysOnTopHint)

        self.lyricWidget.move(12, 50)
        self.iconButton.move(12, 12)
        self.songLabel.move(48, 12)
        self.adjustHeight()
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.resize(int(w*5/6), self.height())
        # don't modify
        self.lyricWidget.resize(self.width(), self.height()-50)
        self.move(w//2 - self.width()//2, h-self.height()-100)

        self.opacityEffect.setOpacity(0.01)
        self.container.setGraphicsEffect(self.opacityEffect)

        self.container.setObjectName("container")
        setStyleSheet(self, "desktop_lyric_interface")
        self.__connectSignalToSlot()

    def enterEvent(self, e):
        if self.isLocked:
            return

        self.opacityAni.setEndValue(1)
        self.opacityAni.setDuration(150)
        self.opacityAni.setEasingCurve(QEasingCurve.OutQuad)
        self.opacityAni.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.opacityAni.setEndValue(0.01)
        self.opacityAni.setDuration(150)
        self.opacityAni.setEasingCurve(QEasingCurve.OutQuad)
        self.opacityAni.start()
        super().leaveEvent(e)

    def resizeEvent(self, e):
        self.container.resize(self.size())
        self.lyricWidget.resize(self.width()-24, self.height()-self.lyricWidget.y())
        self.playButton.move(self.width()//2-self.playButton.width()//2, 12)
        self.lastButton.move(self.playButton.x()-5-self.lastButton.width(), 12)
        self.nextButton.move(self.playButton.x()+5+self.playButton.width(), 12)
        self.lockButton.move(self.width()-112, 12)
        self.settingButton.move(self.width()-77, 12)
        self.closeButton.move(self.width()-42, 12)
        self.__adjustSongLabel()

    def adjustHeight(self):
        """ adjust the height """
        self.setFixedHeight(self.lyricWidget.y()+self.lyricWidget.minimumHeight())

    def __adjustSongLabel(self):
        """ adjust the text of song label """
        if not self.songInfo.singer or not self.songInfo.title:
            text = self.tr("No songs are playing")
        else:
            text = f"{self.songInfo.singer} - {self.songInfo.title}"

        fontMetrics = self.songLabel.fontMetrics()
        width = self.lastButton.x() - 10 - self.songLabel.x()
        text = fontMetrics.elidedText(text, Qt.ElideRight, width)
        self.songLabel.setText(text)
        self.songLabel.adjustSize()

    def updateWindow(self, songInfo: SongInfo):
        """ update window """
        self.lyric = []
        self.times = []
        self.currentIndex = -1
        self.songInfo = songInfo
        self.__adjustSongLabel()
        self.lyricWidget.setLyric([self.tr("Loading lyrics...")], 1)

    def setLyric(self, lyric: Dict[str, List[str]]):
        """ set lyric """
        self.lyric = lyric
        self.times = list(self.lyric.keys())
        self.currentIndex = -1

    def setCurrentTime(self, time: int, totalTime: int):
        """ set current time

        Parameters
        ----------
        time: int
            current time in milliseconds

        totalTime: int
            song duration in milliseconds
        """
        if not self.times:
            return

        # get index of time
        time = str(time/1000)
        times = [float(i) for i in self.times]
        i = bisect.bisect_left(times, float(time))
        i = min(len(self.times)-1, i)
        if float(time) < times[i]:
            i -= 1

        if i == self.currentIndex:
            return

        # update current lyric
        self.currentIndex = i
        if i < len(self.times)-1:
            duration = 1000*(float(self.times[i+1]) - float(self.times[i]))
        else:
            duration = 1000*(totalTime - float(self.times[i]))

        self.lyricWidget.setLyric(self.lyric[self.times[i]], duration)
        self.adjustHeight()
        if self.isPlay and self.isVisible():
            self.lyricWidget.setPlay(True)

    def setPlay(self, isPlay: bool):
        self.isPlay = isPlay
        self.playButton.setPlay(isPlay)
        self.lyricWidget.setPlay(isPlay)

    def mousePressEvent(self, e):
        if self.isLocked or sys.platform == "win32" or not self.__isDragRegion(e.pos()):
            return

        startSystemMove(self, e.globalPos())

    def mouseMoveEvent(self, e):
        if self.isLocked or sys.platform != "win32" or not self.__isDragRegion(e.pos()):
            return

        startSystemMove(self, e.globalPos())

    def __isDragRegion(self, pos: QPoint):
        return not isinstance(self.childAt(pos), Button)

    def setLocked(self, isLocked: bool):
        """ set the locked state of lyric """
        if self.isLocked == isLocked:
            return

        self.isLocked = isLocked
        self.setAttribute(Qt.WA_TransparentForMouseEvents, isLocked)
        if isLocked:
            self.container.hide()

    def __onSettingButtonClicked(self):
        """ setting button clicked slot """
        signalBus.showMainWindowSig.emit()
        signalBus.switchToSettingInterfaceSig.emit()

    def __connectSignalToSlot(self):
        self.lockButton.clicked.connect(lambda: self.setLocked(True))
        self.iconButton.clicked.connect(signalBus.showMainWindowSig)
        self.closeButton.clicked.connect(self.hide)
        self.lastButton.clicked.connect(signalBus.lastSongSig)
        self.nextButton.clicked.connect(signalBus.nextSongSig)
        self.playButton.clicked.connect(signalBus.togglePlayStateSig)
        self.settingButton.clicked.connect(self.__onSettingButtonClicked)
