# coding:utf-8

import json
import os
from copy import deepcopy
from ctypes import POINTER, cast
from ctypes.wintypes import MSG
from random import shuffle
from time import time

from app.common.window_effect import WindowEffect
from app.components.label_navigation_interface import LabelNavigationInterface
from app.components.media_player import MediaPlaylist, PlaylistType
from app.components.opacity_ani_stacked_widget import OpacityAniStackedWidget
from app.components.pop_up_ani_stacked_widget import PopUpAniStackedWidget
from app.components.state_tooltip import StateTooltip
from app.components.thumbnail_tool_bar import ThumbnailToolBar
from app.components.title_bar import TitleBar
from app.View.album_interface import AlbumInterface
from app.View.my_music_interface import MyMusicInterface
from app.View.navigation_interface import NavigationInterface
from app.View.play_bar import PlayBar
from app.View.playing_interface import PlayingInterface
from app.View.playlist_card_interface import PlaylistCardInterface
from app.View.playlist_panel_interface.create_playlist_panel import CreatePlaylistPanel
from app.View.setting_interface import SettingInterface
from app.View.sub_play_window import SubPlayWindow
from PyQt5.QtCore import QEasingCurve, QEvent, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist
from PyQt5.QtWidgets import QAction, QApplication, QWidget
from PyQt5.QtWinExtras import QtWin
from system_hotkey import SystemHotkey
from win32 import win32api, win32gui
from win32.lib import win32con

from .c_structures import *


class MainWindow(QWidget):
    """ 主窗口 """

    BORDER_WIDTH = 5
    showSubPlayWindowSig = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 实例化小部件
        self.createWidgets()
        # 初始化标志位
        self.isInSelectionMode = False
        # 初始化显示器信息
        self.monitor_info = None
        # 创建窗口特效
        self.windowEffect = WindowEffect()
        # 初始化界面
        self.__initWidget()

    def createWidgets(self):
        """ 创建小部件 """
        # 主界面放置totalStackWidget、playBar 和 titleBar
        # totalStackWidget用来放置subMainWindow和playingInterface
        self.totalStackWidget = OpacityAniStackedWidget(self)
        # subMainWindow用来放置堆叠窗口subStackWidget
        self.subMainWindow = QWidget(self)
        self.titleBar = TitleBar(self)
        # 实例化播放器和播放列表
        self.player = QMediaPlayer(self)
        self.mediaPlaylist = MediaPlaylist(self)
        # subStackWidget用来放置myMusicInterface、albumInterface、settingInterface、
        # playlistCardInterface等需要在导航栏右边显示的窗口
        self.subStackWidget = PopUpAniStackedWidget(self.subMainWindow)
        # 创建设置界面
        self.settingInterface = SettingInterface(self.subMainWindow)
        # 从配置文件中的选择文件夹读取音频文件
        t3 = time()
        self.myMusicInterface = MyMusicInterface(
            self.settingInterface.getConfig(
                "selected-folders", []), self.subMainWindow
        )
        t4 = time()
        print("创建整个我的音乐界面耗时：".ljust(15), t4 - t3)
        # 创建定时扫描歌曲信息的定时器
        self.rescanSongInfoTimer = QTimer(self)
        # 创建缩略图任务栏
        QtWin.enableBlurBehindWindow(self)
        self.thumbnailToolBar = ThumbnailToolBar(self)
        self.thumbnailToolBar.setWindow(self.windowHandle())
        # 创建左上角播放窗口
        self.subPlayWindow = SubPlayWindow(
            self, self.mediaPlaylist.lastSongInfo)
        # 创建正在播放界面
        self.playingInterface = PlayingInterface(
            self.mediaPlaylist.playlist, self)
        # 创建专辑界面
        self.albumInterface = AlbumInterface({}, self.subMainWindow)
        # 创建播放列表卡界面
        self.readCustomPlaylists()  # 读入所有播放列表
        self.playlistCardInterface = PlaylistCardInterface(
            self.customPlaylists, self)
        # 创建导航界面
        self.navigationInterface = NavigationInterface(self.subMainWindow)
        # 创建标签导航界面
        self.labelNavigationInterface = LabelNavigationInterface(
            self.subMainWindow)
        # 创建播放栏
        self.playBar = PlayBar(self.mediaPlaylist.lastSongInfo, self)
        # 创建快捷键
        self.togglePlayPauseAct_1 = QAction(
            parent=self, shortcut=Qt.Key_Space, triggered=self.switchPlayState
        )
        self.showNormalAct = QAction(
            parent=self, shortcut=Qt.Key_Escape, triggered=self.exitFullScreen
        )
        self.lastSongAct = QAction(
            parent=self,
            shortcut=Qt.Key_MediaPrevious,
            triggered=self.mediaPlaylist.previous,
        )
        self.nextSongAct = QAction(
            parent=self, shortcut=Qt.Key_MediaNext, triggered=self.mediaPlaylist.next
        )
        self.togglePlayPauseAct_2 = QAction(
            parent=self, shortcut=Qt.Key_MediaPlay, triggered=self.switchPlayState
        )
        self.addActions(
            [
                self.togglePlayPauseAct_1,
                self.showNormalAct,
                self.nextSongAct,
                self.lastSongAct,
                self.togglePlayPauseAct_2,
            ]
        )
        # 创建stackWidget字典
        self.stackWidget_dict = {
            "subStackWidget": self.subStackWidget,
            "myMusicInterfaceStackWidget": self.myMusicInterface.stackedWidget,
        }
        # 当前选中的专辑卡
        self.currentAlbumCard = None

    def __initWidget(self):
        """ 初始化小部件 """
        self.resize(1300, 1000)
        self.setMinimumSize(1030, 800)
        self.setWindowTitle("Groove音乐")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint |
                            Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setWindowIcon(QIcon("app\\resource\\images\\透明icon.png"))
        self.setAttribute(Qt.WA_TranslucentBackground | Qt.WA_StyledBackground)
        # 在去除任务栏的显示区域居中显示
        desktop = QApplication.desktop().availableGeometry()
        self.move(
            int(desktop.width() / 2 - self.width() / 2),
            int(desktop.height() / 2 - self.height() / 2),
        )
        # 标题栏置顶
        self.titleBar.raise_()
        # 设置窗口特效
        self.setWindowEffect()
        # todo:将窗口添加到StackWidget中
        self.subStackWidget.addWidget(self.myMusicInterface, 0, 70, False)
        self.subStackWidget.addWidget(
            self.playlistCardInterface, 0, 120, False)
        self.subStackWidget.addWidget(self.settingInterface, 0, 120, False)
        self.subStackWidget.addWidget(self.albumInterface, 0, 70)
        self.subStackWidget.addWidget(
            self.labelNavigationInterface, 0, 100, False)
        self.totalStackWidget.addWidget(self.subMainWindow)
        self.totalStackWidget.addWidget(self.playingInterface)
        # 初始化标题栏的下标列表
        self.titleBar.stackWidgetIndex_list.append(
            ("myMusicInterfaceStackWidget", 0))
        # 设置右边子窗口的位置
        self.adjustWidgetGeometry()
        # 引用小部件
        self.referenceWidgets()
        # 设置层叠样式
        self.setObjectName("mainWindow")
        self.subMainWindow.setObjectName("subMainWindow")
        self.subStackWidget.setObjectName("subStackWidget")
        self.playingInterface.setObjectName("playingInterface")
        self.setQss()
        # 设置定时器溢出时间
        self.rescanSongInfoTimer.setInterval(180000)
        # 初始化播放列表
        self.initPlaylist()
        # todo:设置全局热键
        self.setHotKey()
        # 将信号连接到槽函数
        self.connectSignalToSlot()
        # 初始化播放栏
        self.initPlayBar()
        # 安装事件过滤器
        self.navigationInterface.navigationMenu.installEventFilter(self)
        self.rescanSongInfoTimer.start()

    def setHotKey(self):
        """ 设置全局热键 """
        self.nextSongHotKey = SystemHotkey()
        self.lastSongHotKey = SystemHotkey()
        self.playHotKey = SystemHotkey()
        # callback会返回一个event参数，所以需要用lambda
        self.nextSongHotKey.register(
            ("f6",), callback=lambda x: self.hotKeySlot(self.mediaPlaylist.next)
        )
        self.lastSongHotKey.register(
            ("f4",), callback=lambda x: self.hotKeySlot(self.mediaPlaylist.previous)
        )
        self.playHotKey.register(
            ("f5",), callback=lambda x: self.hotKeySlot(self.switchPlayState)
        )

    def setWindowEffect(self):
        """ 设置窗口特效 """
        # 开启窗口动画
        self.windowEffect.addWindowAnimation(self.winId())
        # 开启亚克力效果和阴影效果
        self.windowEffect.setAcrylicEffect(self.winId(), "F2F2F299", True)

    def adjustWidgetGeometry(self):
        """ 调整小部件的geometry """
        self.subMainWindow.resize(self.size())
        self.totalStackWidget.resize(self.size())
        self.titleBar.resize(self.width(), 40)
        if hasattr(self, "navigationInterface"):
            self.navigationInterface.setOverlay(self.width() < 1280)
            self.subStackWidget.move(self.navigationInterface.width(), 0)
            self.subStackWidget.resize(
                self.width() - self.navigationInterface.width(), self.height()
            )
            self.navigationInterface.resize(
                self.navigationInterface.width(), self.height()
            )
            self.labelNavigationInterface.resize(
                self.subMainWindow.width(), self.height()
            )
        if hasattr(self, "playBar"):
            if not self.playingInterface.smallestModeInterface.isVisible():
                self.playBar.resize(self.width(), self.playBar.height())

    def eventFilter(self, obj, e: QEvent):
        """ 过滤事件 """
        if obj == self.navigationInterface.navigationMenu:
            # 显示导航菜单是更改标题栏返回按钮和标题的父级为导航菜单
            isVisible = self.titleBar.returnBt.isVisible()
            if e.type() == QEvent.Show:
                self.titleBar.returnBt.setParent(obj)
                # 显示标题
                self.titleBar.title.setParent(obj)
                self.titleBar.title.move(15, 10)
                self.titleBar.title.show()
                # 如果播放栏课件就缩短导航菜单
                isScaled = self.playBar.isVisible()
                height = self.height() - isScaled * self.playBar.height()
                self.navigationInterface.navigationMenu.setBottomSpacingVisible(
                    not isScaled
                )
                self.navigationInterface.navigationMenu.resize(
                    self.navigationInterface.navigationMenu.width(), height
                )
            elif e.type() == QEvent.Hide:
                # 隐藏标题
                self.titleBar.title.hide()
                self.titleBar.title.setParent(self.titleBar)
                self.titleBar.returnBt.setParent(self.titleBar)
            # 根据情况显示/隐藏返回按钮和标题
            self.titleBar.returnBt.setVisible(isVisible)
        return super().eventFilter(obj, e)

    def resizeEvent(self, e):
        """ 调整尺寸时同时调整子窗口的尺寸 """
        super().resizeEvent(e)
        self.adjustWidgetGeometry()
        # 更新标题栏图标
        if self.isWindowMaximized(int(self.winId())):
            self.titleBar.maxBt.setMaxState(True)

    def moveEvent(self, e):
        if hasattr(self, "playBar"):
            if not self.isMaximized():
                self.playBar.move(
                    self.x() - 8, self.y() + self.height() - self.playBar.height()
                )
            else:
                self.playBar.move(
                    self.x() + 1, self.y() + self.height() - self.playBar.height() + 9
                )

    def closeEvent(self, e: QCloseEvent):
        """ 关闭窗口前更新json文件 """
        config = {}
        config["volume"] = self.playBar.volumeSlider.value()
        config["playBar.acrylicColor"] = self.playBar.acrylicColor
        self.settingInterface.updateConfig(config)
        self.playBar.close()
        self.subPlayWindow.close()
        self.mediaPlaylist.save()
        e.accept()

    def nativeEvent(self, eventType, message):
        """ 处理windows消息 """
        msg = MSG.from_address(message.__int__())
        if msg.message == win32con.WM_NCHITTEST:
            xPos = win32api.LOWORD(msg.lParam) - self.frameGeometry().x()
            yPos = win32api.HIWORD(msg.lParam) - self.frameGeometry().y()
            w, h = self.width(), self.height()
            lx = xPos < self.BORDER_WIDTH
            rx = xPos + 9 > w - self.BORDER_WIDTH
            ty = yPos < self.BORDER_WIDTH
            by = yPos > h - self.BORDER_WIDTH
            if lx and ty:
                return True, win32con.HTTOPLEFT
            elif rx and by:
                return True, win32con.HTBOTTOMRIGHT
            elif rx and ty:
                return True, win32con.HTTOPRIGHT
            elif lx and by:
                return True, win32con.HTBOTTOMLEFT
            elif ty:
                return True, win32con.HTTOP
            elif by:
                return True, win32con.HTBOTTOM
            elif lx:
                return True, win32con.HTLEFT
            elif rx:
                return True, win32con.HTRIGHT
        elif msg.message == win32con.WM_NCCALCSIZE:
            if self.isWindowMaximized(msg.hWnd):
                self.monitorNCCALCSIZE(msg)
            return True, 0
        if msg.message == win32con.WM_GETMINMAXINFO:
            if self.isWindowMaximized(msg.hWnd):
                window_rect = win32gui.GetWindowRect(msg.hWnd)
                if not window_rect:
                    return False, 0
                # 获取显示器句柄
                monitor = win32api.MonitorFromRect(window_rect)
                if not monitor:
                    return False, 0
                # 获取显示器信息
                monitor_info = win32api.GetMonitorInfo(monitor)
                monitor_rect = monitor_info["Monitor"]
                work_area = monitor_info["Work"]
                # 将lParam转换为MINMAXINFO指针
                info = cast(msg.lParam, POINTER(MINMAXINFO)).contents
                # 调整位置
                info.ptMaxSize.x = work_area[2] - work_area[0]
                info.ptMaxSize.y = work_area[3] - work_area[1]
                info.ptMaxTrackSize.x = info.ptMaxSize.x
                info.ptMaxTrackSize.y = info.ptMaxSize.y
                # 修改放置点的x,y坐标
                info.ptMaxPosition.x = abs(window_rect[0] - monitor_rect[0])
                info.ptMaxPosition.y = abs(window_rect[1] - monitor_rect[1])
                return True, 1
        return QWidget.nativeEvent(self, eventType, message)

    def isWindowMaximized(self, hWnd) -> bool:
        """ 判断窗口是否最大化 """
        # 返回指定窗口的显示状态以及被恢复的、最大化的和最小化的窗口位置，返回值为元组
        windowPlacement = win32gui.GetWindowPlacement(hWnd)
        if not windowPlacement:
            return False
        return windowPlacement[1] == win32con.SW_MAXIMIZE

    def monitorNCCALCSIZE(self, msg: MSG):
        """ 调整窗口大小 """
        monitor = win32api.MonitorFromWindow(msg.hWnd)
        # 如果没有保存显示器信息就直接返回，否则接着调整窗口大小
        if monitor is None and not self.monitor_info:
            return
        elif monitor is not None:
            self.monitor_info = win32api.GetMonitorInfo(monitor)
        # 调整窗口大小
        params = cast(msg.lParam, POINTER(NCCALCSIZE_PARAMS)).contents
        params.rgrc[0].left = self.monitor_info["Work"][0]
        params.rgrc[0].top = self.monitor_info["Work"][1]
        params.rgrc[0].right = self.monitor_info["Work"][2]
        params.rgrc[0].bottom = self.monitor_info["Work"][3]

    def connectSignalToSlot(self):
        """ 将信号连接到槽 """
        # todo:设置界面信号连接到槽函数
        self.settingInterface.crawlComplete.connect(
            self.myMusicInterface.rescanSongInfo
        )
        self.settingInterface.selectedFoldersChanged.connect(
            self.myMusicInterface.scanTargetPathSongInfo
        )
        # todo:标题栏返回按钮功能
        self.titleBar.returnBt.clicked.connect(self.returnButtonSlot)
        # todo:导航界面信号连接到槽函数
        self.navigationInterface.displayModeChanged.connect(
            self.navigationDisplayModeChangedSlot
        )
        self.navigationInterface.switchInterfaceSig.connect(
            self.stackWidgetIndexChangedSlot
        )
        self.navigationInterface.showPlayingInterfaceSig.connect(
            self.showPlayingInterface
        )
        self.navigationInterface.showCreatePlaylistPanelSig.connect(
            self.showCreatePlaylistPanel
        )
        self.navigationInterface.switchToSettingInterfaceSig.connect(
            self.switchToSettingInterface
        )
        self.navigationInterface.switchToMyMusicInterfaceSig.connect(
            self.switchToMyMusicInterface
        )
        self.navigationInterface.switchToPlaylistCardInterfaceSig.connect(
            self.switchToPlaylistCardInterface
        )
        # todo:缩略图任务栏各按钮的功能
        self.thumbnailToolBar.playButton.clicked.connect(self.switchPlayState)
        self.thumbnailToolBar.lastSongButton.clicked.connect(
            self.mediaPlaylist.previous
        )
        self.thumbnailToolBar.nextSongButton.clicked.connect(
            self.mediaPlaylist.next)
        # todo:播放栏各部件功能
        self.playBar.playButton.clicked.connect(self.switchPlayState)
        self.playBar.nextSongButton.clicked.connect(self.mediaPlaylist.next)
        self.playBar.volumeButton.muteStateChanged.connect(self.setMute)
        self.playBar.randomPlayButton.clicked.connect(self.setRandomPlay)
        self.playBar.lastSongButton.clicked.connect(
            self.mediaPlaylist.previous)
        self.playBar.songInfoCard.clicked.connect(self.showPlayingInterface)
        self.playBar.volumeSlider.valueChanged.connect(self.volumeChangedSlot)
        self.playBar.progressSlider.sliderMoved.connect(
            self.progressSliderMoveSlot)
        self.playBar.progressSlider.clicked.connect(
            self.progressSliderMoveSlot)
        self.playBar.loopModeButton.loopModeChanged.connect(
            self.switchLoopMode)
        self.playBar.moreActionsMenu.fillScreenAct.triggered.connect(
            self.setFullScreen)
        self.playBar.moreActionsMenu.showPlayListAct.triggered.connect(
            self.showPlaylist
        )
        self.playBar.moreActionsMenu.clearPlayListAct.triggered.connect(
            self.clearPlaylist
        )
        self.playBar.smallPlayModeButton.clicked.connect(
            self.showSmallestModeInterface)
        self.playBar.moreActionsMenu.savePlayListAct.triggered.connect(
            lambda: self.showCreatePlaylistPanel(self.mediaPlaylist.playlist)
        )
        # todo:将播放器的信号连接到槽函数
        self.player.positionChanged.connect(self.playerPositionChangeSlot)
        self.player.durationChanged.connect(self.playerDurationChangeSlot)
        # todo:将播放列表的信号连接到槽函数
        self.mediaPlaylist.switchSongSignal.connect(self.updateWindow)
        self.mediaPlaylist.currentIndexChanged.connect(
            self.playingInterface.setCurrentIndex
        )
        # todo:将正在播放界面信号连接到槽函数
        self.playingInterface.currentIndexChanged.connect(
            self.playingInterfaceCurrrentIndexChangedSlot
        )
        self.playingInterface.switchPlayStateSig.connect(self.switchPlayState)
        self.playingInterface.lastSongSig.connect(self.mediaPlaylist.previous)
        self.playingInterface.nextSongSig.connect(self.mediaPlaylist.next)
        self.playingInterface.playBar.randomPlayButton.clicked.connect(
            self.setRandomPlay
        )
        self.playingInterface.playBar.volumeSlider.muteStateChanged.connect(
            self.setMute
        )
        self.playingInterface.playBar.volumeSlider.volumeSlider.valueChanged.connect(
            self.volumeChangedSlot
        )
        self.playingInterface.playBar.progressSlider.sliderMoved.connect(
            self.progressSliderMoveSlot
        )
        self.playingInterface.playBar.progressSlider.clicked.connect(
            self.progressSliderMoveSlot
        )
        self.playingInterface.playBar.fillScreenButton.clicked.connect(
            self.setFullScreen
        )
        self.playingInterface.playBar.loopModeButton.loopModeChanged.connect(
            self.switchLoopMode
        )
        self.playingInterface.removeMediaSignal.connect(
            self.mediaPlaylist.removeMedia)
        self.playingInterface.randomPlayAllSignal.connect(self.disorderPlayAll)
        self.playingInterface.switchToAlbumInterfaceSig.connect(
            self.switchToAlbumInterfaceByName
        )
        self.playingInterface.playBar.moreActionsMenu.clearPlayListAct.triggered.connect(
            self.clearPlaylist
        )
        self.playingInterface.playBar.moreActionsMenu.savePlayListAct.triggered.connect(
            lambda: self.showCreatePlaylistPanel(self.mediaPlaylist.playlist)
        )
        self.playingInterface.smallestModeStateChanged.connect(
            self.smallestModeStateChanedSlot
        )
        self.playingInterface.exitFullScreenSig.connect(self.exitFullScreen)
        # todo:歌曲界面歌曲卡列表视图的信号连接到槽函数
        self.songTabSongListWidget.playSignal.connect(self.songCardPlaySlot)
        self.songTabSongListWidget.playOneSongSig.connect(self.playOneSongCard)
        self.songTabSongListWidget.nextToPlayOneSongSig.connect(
            self.songCardNextPlaySlot
        )
        self.songTabSongListWidget.addSongToPlayingSignal.connect(
            self.addOneSongToPlayingPlaylist
        )
        self.songTabSongListWidget.switchToAlbumInterfaceSig.connect(
            self.switchToAlbumInterfaceByName
        )
        self.songTabSongListWidget.editSongCardSignal.connect(
            self.editSongCardSlot)
        # todo:将专辑卡的信号连接到槽函数
        self.albumCardViewer.playSignal.connect(self.playAlbum)
        self.albumCardViewer.nextPlaySignal.connect(
            self.multiSongsNextPlaySlot)
        self.albumCardViewer.switchToAlbumInterfaceSig.connect(
            self.switchToAlbumInterfaceByAlbumInfo
        )
        self.albumCardViewer.saveAlbumInfoSig.connect(self.updateAlbumInfo)
        # todo:将子播放窗口的信号连接槽槽函数
        self.subPlayWindow.nextSongButton.clicked.connect(
            self.mediaPlaylist.next)
        self.subPlayWindow.lastSongButton.clicked.connect(
            self.mediaPlaylist.previous)
        self.subPlayWindow.playButton.clicked.connect(self.switchPlayState)
        # todo:将我的音乐界面连接到槽函数
        self.myMusicInterface.randomPlayAllSig.connect(self.disorderPlayAll)
        self.myMusicInterface.playCheckedCardsSig.connect(
            self.playCheckedCards)
        self.myMusicInterface.currentIndexChanged.connect(
            self.stackWidgetIndexChangedSlot
        )
        self.myMusicInterface.nextToPlayCheckedCardsSig.connect(
            self.multiSongsNextPlaySlot
        )
        self.myMusicInterface.selectionModeStateChanged.connect(
            self.selectionModeStateChangedSlot
        )
        self.myMusicInterface.addSongsToCustomPlaylistSig.connect(
            self.addSongsToCustomPlaylist
        )
        self.myMusicInterface.addSongsToNewCustomPlaylistSig.connect(
            lambda songInfo_list: self.showCreatePlaylistPanel(songInfo_list)
        )
        self.myMusicInterface.addSongsToPlayingPlaylistSig.connect(
            self.addSongsToPlayingPlaylist
        )
        self.myMusicInterface.showLabelNavigationInterfaceSig.connect(
            self.showLabelNavigationInterface
        )
        # todo:将定时器信号连接到槽函数
        self.rescanSongInfoTimer.timeout.connect(self.rescanSongInfoTimerSlot)
        # todo:将自己的信号连接到槽函数
        self.showSubPlayWindowSig.connect(self.subPlayWindow.show)
        # todo:将专辑界面的信号连接到槽函数
        self.albumInterface.playAlbumSignal.connect(self.playAlbum)
        self.albumInterface.songCardPlaySig.connect(
            self.albumInterfaceSongCardPlaySlot)
        self.albumInterface.playOneSongCardSig.connect(self.playOneSongCard)
        self.albumInterface.nextToPlayOneSongSig.connect(
            self.songCardNextPlaySlot)
        self.albumInterface.addOneSongToPlayingSig.connect(
            self.addOneSongToPlayingPlaylist
        )
        self.albumInterface.addSongsToPlayingPlaylistSig.connect(
            self.addSongsToPlayingPlaylist
        )
        self.albumInterface.songListWidget.editSongCardSignal.connect(
            self.editSongCardSlot
        )
        self.albumInterface.saveAlbumInfoSig.connect(self.updateAlbumInfo)
        self.albumInterface.selectionModeStateChanged.connect(
            self.selectionModeStateChangedSlot
        )
        self.albumInterface.playCheckedCardsSig.connect(self.playCheckedCards)
        self.albumInterface.nextToPlayCheckedCardsSig.connect(
            self.multiSongsNextPlaySlot
        )
        self.albumInterface.addSongsToCustomPlaylistSig.connect(
            self.addSongsToCustomPlaylist
        )
        self.albumInterface.addSongsToNewCustomPlaylistSig.connect(
            lambda songInfo_list: self.showCreatePlaylistPanel(songInfo_list)
        )
        # todo:将播放列表界面信号连接到槽函数
        self.playlistCardInterface.selectionModeStateChanged.connect(
            self.selectionModeStateChangedSlot
        )
        self.playlistCardInterface.createPlaylistButton.clicked.connect(
            self.showCreatePlaylistPanel
        )
        self.playlistCardInterface.renamePlaylistSig.connect(
            self.renamePlaylistSlot)
        self.playlistCardInterface.deletePlaylistSig.connect(
            self.removePlaylistSlot)
        self.playlistCardInterface.playSig.connect(self.playCustomPlaylist)
        self.playlistCardInterface.nextToPlaySig.connect(
            self.multiSongsNextPlaySlot)
        # todo:将标签导航界面的信号连接到槽函数
        self.labelNavigationInterface.labelClicked.connect(
            self.navigationLabelClickedSlot
        )

    def referenceWidgets(self):
        """ 引用小部件 """
        self.songTabSongListWidget = self.myMusicInterface.songCardListWidget
        self.albumCardViewer = self.myMusicInterface.albumCardViewer

    def navigationDisplayModeChangedSlot(self, diaPlayMode: int):
        """ 导航界面显示模式改变对应的槽函数 """
        self.titleBar.title.setVisible(self.navigationInterface.isExpanded)
        self.adjustWidgetGeometry()
        self.navigationInterface.navigationMenu.stackUnder(self.playBar)
        # 如果现在显示的是字母导航界面就将其隐藏
        if self.subStackWidget.currentWidget() is self.labelNavigationInterface:
            self.subStackWidget.setCurrentIndex(0)

    def initPlaylist(self):
        """ 初始化播放列表 """
        self.player.setPlaylist(self.mediaPlaylist)
        # 如果没有上一次的播放列表数据，就设置默认的播放列表
        if not self.mediaPlaylist.playlist:
            songInfo_list = self.songTabSongListWidget.songInfo_list
            self.playingInterface.setPlaylist(songInfo_list)
            self.mediaPlaylist.setPlaylist(songInfo_list)
            self.mediaPlaylist.playlistType = PlaylistType.ALL_SONG_PLAYLIST
        # 将当前歌曲设置为上次关闭前播放的歌曲
        if self.mediaPlaylist.lastSongInfo in self.mediaPlaylist.playlist:
            index = self.mediaPlaylist.playlist.index(
                self.mediaPlaylist.lastSongInfo)
            self.mediaPlaylist.setCurrentIndex(index)
            self.playingInterface.setCurrentIndex(index)
            index = self.songTabSongListWidget.index(
                self.mediaPlaylist.lastSongInfo)
            if index is not None:
                self.songTabSongListWidget.setPlay(index)

    def switchPlayState(self):
        """ 播放按钮按下时根据播放器的状态来决定是暂停还是播放 """
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.setPlayButtonState(False)
            self.thumbnailToolBar.setButtonsEnabled(True)
        else:
            self.play()

    def setPlayButtonState(self, isPlay: bool):
        """ 设置播放按钮状态 """
        self.subPlayWindow.setPlay(isPlay)
        self.playBar.playButton.setPlay(isPlay)
        self.thumbnailToolBar.playButton.setPlay(isPlay)
        self.playingInterface.playBar.playButton.setPlay(isPlay)
        self.playingInterface.smallestModeInterface.playButton.setPlay(isPlay)

    def volumeChangedSlot(self, value):
        """ 音量滑动条数值改变时更换图标并设置音量 """
        self.player.setVolume(value)
        self.playBar.volumeButton.setVolumeLevel(value)
        if self.sender() == self.playBar.volumeSlider:
            self.playingInterface.playBar.volumeSlider.setValue(value)
        elif self.sender() == self.playingInterface.playBar.volumeSlider.volumeSlider:
            self.playBar.volumeSlider.setValue(value)

    def playerPositionChangeSlot(self):
        """ 播放器的播放进度改变时更新当前播放进度标签和进度条的值 """
        self.playBar.progressSlider.setValue(self.player.position())
        self.playBar.setCurrentTime(self.player.position())
        self.playingInterface.playBar.progressSlider.setValue(
            self.player.position())
        self.playingInterface.playBar.setCurrentTime(self.player.position())
        self.playingInterface.smallestModeInterface.progressBar.setValue(
            self.player.position()
        )

    def playerDurationChangeSlot(self):
        """ 播放器当前播放的歌曲变化时更新进度条的范围和总时长标签 """
        # 刚切换时得到的时长为0，所以需要先判断一下
        if self.player.duration() >= 1:
            self.playBar.setTotalTime(self.player.duration())
            self.playBar.progressSlider.setRange(0, self.player.duration())
            self.playingInterface.playBar.progressSlider.setRange(
                0, self.player.duration()
            )
            self.playingInterface.playBar.setTotalTime(self.player.duration())
            self.playingInterface.smallestModeInterface.progressBar.setRange(
                0, self.player.duration()
            )

    def progressSliderMoveSlot(self):
        """ 手动拖动进度条时改变当前播放进度标签和播放器的值 """
        if self.sender() == self.playBar.progressSlider:
            self.player.setPosition(self.playBar.progressSlider.value())
        elif self.sender() == self.playingInterface.playBar.progressSlider:
            self.player.setPosition(
                self.playingInterface.playBar.progressSlider.value()
            )
        self.playBar.setCurrentTime(self.player.position())
        self.playingInterface.playBar.setCurrentTime(self.player.position())
        self.playingInterface.smallestModeInterface.progressBar.setValue(
            self.player.position()
        )

    def songCardNextPlaySlot(self, songInfo: dict):
        """ 下一首播放动作触发对应的槽函数 """
        # 直接更新正在播放界面的播放列表
        index = self.mediaPlaylist.currentIndex()
        newPlaylist = (
            self.mediaPlaylist.playlist[: index + 1]
            + [songInfo]
            + self.mediaPlaylist.playlist[index + 1:]
        )
        self.playingInterface.setPlaylist(newPlaylist, False)
        self.playingInterface.setCurrentIndex(
            self.mediaPlaylist.currentIndex())
        self.mediaPlaylist.insertMedia(
            self.mediaPlaylist.currentIndex() + 1, songInfo)

    def songCardPlaySlot(self, songInfo: dict):
        """ 歌曲界面歌曲卡的播放按钮按下或者双击歌曲卡时播放这首歌 """
        # 如果当前播放列表模式不是歌曲文件夹的所有歌曲或者指定的歌曲不在播放列表中就刷新播放列表
        if (
            self.mediaPlaylist.playlistType != PlaylistType.ALL_SONG_PLAYLIST
            or songInfo not in self.mediaPlaylist.playlist
        ):
            self.mediaPlaylist.playlistType = PlaylistType.ALL_SONG_PLAYLIST
            songInfo_list = self.songTabSongListWidget.songInfo_list
            index = songInfo_list.index(songInfo)
            newPlaylist = songInfo_list[index:] + songInfo_list[0:index]
            self.mediaPlaylist.setPlaylist(newPlaylist)
            self.playingInterface.setPlaylist(newPlaylist)
        # 将播放列表的当前歌曲设置为指定的歌曲
        self.mediaPlaylist.setCurrentSong(songInfo)
        self.play()

    def playOneSongCard(self, songInfo: dict):
        """ 将播放列表重置为一首歌 """
        self.mediaPlaylist.playlistType = PlaylistType.SONG_CARD_PLAYLIST
        self.setPlaylist([songInfo])

    def switchLoopMode(self, loopMode):
        """ 根据随机播放按钮的状态和循环模式的状态决定播放器的播放模式 """
        # 记录按下随机播放前的循环模式
        self.mediaPlaylist.prePlayMode = loopMode
        # 更新按钮样式
        if self.sender() == self.playBar.loopModeButton:
            self.playingInterface.playBar.loopModeButton.setLoopMode(loopMode)
        elif self.sender() == self.playingInterface.playBar.loopModeButton:
            self.playBar.loopModeButton.setLoopMode(loopMode)
        if not self.mediaPlaylist.randPlayBtPressed:
            # 随机播放按钮没按下时，直接设置播放模式为循环模式按钮的状态
            self.mediaPlaylist.setPlaybackMode(loopMode)
        else:
            # 随机播放按钮按下时，如果选了单曲循环就直接设置为单曲循环，否则设置为随机播放
            if self.playBar.loopModeButton.loopMode == QMediaPlaylist.CurrentItemInLoop:
                self.mediaPlaylist.setPlaybackMode(
                    QMediaPlaylist.CurrentItemInLoop)
            else:
                self.mediaPlaylist.setPlaybackMode(QMediaPlaylist.Random)

    def setRandomPlay(self):
        """ 选择随机播放模式 """
        isRandomPlay = self.sender().isSelected
        self.mediaPlaylist.setRandomPlay(isRandomPlay)
        if self.sender() == self.playBar.randomPlayButton:
            self.playingInterface.playBar.randomPlayButton.setRandomPlay(
                isRandomPlay)
        elif self.sender() == self.playingInterface.playBar.randomPlayButton:
            self.playBar.randomPlayButton.setRandomPlay(isRandomPlay)

    def updateWindow(self, songInfo):
        """ 切换歌曲时更新歌曲卡、播放栏和子播放窗口 """
        index = self.songTabSongListWidget.index(songInfo)
        if index is not None:
            self.songTabSongListWidget.setPlay(index)
            self.playBar.updateSongInfoCard(songInfo)
            self.subPlayWindow.updateWindow(songInfo)
        # 更新专辑界面的歌曲卡
        if songInfo in self.albumInterface.songListWidget.songInfo_list:
            index = self.albumInterface.songListWidget.songInfo_list.index(
                songInfo)
            self.albumInterface.songListWidget.setPlay(index)

    def hotKeySlot(self, funcObj):
        """ 热键按下时显示子播放窗口并执行对应操作 """
        funcObj()
        self.showSubPlayWindowSig.emit()

    def playAlbum(self, playlist: list):
        """ 播放专辑中的歌曲 """
        # 直接更新播放列表
        self.playingInterface.setPlaylist(playlist)
        self.mediaPlaylist.playAlbum(playlist)
        self.play()

    def multiSongsNextPlaySlot(self, songInfo_list: list):
        """ 多首歌下一首播放动作触发对应的槽函数 """
        index = self.mediaPlaylist.currentIndex()
        newPlaylist = (
            self.mediaPlaylist.playlist[: index + 1]
            + songInfo_list
            + self.mediaPlaylist.playlist[index + 1:]
        )
        self.playingInterface.setPlaylist(newPlaylist, isResetIndex=False)
        self.playingInterface.setCurrentIndex(
            self.mediaPlaylist.currentIndex())
        # insertMedia的时候自动更新playlist列表，所以不必手动更新列表
        self.mediaPlaylist.insertMedias(
            self.mediaPlaylist.currentIndex() + 1, songInfo_list
        )

    def disorderPlayAll(self):
        """ 无序播放所有 """
        self.mediaPlaylist.playlistType = PlaylistType.ALL_SONG_PLAYLIST
        newPlaylist = deepcopy(self.songTabSongListWidget.songInfo_list)
        shuffle(newPlaylist)
        self.setPlaylist(newPlaylist)

    def play(self):
        """ 播放歌曲并改变按钮样式 """
        self.player.play()
        self.setPlayButtonState(True)
        # 显示被隐藏的歌曲信息卡
        if self.mediaPlaylist.playlist:
            if not self.playBar.songInfoCard.isVisible() and self.playBar.isVisible():
                self.playBar.songInfoCard.show()
                self.playBar.songInfoCard.updateSongInfoCard(
                    self.mediaPlaylist.playlist[0]
                )

    def initPlayBar(self):
        """ 从配置文件中读取配置数据来初始化播放栏 """
        # 初始化音量
        volume = self.settingInterface.getConfig("volume", 20)
        self.playingInterface.playBar.volumeSlider.setValue(volume)
        # 初始化亚克力颜色
        acrylicColor = self.settingInterface.getConfig(
            "playBar.acrylicColor", "225c7fCC"
        )
        self.playBar.setAcrylicColor(acrylicColor)
        # 初始化歌曲卡信息
        if self.mediaPlaylist.playlist:
            self.playBar.updateSongInfoCard(
                self.mediaPlaylist.getCurrentSong())

    def showPlayingInterface(self):
        """ 显示正在播放界面 """
        # 先退出选择模式
        self.exitSelectionMode()
        self.playBar.hide()
        self.titleBar.title.hide()
        self.titleBar.returnBt.show()
        if not self.playingInterface.isPlaylistVisible:
            self.playingInterface.songInfoCardChute.move(
                0, -self.playingInterface.playBar.height() + 68
            )
            self.playingInterface.playBar.show()
        self.subStackWidget.setCurrentIndex(0)
        self.totalStackWidget.setCurrentIndex(1)
        self.titleBar.setWhiteIcon(True)

    def hidePlayingInterface(self):
        """ 隐藏正在播放界面，返回我的音乐界面 """
        self.playBar.show()
        self.totalStackWidget.setCurrentIndex(0)
        # 根据当前界面设置标题栏按钮颜色
        if self.subStackWidget.currentWidget() is self.albumInterface:
            self.titleBar.returnBt.setWhiteIcon(False)
        else:
            self.titleBar.setWhiteIcon(False)
        # 隐藏返回按钮
        cond = self.subStackWidget.currentWidget() not in [
            self.albumInterface,
            self.labelNavigationInterface,
        ]
        if len(self.titleBar.stackWidgetIndex_list) == 1 and cond:
            self.titleBar.returnBt.hide()
        self.titleBar.title.setVisible(self.navigationInterface.isExpanded)

    def setQss(self):
        """ 设置层叠样式 """
        with open(r"app\resource\css\mainWindow.qss", encoding="utf-8") as f:
            self.setStyleSheet(f.read())

    def playingInterfaceCurrrentIndexChangedSlot(self, index):
        """ 正在播放界面下标变化槽函数 """
        self.mediaPlaylist.setCurrentIndex(index)
        self.play()

    def setMute(self, isMute):
        """ 设置静音 """
        self.player.setMuted(isMute)
        if self.sender() == self.playBar.volumeButton:
            self.playingInterface.playBar.volumeButton.setMute(isMute)
            self.playingInterface.playBar.volumeSlider.volumeButton.setMute(
                isMute)
        elif self.sender() == self.playingInterface.playBar.volumeSlider:
            self.playBar.volumeButton.setMute(isMute)

    def setFullScreen(self):
        """ 设置全屏 """
        if not self.isFullScreen():
            # 更新标题栏
            self.playBar.hide()
            self.titleBar.title.hide()
            self.titleBar.setWhiteIcon(True)
            self.titleBar.hide()
            # 切换到正在播放界面
            self.totalStackWidget.setCurrentIndex(1)
            self.showFullScreen()
            self.playingInterface.playBar.fillScreenButton.setFillScreen(True)
            if self.playingInterface.isPlaylistVisible:
                self.playingInterface.songInfoCardChute.move(
                    0, 258 - self.height())
        else:
            self.exitFullScreen()

    def exitFullScreen(self):
        """ 退出全屏 """
        if not self.isFullScreen():
            return
        self.showNormal()
        # 更新最大化按钮图标
        self.titleBar.maxBt.setMaxState(False)
        self.titleBar.returnBt.show()
        self.titleBar.show()
        self.playingInterface.playBar.fillScreenButton.setFillScreen(False)
        if self.playingInterface.isPlaylistVisible:
            self.playingInterface.songInfoCardChute.move(
                0, 258 - self.height())

    def showPlaylist(self):
        """ 显示正在播放界面的播放列表 """
        self.playingInterface.showPlaylist()
        # 直接设置播放栏上拉箭头按钮箭头方向朝下
        self.playingInterface.playBar.pullUpArrowButton.setArrowDirection(
            "down")
        if self.playingInterface.isPlaylistVisible:
            self.showPlayingInterface()

    def clearPlaylist(self):
        """ 清空播放列表 """
        self.mediaPlaylist.playlistType = PlaylistType.NO_PLAYLIST
        self.mediaPlaylist.clear()
        self.playingInterface.clearPlaylist()

    def addOneSongToPlayingPlaylist(self, songInfo: dict):
        """ 向正在播放列表尾部添加一首歌 """
        self.mediaPlaylist.addMedia(songInfo)
        self.playingInterface.setPlaylist(self.mediaPlaylist.playlist, False)

    def addSongsToPlayingPlaylist(self, songInfo_list: list):
        """ 向正在播放列表尾部添加多首歌 """
        self.mediaPlaylist.addMedias(songInfo_list)
        self.playingInterface.setPlaylist(self.mediaPlaylist.playlist, False)

    def switchToAlbumInterfaceByName(self, albumName: str, songerName: str):
        """ 由名字切换到专辑界面 """
        # 处于选择模式下直接返回
        if self.isInSelectionMode:
            return
        if (
            self.albumInterface.albumInfo.get("album") != albumName
            or self.albumInterface.albumInfo.get("songer") != songerName
            or not self.currentAlbumCard
        ):
            self.currentAlbumCard = self.albumCardViewer.findAlbumCardByName(
                albumName, songerName
            )
        if self.currentAlbumCard:
            self.__switchToAlbumInterface(self.currentAlbumCard.albumInfo)

    def switchToAlbumInterfaceByAlbumInfo(self, albumInfo: dict):
        """ 由专辑信息切换到专辑界面 """
        # 处于选择模式下直接返回
        if self.isInSelectionMode:
            return
        # 引用对应的专辑卡
        if self.albumInterface.albumInfo != albumInfo or not self.currentAlbumCard:
            self.currentAlbumCard = self.albumCardViewer.findAlbumCardByAlbumInfo(
                albumInfo
            )
        self.__switchToAlbumInterface(albumInfo)

    def __switchToAlbumInterface(self, albumInfo: dict):
        """ 切换到专辑界面 """
        # 退出全屏
        if self.isFullScreen():
            self.exitFullScreen()
        # 显示返回按钮
        self.titleBar.returnBt.show()
        QApplication.processEvents()
        self.albumInterface.updateWindow(albumInfo)
        self.subStackWidget.setCurrentWidget(self.albumInterface, duration=300)
        self.totalStackWidget.setCurrentIndex(0)
        self.playBar.show()
        self.titleBar.setWhiteIcon(True)
        self.titleBar.returnBt.setWhiteIcon(False)
        # 根据当前播放的歌曲设置歌曲卡播放状态
        songInfo = self.mediaPlaylist.playlist[self.mediaPlaylist.currentIndex(
        )]
        if songInfo in self.albumInterface.songInfo_list:
            index = self.albumInterface.songInfo_list.index(songInfo)
            self.albumInterface.songListWidget.setPlay(index)
        else:
            self.albumInterface.songListWidget.songCard_list[
                self.albumInterface.songListWidget.playingIndex
            ].setPlay(False)

    def albumInterfaceSongCardPlaySlot(self, index):
        """ 专辑界面歌曲卡播放按钮按下时 """
        albumSongList = self.albumInterface.songInfo_list
        # 播放模式不为专辑播放模式或者播放列表不同时直接刷新播放列表
        cond = (
            self.mediaPlaylist.playlistType != PlaylistType.ALBUM_CARD_PLAYLIST
            or self.mediaPlaylist.playlist != albumSongList
        )
        if cond:
            self.playAlbum(albumSongList)
        self.mediaPlaylist.setCurrentIndex(index)

    def returnButtonSlot(self):
        """ 标题栏返回按钮的槽函数 """
        if self.isInSelectionMode:
            return
        # 隐藏音量条
        self.playingInterface.playBar.volumeSlider.hide()
        if self.totalStackWidget.currentWidget() == self.playingInterface:
            self.hidePlayingInterface()
        else:
            # 当前界面不是albumInterface或者labelNavigationInterface时弹出下标列表的最后一个下标
            cond = self.subStackWidget.currentWidget() not in [
                self.albumInterface,
                self.labelNavigationInterface,
            ]
            if self.titleBar.stackWidgetIndex_list and cond:
                self.titleBar.stackWidgetIndex_list.pop()
            if self.titleBar.stackWidgetIndex_list:
                stackWidgetName, index = self.titleBar.stackWidgetIndex_list[-1]
                if stackWidgetName == "myMusicInterfaceStackWidget":
                    self.myMusicInterface.stackedWidget.setCurrentIndex(index)
                    if self.subStackWidget.currentWidget() != self.albumInterface:
                        self.subStackWidget.setCurrentIndex(
                            0,
                            True,
                            False,
                            duration=200,
                            easingCurve=QEasingCurve.InCubic,
                        )
                    else:
                        self.subStackWidget.setCurrentIndex(0, True)
                    self.navigationInterface.setCurrentIndex(0)
                    self.myMusicInterface.setSelectedButton(index)
                elif stackWidgetName == "subStackWidget":
                    isShowNextWidgetDirectly = not (
                        self.subStackWidget.currentWidget() is self.settingInterface
                    )
                    self.subStackWidget.setCurrentIndex(
                        index, True, isShowNextWidgetDirectly, 200, QEasingCurve.InCubic
                    )
                    self.navigationInterface.setCurrentIndex(index)
                if len(self.titleBar.stackWidgetIndex_list) == 1:
                    # 没有上一个下标时隐藏返回按钮
                    self.titleBar.returnBt.hide()
        # 更新按钮颜色
        self.titleBar.setWhiteIcon(False)

    def stackWidgetIndexChangedSlot(self, index):
        """ 堆叠窗口下标改变时的槽函数 """
        if self.sender() is self.navigationInterface:
            if self.subStackWidget.currentIndex() == index:
                return
            self.titleBar.stackWidgetIndex_list.append(
                ("subStackWidget", index))
            self.titleBar.setWhiteIcon(False)
        elif self.sender() is self.myMusicInterface:
            self.titleBar.stackWidgetIndex_list.append(
                ("myMusicInterfaceStackWidget", index)
            )
        self.titleBar.returnBt.show()

    def editSongCardSlot(self, oldSongInfo: dict, newSongInfo: dict):
        """ 编辑歌曲卡完成信号的槽函数 """
        self.mediaPlaylist.updateOneSongInfo(oldSongInfo, newSongInfo)
        self.playingInterface.updateOneSongCard(oldSongInfo, newSongInfo)
        if self.sender() == self.albumInterface.songListWidget:
            self.songTabSongListWidget.updateOneSongCard(
                oldSongInfo, newSongInfo)
        elif self.sender() == self.songTabSongListWidget:
            # 获取专辑信息并更新专辑界面和专辑信息
            albumInfo = self.albumCardViewer.updateOneAlbumCardSongInfo(
                newSongInfo)
            if albumInfo:
                self.albumInterface.updateWindow(albumInfo)
            self.albumInterface.updateOneSongCard(oldSongInfo, newSongInfo)

    def updateAlbumInfo(self, oldAlbumInfo: dict, newAlbumInfo: dict):
        """ 更新专辑卡及其对应的歌曲卡信息 """
        oldSongInfo_list = oldAlbumInfo["songInfo_list"]
        newSongInfo_list = newAlbumInfo["songInfo_list"]
        self.songTabSongListWidget.updateMultiSongCards(
            deepcopy(oldSongInfo_list), deepcopy(newSongInfo_list)
        )
        self.mediaPlaylist.updateMultiSongInfo(
            deepcopy(oldSongInfo_list), deepcopy(newSongInfo_list)
        )
        self.playingInterface.updateMultiSongCards(
            deepcopy(oldSongInfo_list), deepcopy(newSongInfo_list)
        )
        # 更新专辑标签界面
        with open("app\\data\\songInfo.json", encoding="utf-8") as f:
            songInfo_list = json.load(f)
        # 如果在专辑界面更新了专辑信息需要刷新对应的专辑卡的封面
        if self.sender() is self.albumInterface:
            self.currentAlbumCard.updateAlbumCover(newAlbumInfo["cover_path"])
        self.myMusicInterface.updateAlbumCardViewer(songInfo_list)

    def smallestModeStateChanedSlot(self, state: bool):
        """ 最小播放模式状态改变时更改标题栏按钮可见性和窗口是否置顶 """
        self.titleBar.closeBt.show()
        self.titleBar.returnBt.setHidden(state)
        self.titleBar.minBt.setHidden(state)
        self.titleBar.maxBt.setHidden(state)
        self.windowEffect.setWindowStayOnTop(self.winId(), state)

    def showSmallestModeInterface(self):
        """ 切换到最小化播放模式 """
        self.showPlayingInterface()
        self.playingInterface.showSmallestModeInterface()

    def selectionModeStateChangedSlot(self, isOpenSelectionMode: bool):
        """ 进入/退出选择模式信号的槽函数 """
        self.isInSelectionMode = isOpenSelectionMode
        self.playBar.setHidden(isOpenSelectionMode)

    def playCheckedCards(self, songInfo_list: list):
        """ 重置播放列表为所有选中的歌曲卡中的歌曲 """
        self.mediaPlaylist.playlistType = PlaylistType.CUSTOM_PLAYLIST
        self.setPlaylist(songInfo_list)

    def setPlaylist(self, playlist: list):
        """ 设置播放列表 """
        self.playingInterface.setPlaylist(playlist)
        self.mediaPlaylist.setPlaylist(playlist)
        self.play()

    def switchToSettingInterface(self):
        """ 切换到设置界面 """
        # 先退出选择模式再切换界面
        self.exitSelectionMode()
        self.subStackWidget.setCurrentWidget(
            self.settingInterface, duration=300)

    def switchToMyMusicInterface(self):
        """ 切换到我的音乐界面 """
        self.exitSelectionMode()
        self.subStackWidget.setCurrentWidget(self.myMusicInterface)

    def switchToPlaylistCardInterface(self):
        """ 切换到播放列表卡界面 """
        self.exitSelectionMode()
        self.subStackWidget.setCurrentWidget(
            self.playlistCardInterface, duration=300)

    def exitSelectionMode(self):
        """ 退出选择模式 """
        if not self.isInSelectionMode:
            return
        self.myMusicInterface.exitSelectionMode()
        self.albumInterface.exitSelectionMode()
        self.playlistCardInterface.exitSelectionMode()

    def readCustomPlaylists(self):
        """ 读取自定义播放列表 """
        # 如果没有播放列表文件夹就创建一个
        path = "app\\Playlists"
        if not os.path.exists(path):
            os.mkdir(path)
        # 获取播放列表
        self.customPlaylists = []
        playlistFile_list = os.listdir(path)
        for playlistFile in playlistFile_list:
            with open(os.path.join(path, playlistFile), encoding="utf-8") as f:
                self.customPlaylists.append(json.load(f))

    def showCreatePlaylistPanel(self, songInfo_list: list = None):
        """ 显示创建播放列表面板 """
        createPlaylistPanel = CreatePlaylistPanel(self, songInfo_list)
        createPlaylistPanel.createPlaylistSig.connect(self.createPlaylistSlot)
        createPlaylistPanel.exec_()

    def createPlaylistSlot(self, playlist: dict):
        """ 创建播放列表 """
        self.customPlaylists.append(playlist)
        self.playlistCardInterface.addOnePlaylistCard(playlist)
        self.navigationInterface.updateWindow()

    def renamePlaylistSlot(self, oldPlaylist: dict, newPlaylist: dict):
        """ 重命名播放列表槽函数 """
        index = self.customPlaylists.index(oldPlaylist)
        self.customPlaylists[index] = newPlaylist
        self.navigationInterface.updateWindow()

    def removePlaylistSlot(self, playlist: dict):
        """ 删除播放列表槽函数 """
        self.customPlaylists.remove(playlist)
        self.navigationInterface.updateWindow()

    def playCustomPlaylist(self, songInfo_list: list):
        """ 播放自定义播放列表中的所有歌曲 """
        self.playCheckedCards(songInfo_list)

    def addSongsToCustomPlaylist(self, playlistName: str, songInfo_list: list):
        """ 将歌曲添加到自定义播放列表中 """
        playlist = self.playlistCardInterface.addSongsToPlaylist(
            playlistName, songInfo_list
        )
        index = self.getCustomPlaylistIndexByName(playlistName)
        self.customPlaylists[index] = deepcopy(playlist)

    def getCustomPlaylistIndexByName(self, playlistName: str) -> int:
        """ 通过播放列表名字得到播放列表的下标 """
        for index, playlist in enumerate(self.customPlaylists):
            if playlist["playlistName"] == playlistName:
                return index
        raise Exception(f'指定的播放列表"{playlistName}"不存在')

    def showLabelNavigationInterface(self, label_list: list, layout: str):
        """ 显示标签导航界面 """
        self.labelNavigationInterface.setLabels(label_list, layout)
        self.subStackWidget.setCurrentWidget(
            self.labelNavigationInterface, duration=300
        )

    def navigationLabelClickedSlot(self, label: str):
        """ 导航标签点击槽函数 """
        self.myMusicInterface.scrollToLabel(label)
        self.subStackWidget.setCurrentWidget(
            self.subStackWidget.previousWidget)

    def rescanSongInfoTimerSlot(self):
        """ 重新扫描歌曲信息 """
        if not self.isInSelectionMode and self.myMusicInterface.hasSongModified():
            stateTooltip = StateTooltip("正在更新歌曲列表", "要耐心等待哦 ٩(๑>◡<๑)۶ ", self)
            stateTooltip.show()
            self.myMusicInterface.rescanSongInfo()
            stateTooltip.setState(True)
