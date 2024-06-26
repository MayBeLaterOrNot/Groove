# coding:utf-8
from common.picture import Cover
from common.database.entity import AlbumInfo
from components.app_bar import AppBarButtonFactory as BF
from components.app_bar import CollapsingAppBarBase


class AlbumInfoBar(CollapsingAppBarBase):
    """ Album information bar """

    def __init__(self, albumInfo: AlbumInfo, parent=None):
        self.setAlbumInfo(albumInfo)
        super().__init__(
            self.album,
            f'{self.singer}\n{self.year} • {self.genre}',
            self.albumCoverPath,
            'album',
            parent
        )

        self.setButtons([BF.PLAY, BF.ADD_TO, BF.SINGER, BF.ONLINE,
                        BF.EDIT_INFO, BF.DELETE])

    def setAlbumInfo(self, albumInfo: AlbumInfo):
        """ set album information """
        self.albumInfo = albumInfo if albumInfo else AlbumInfo()
        self.year = str(albumInfo.year or '')
        self.genre = albumInfo.genre or ''
        self.album = albumInfo.album or ''
        self.singer = albumInfo.singer or ''
        self.albumCoverPath = Cover(self.singer, self.album).path()

    def updateWindow(self, albumInfo: AlbumInfo):
        """ update window """
        self.setAlbumInfo(albumInfo)
        super().updateWindow(
            self.album,
            f'{self.singer}\n{self.year} • {self.genre}',
            self.albumCoverPath
        )
