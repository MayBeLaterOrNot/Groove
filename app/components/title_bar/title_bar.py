# coding:utf-8
from win32.lib import win32con
from win32.win32api import SendMessage
from win32.win32gui import ReleaseCapture

from PyQt5.QtCore import QFile, Qt, QEvent
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QLabel, QWidget

from .title_bar_buttons import TitleBarButton, MaximizeButton


class TitleBar(QWidget):
    """ Title bar """

    def __init__(self, parent):
        super().__init__(parent)
        self.resize(600, 40)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.titleLabel = QLabel(self.tr("Groove Music"), self)
        self.minButton = TitleBarButton(parent=self)
        self.closeButton = TitleBarButton(parent=self)
        self.returnButton = TitleBarButton((60, 40), self)
        self.maxButton = MaximizeButton(self)
        self.__initWidget()

    def __initWidget(self):
        """ initialize widgets """
        self.setFixedHeight(40)
        self.__setQss()

        self.titleLabel.hide()
        self.returnButton.hide()

        # connect signal to slot
        self.minButton.clicked.connect(self.window().showMinimized)
        self.maxButton.clicked.connect(self.__showRestoreWindow)
        self.closeButton.clicked.connect(self.window().close)

        self.returnButton.installEventFilter(self)
        self.titleLabel.installEventFilter(self)

    def __setQss(self):
        """ set style sheet """
        self.titleLabel.setObjectName("titleLabel")
        self.minButton.setObjectName("minButton")
        self.maxButton.setObjectName("maxButton")
        self.closeButton.setObjectName("closeButton")
        self.returnButton.setObjectName("returnButton")

        f = QFile(":/qss/title_bar.qss")
        f.open(QFile.ReadOnly)
        self.setStyleSheet(str(f.readAll(), encoding='utf-8'))
        f.close()

    def resizeEvent(self, e: QResizeEvent):
        self.titleLabel.move(self.returnButton.isVisible() * 60, 0)
        self.closeButton.move(self.width() - 57, 0)
        self.maxButton.move(self.width() - 2 * 57, 0)
        self.minButton.move(self.width() - 3 * 57, 0)

    def mouseDoubleClickEvent(self, e):
        self.__showRestoreWindow()

    def mousePressEvent(self, e):
        if self.childAt(e.pos()):
            return

        ReleaseCapture()
        SendMessage(
            int(self.window().winId()),
            win32con.WM_SYSCOMMAND,
            win32con.SC_MOVE + win32con.HTCAPTION,
            0,
        )
        e.ignore()

    def __showRestoreWindow(self):
        """ show restored window """
        if self.window().isMaximized():
            self.window().showNormal()
            self.maxButton.setMaxState(False)
        else:
            self.window().showMaximized()
            self.maxButton.setMaxState(True)

    def setWhiteIcon(self, isWhiteIcon: bool):
        """ set icon color """
        for button in self.findChildren(TitleBarButton):
            button.setWhiteIcon(isWhiteIcon)

    def eventFilter(self, obj, e: QEvent):
        if obj == self.returnButton:
            if e.type() == QEvent.Hide:
                cond = self.titleLabel.parent() is not self
                self.titleLabel.move(15 * cond, 10 * cond)
            elif e.type() == QEvent.Show:
                self.titleLabel.move(
                    self.returnButton.width() + self.titleLabel.x(), self.titleLabel.y())
        elif obj == self.titleLabel:
            if e.type() == QEvent.Show and self.returnButton.isVisible():
                self.titleLabel.move(
                    self.returnButton.width() + self.titleLabel.y(), self.titleLabel.y())

        return super().eventFilter(obj, e)
