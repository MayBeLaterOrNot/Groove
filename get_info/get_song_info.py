# coding:utf-8
import json
import os
import re
import time

from mutagen import File

from my_functions.adjust_album_name import adjustAlbumName


class GetSongInfo():
    """ 创建一个获取和保存歌曲信息的类 """

    def __init__(self, targetFolderPath_list: list):
        # 获取音频文件夹列表
        self.targetFolderPath_list = targetFolderPath_list
        if not targetFolderPath_list:
            self.targetFolderPath_list = []
        self.songInfo_list = []
        self.getInfo()

    def scanTargetFolderSongInfo(self, targetFolderPath_list: list):
        """ 扫描指定文件夹的歌曲信息并更新歌曲信息 """
        self.targetFolderPath_list = targetFolderPath_list
        if not os.path.exists('Data'):
            os.mkdir('Data')
        with open('Data\\songInfo.json', 'w', encoding='utf-8') as f:
            json.dump([{}], f)
        self.songInfo_list = []
        self.getInfo()

    def getInfo(self):
        """ 从指定的目录读取符合匹配规则的歌曲的标签卡信息 """
        filePath_list = []
        for target_path in self.targetFolderPath_list:
            for _, _, sub_filename_list in os.walk(target_path):
                break
            # 更新文件路径列表
            filePath_list += [
                os.path.join(target_path, file_name) for file_name in sub_filename_list]

        # 获取符合匹配音频文件名和路径列表
        self.split_song_list(filePath_list)
        # 如果数据文件夹不存在就创建一个
        if not os.path.exists('Data'):
            os.mkdir('Data')
        # 从json文件读取旧信息
        oldData = [{}]
        if os.path.exists('Data\\songInfo.json'):
            with open('Data\\songInfo.json', 'r', encoding='utf-8') as f:
                try:
                    oldData = json.load(f)
                except:
                    pass

        oldSongPath_list = [
            oldFileInfo.get('songPath') for oldFileInfo in oldData]

        # 判断旧文件路径列表是否与新文件名列表相等
        if set(self.songPath_list) == set(oldSongPath_list) and len(oldSongPath_list) == len(self.songPath_list):
            # 如果文件路径完全相等就直接获取以前的文件信息并返回
            self.songInfo_list = oldData.copy()
            return
        newSongPath_set = set(self.songPath_list)
        oldSongPath_set = set(oldSongPath_list)
        # 计算文件路径差集
        diffSongPath_list = list(newSongPath_set - oldSongPath_set)
        # 计算文件路径的并集
        commonSongPath_set = newSongPath_set & oldSongPath_set

        # 根据文件路径并集获取部分文件信息字典
        if commonSongPath_set:
            self.songInfo_list = [
                oldSongInfo_dict for oldSongInfo_dict in oldData
                if oldSongInfo_dict['songPath'] in commonSongPath_set
            ]
        # 如果有差集的存在就需要更新json文件
        if not (newSongPath_set < oldSongPath_set and commonSongPath_set):
            # 获取后缀名，歌名，歌手名列表
            self.split_song_list(diffSongPath_list, flag=1)
            argZip = zip(self.song_list, self.songPath_list,
                         self.songname_list, self.songer_list,
                         self.suffix_list)
            for index, (song, songPath, songname, songer, suffix) in enumerate(argZip):
                id_card = File(songPath)
                # 获取时间戳
                createTime = os.path.getctime(songPath)
                # 将时间戳转换为时间结构
                timeStruct = time.localtime(createTime)
                # 格式化时间结构
                createTime = time.strftime('%Y-%m-%d %H:%M:%S', timeStruct)
                album_list, tcon, year, duration, tracknumber = self.fetch_album_tcon_year_trkn(
                    suffix, id_card)
                # 将歌曲信息字典插入列表
                self.songInfo_list.append({
                    'song': song,
                    'songPath': songPath,
                    'songer': songer,
                    'songName': songname,
                    'album': album_list,
                    'tcon': tcon,
                    'year': year,
                    'tracknumber': tracknumber,
                    'duration': duration,
                    'suffix': suffix,
                    'createTime': createTime,
                })
        self.sortByCreateTime()
        # 更新json文件
        with open('Data\\songInfo.json', 'w', encoding='utf-8') as f:
            json.dump(self.songInfo_list, f)

    def split_song_list(self, filePath_list, flag=0):
        """分离歌手名，歌名和后缀名,flag用于表示是否将匹配到的音频文件拆开,
        flag = 1为拆开,flag=0为不拆开，update_songList用于更新歌曲文件列表"""
        self.songPath_list = filePath_list.copy()
        # 获取文件名列表
        fileName_list = [
            filePath.split('\\')[-1] for filePath in filePath_list
        ]
        self.song_list = fileName_list.copy()
        # 创建列表
        self.songer_list, self.songname_list, self.suffix_list = [], [], []
        rex = r'(.+) - (.+)(\.mp3)|(.+) - (.+)(\.flac)|(.+) - (.+)(\.m4a)'

        for file_name, file_path in zip(fileName_list, filePath_list):
            Match = re.match(rex, file_name)
            if Match and flag == 1:
                if Match.group(1):
                    self.songer_list.append(Match.group(1))
                    self.songname_list.append(Match.group(2))
                    self.suffix_list.append(Match.group(3))
                elif Match.group(4):
                    self.songer_list.append(Match.group(4))
                    self.songname_list.append(Match.group(5))
                    self.suffix_list.append(Match.group(6))
                else:
                    self.songer_list.append(Match.group(7))
                    self.songname_list.append(Match.group(8))
                    self.suffix_list.append(Match.group(9))
            elif not Match:
                self.song_list.remove(file_name)
                self.songPath_list.remove(file_path)

    def fetch_album_tcon_year_trkn(self, suffix, id_card):
        """ 根据文件的后缀名来获取专辑信息及时长 """
        if suffix == '.mp3':
            # 如果没有标题则添加标题
            album = str(id_card['TALB'][0]) if id_card.get('TALB') else '未知专辑'
            # 曲目
            tracknumber = str(
                id_card['TRCK'][0]) if id_card.get('TRCK') else '0'
            tracknumber = self.adjustTrackNumber(tracknumber, suffix)
            # 流派
            tcon = str(id_card['TCON'][0]) if id_card.get('TCON') else '未知流派'
            if id_card.get('TDRC'):
                year = str(id_card['TDRC'][0]) + \
                    '年' if len(str(id_card['TDRC'])) == 4 else '未知年份'
            else:
                year = '未知年份'
            duration = f'{int(id_card.info.length//60)}:{int(id_card.info.length%60):02}'

        elif suffix == '.flac':
            album = id_card.get('album')[0] if id_card.get('album') else '未知专辑'
            tracknumber = id_card['tracknumber'][0] if id_card.get(
                'tracknumber') else '0'
            tracknumber = self.adjustTrackNumber(tracknumber, suffix)
            tcon = id_card.get('genre')[0] if id_card.get('genre') else '未知流派'
            year = id_card.get('year')[0][:4] + \
                '年' if id_card.get('year') else '未知年份'
            duration = f'{int(id_card.info.length//60)}:{int(id_card.info.length%60):02}'

        elif suffix == '.m4a':
            album = id_card.get('©alb')[0] if id_card.get('©alb') else '未知专辑'
            # m4a的曲目标签还应包括专辑中的总曲数,得到的是元组
            tracknumber = str(
                id_card['trkn'][0]) if id_card.get('trkn') else '(0, 0)'
            tracknumber = self.adjustTrackNumber(tracknumber, suffix)
            tcon = id_card.get('©gen')[0] if id_card.get('©gen') else '未知流派'
            year = id_card.get('©day')[0][:4] + \
                '年' if id_card.get('©day') else '未知年份'
            duration = f'{int(id_card.info.length//60)}:{int(id_card.info.length%60):02}'

        # album作为列表返回，最后元素是改过的专辑名，第一个是原名
        album_list = adjustAlbumName(album)
        return album_list, tcon, year, duration, tracknumber

    def sortByCreateTime(self):
        """ 依据文件创建日期排序文件信息列表 """
        self.songInfo_list.sort(
            key=lambda songInfo: songInfo['createTime'], reverse=True)

    def sortByDictOrder(self):
        """ 以字典序排序文件信息列表 """
        self.songInfo_list.sort(key=lambda songInfo: songInfo['songName'])

    def sortBySonger(self):
        """ 以歌手名排序文件信息列表 """
        self.songInfo_list.sort(key=lambda songInfo: songInfo['songer'])

    def adjustTrackNumber(self, trackNum: str, suffix):
        """ 调整曲目编号 """
        # 删除前导0
        if suffix == '.m4a':
            trackNum = trackNum.replace(' ', '')
            trackNum_list = trackNum[1:-1].split(',')
            trackNum_list = [int(i.lstrip('0')) if i !=
                             '0' else int(i) for i in trackNum_list]
            trackNum = str(tuple(trackNum_list))
        else:
            if trackNum != '0':
                trackNum = trackNum.lstrip('0')
            # 处理a/b
            trackNum = trackNum.split('/')[0]
            # 处理An
            if trackNum[0].upper() == 'A':
                trackNum = trackNum[1:]
        return trackNum
