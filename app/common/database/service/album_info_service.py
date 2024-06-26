# coding:utf-8
from typing import List

from PyQt5.QtSql import QSqlDatabase

from ..dao import AlbumInfoDao
from ..entity import AlbumInfo

from.service_base import ServiceBase


class AlbumInfoService(ServiceBase):
    """ Album information service """

    def __init__(self, db: QSqlDatabase = None):
        super().__init__()
        self.albumInfoDao = AlbumInfoDao(db)

    def createTable(self) -> bool:
        return self.albumInfoDao.createTable()

    def findBy(self, **condition) -> AlbumInfo:
        return self.albumInfoDao.selectBy(**condition)

    def listBy(self, **condition) -> List[AlbumInfo]:
        return self.albumInfoDao.listBy(**condition)

    def listAll(self) -> List[AlbumInfo]:
        return self.albumInfoDao.listAll()

    def listLike(self, **condition) -> List[AlbumInfo]:
        return self.albumInfoDao.listLike(**condition)

    def listByIds(self, ids: List[str]) -> List[AlbumInfo]:
        return self.albumInfoDao.listByIds(ids)

    def listBySingerAlbums(self, singers: List[str], albums: List[str]) -> List[AlbumInfo]:
        """ list album information by singer names and album names """
        return self.albumInfoDao.listBySingerAlbums(singers, albums)

    def modify(self, id: str, field: str, value) -> bool:
        return self.albumInfoDao.update(id, field, value)

    def modifyById(self, albumInfo: AlbumInfo) -> bool:
        return self.albumInfoDao.updateById(albumInfo)

    def modifyByIds(self, albumInfos: List[AlbumInfo]) -> bool:
        return self.albumInfoDao.updateByIds(albumInfos)

    def add(self, albumInfo: AlbumInfo) -> bool:
        return self.albumInfoDao.insert(albumInfo)

    def addBatch(self, albumInfos: List[AlbumInfo]) -> bool:
        return self.albumInfoDao.insertBatch(albumInfos)

    def removeById(self, id: str) -> bool:
        return self.albumInfoDao.deleteById(id)

    def removeByIds(self, ids: List[str]) -> bool:
        return self.albumInfoDao.deleteByIds(ids)

    def removeBySingerAlbums(self, singers: List[str], albums: List[str]) -> bool:
        """ list album information by singer names and album names """
        return self.albumInfoDao.deleteBySingerAlbums(singers, albums)

    def clearTable(self) -> bool:
        return self.albumInfoDao.clearTable()

    def setDatabase(self, db: QSqlDatabase):
        self.albumInfoDao.setDatabase(db)
