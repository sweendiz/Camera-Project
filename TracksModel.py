# -*- coding: utf-8 -*-
from PyQt5 import  QtCore


class TracksModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
        """ Tracks model to save tracks in this model and show tracks in QListView
        """
        QtCore.QAbstractListModel.__init__(self)
        self.tracks = []

    def rowCount(self, parent):
        return len(self.tracks)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        if(index.row()>=len(self.tracks)):
            print 'NOT'
        track_id = self.tracks[index.row()][0]
        if role == QtCore.Qt.DisplayRole:
            return str(track_id)
        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            self.tracks[row][0] = value
            print 'update susccs'
            return True
        return False

    def removeRow(self, row):
        if row>=0 and row<len(self.tracks):
            self.beginRemoveRows(QtCore.QModelIndex(),row, row+1)
            del self.tracks[row]
            self.endRemoveRows()
            #self.rowsRemoved.emit(self.createIndex(0, 0),
            #                      self.createIndex(row, 0))
        else:
            print 'can not remove object'

    def flags(self, index):
        flags = super(self.__class__, self).flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        flags |= QtCore.Qt.ItemIsSelectable
        flags |= QtCore.Qt.ItemIsEnabled
        return flags

    def addTrack(self, track):
        for index, existing_track in enumerate(self.tracks):
            if(existing_track[0] == track[0]):
                self.tracks[index][1] = track[1]
                return
        row = len(self.tracks)
        self.beginInsertRows(QtCore.QModelIndex(),row, row+1)
        self.tracks.append(track)
        self.endInsertRows()
        
    def clear(self):
        self.tracks = []

    def filterTracks(self, size):
        newTracks = []
        changed = False
        for track in self.tracks:
            rect = track[1]
            if(rect[0]+rect[2]/2 > size[0] or
                    rect[1]+rect[3]/2 > size[1]):
                changed = True
                continue
            elif(rect[0]+rect[2]/2 < 0 or
                 rect[1]+rect[3]/2 < 0):
                changed = True
                continue
            newTracks.append(track)
        self.tracks = newTracks
        if(changed):
            self.dataChanged.emit(self.createIndex(0, 0),
                                  self.createIndex(len(self.tracks)-1, 0))
