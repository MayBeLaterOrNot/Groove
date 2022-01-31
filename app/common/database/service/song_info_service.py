# coding:utf-8
from typing import List

from PyQt5.QtSql import QSqlDatabase

from ..dao import SongInfoDao
from ..entity import SongInfo

from.service_base import ServiceBase


class SongInfoService(ServiceBase):
    """ 歌曲信息服务类 """

    def __init__(self, db: QSqlDatabase = None):
        super().__init__()
        self.songInfoDao = SongInfoDao(db)

    def createTable(self) -> bool:
        return self.songInfoDao.createTable()

    def findBy(self, **condition) -> SongInfo:
        return self.songInfoDao.selectBy(**condition)

    def findByFile(self, file: str):
        """ 通过文件路径查询歌曲信息 """
        return self.songInfoDao.selectByFile(str(file))

    def listBy(self, **condition) -> List[SongInfo]:
        return self.songInfoDao.listBy(**condition)

    def listAll(self) -> List[SongInfo]:
        return self.songInfoDao.listAll()

    def listByIds(self, files: list, repeat=False) -> List[SongInfo]:
        """ 通过文件位置查询歌曲信息

        Parameters
        ----------
        files: List[str]
            歌曲文件路径

        repeat: bool
            是否允许歌曲信息重复
        """
        songInfos = self.songInfoDao.listByIds(files)
        k = self.songInfoDao.fields[0]
        songInfos.sort(key=lambda i: files.index(i[k]))

        if len(songInfos) < len(files) and repeat:
            songInfoMap = {i.file: i for i in songInfos}
            songInfos = [songInfoMap[i].copy() for i in files]

        return songInfos

    def listBySingerAlbum(self, singer: str, album: str) -> List[SongInfo]:
        """ 通过歌手和专辑查询所有歌曲信息 """
        return self.songInfoDao.listBySingerAlbum(singer, album)

    def listBySingerAlbums(self, singers: List[str], albums: List[str]):
        """ 通过歌手和专辑列表查询所有歌曲信息 """
        return self.songInfoDao.listBySongerAlbums(singers, albums)

    def modify(self, file: str, field: str, value) -> bool:
        return self.songInfoDao.update(file, field, value)

    def modifyById(self, songInfo: SongInfo) -> bool:
        return self.songInfoDao.updateById(songInfo)

    def modifyByIds(self, songInfos: List[SongInfo]) -> bool:
        return self.songInfoDao.updateByIds(songInfos)

    def add(self, songInfo: SongInfo) -> bool:
        return self.songInfoDao.insert(songInfo)

    def addBatch(self, songInfos: List[SongInfo]) -> bool:
        return self.songInfoDao.insertBatch(songInfos)

    def removeById(self, file: str) -> bool:
        return self.songInfoDao.deleteById(file)

    def removeByIds(self, files: List[str]) -> bool:
        return self.songInfoDao.deleteByIds(files)

    def clearTable(self) -> bool:
        return self.songInfoDao.clearTable()

    def setDatabase(self, db: QSqlDatabase):
        """ 使用指定的数据库 """
        self.songInfoDao.setDatabase(db)
