# coding:utf-8
from typing import Dict, List

from common.singleton import Singleton

from ..entity import AlbumInfo, SongInfo
from ..service import AlbumInfoService, SongInfoService
from ..utils import UUIDUtils


class AlbumInfoController(Singleton):
    """ 专辑信息控制器 """

    def __init__(self):
        super().__init__()
        self.albumInfoService = AlbumInfoService()
        self.songInfoService = SongInfoService()

    def getAlbumInfos(self, songInfos: List[SongInfo]):
        """ 获取专辑信息列表

        Parameters
        ----------
        songInfos: List[SongInfo]
            歌曲信息列表

        Returns
        -------
        albumInfos: List[AlbumInfo]
            专辑信息列表
        """
        # 从数据库获取所有专辑信息
        cacheAlbumInfos = {
            (i.singer+'_'+i.album): i for i in self.albumInfoService.listAll()
        }

        addedAlbumInfos = []    # type: List[AlbumInfo]
        expiredAlbumInfos = {}  # type:Dict[str, AlbumInfo]
        currentAlbumInfos = {}  # type:Dict[str, AlbumInfo]
        for songInfo in songInfos:
            key = songInfo.singer + '_' + songInfo.album
            t = songInfo.modifiedTime

            if key in cacheAlbumInfos:
                currentAlbumInfos[key] = cacheAlbumInfos[key]
                if currentAlbumInfos[key].modifiedTime < t:
                    currentAlbumInfos[key].modifiedTime = t
                    expiredAlbumInfos[key] = cacheAlbumInfos[key]
                    expiredAlbumInfos[key].modifiedTime = t

            elif key not in currentAlbumInfos:
                albumInfo = AlbumInfo(
                    id=UUIDUtils.getUUID(),
                    singer=songInfo.singer,
                    album=songInfo.album,
                    year=songInfo.year,
                    genre=songInfo.genre,
                    modifiedTime=t
                )
                currentAlbumInfos[key] = albumInfo
                addedAlbumInfos.append(albumInfo)

            else:
                if currentAlbumInfos[key].modifiedTime < t:
                    currentAlbumInfos[key].modifiedTime = t

        removedIds = []
        for i in set(cacheAlbumInfos.keys())-set(currentAlbumInfos.keys()):
            removedIds.append(cacheAlbumInfos[i].id)

        # 更新数据库
        self.albumInfoService.removeByIds(removedIds)
        for albumInfo in expiredAlbumInfos.values():
            self.albumInfoService.modify(
                albumInfo.id, 'modifiedTime', albumInfo.modifiedTime)

        self.albumInfoService.addBatch(addedAlbumInfos)

        # 排序专辑信息
        albumInfos = sorted(
            currentAlbumInfos.values(),
            key=lambda i: i.modifiedTime,
            reverse=True
        )

        return albumInfos

    def getAlbumInfo(self, singer: str, album: str):
        """ 获取一张专辑信息

        Paramters
        ---------
        singer: str
            歌手

        album: str
            专辑

        Returns
        -------
        albumInfo: AlbumInfo
            专辑信息，没有找到则返回 None
        """
        albumInfo = self.albumInfoService.findBy(singer=singer, album=album)
        if not albumInfo:
            return None

        albumInfo.songInfos = self.songInfoService.listBySingerAlbum(
            singer, album)
        return albumInfo