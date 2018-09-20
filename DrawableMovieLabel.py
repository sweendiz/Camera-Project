# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtGui, QtCore
from TracksModel import TracksModel
import cv2
import pandas as pd
import sys
sys.path.append('KCFnb')
import kcftracker
import time
class DrawableMovieLabel(QtWidgets.QLabel):
    progress = QtCore.pyqtSignal([float])

    def __init__(self):
        QtWidgets.QLabel.__init__(self)
        self.painter = QtGui.QPainter()
        self.setScaledContents(True)
        self.globalId = 0
        self.cap = cv2.VideoCapture()
        self.model = TracksModel(self)
        try:
            self.cap.open(0)
        except:
            print 'Can not open Webcap!'
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.grabFrame)
        self.frameNumber = 0
        self.annotations = pd.DataFrame()
        self.grabFrame()
        self.kafkaProducer = []
        self.kafkaTopic = []

    def start(self):
        self.timer.start(30)

    def stop(self):
        self.timer.stop()

    def openVideo(self, videoAddress):
        self.cap.open(videoAddress)
        self.model.clear()
        self.annotations = pd.DataFrame()
        self.frameNumber = 0

    def mousePressEvent(self, event):
        self.x = event.x()*self.pixmap.width()/self.width()
        self.y = event.y()*self.pixmap.height()/self.height()

    def mouseMoveEvent(self, event):
        x = event.x()*self.pixmap.width()/self.width()
        y = event.y()*self.pixmap.height()/self.height()
        copyImage = self.pixmap.copy()
        self.painter.begin(copyImage)
        self.painter.setPen(QtGui.QPen(QtGui.QColor('#f46e42'), 3))
        self.painter.drawRect(self.x, self.y, x - self.x, y - self.y)
        self.painter.end()
        self.setPixmap(copyImage)

    def drawRect(self, id, rect):
        self.painter.begin(self.pixmap)
        self.painter.setPen(QtGui.QPen(QtGui.QColor('#c10d4c'), 3))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.painter.setFont(font)
        self.painter.drawRect(*rect)
        self.painter.drawText(QtCore.QPoint(rect[0], rect[1]), str(id))
        self.painter.end()

    def mouseReleaseEvent(self, event):
        x = event.x()*self.pixmap.width()/self.width()
        y = event.y()*self.pixmap.height()/self.height()
        rect = (self.x, self.y, x - self.x, y - self.y)
        self.drawRect(self.globalId, rect)
        self.setPixmap(self.pixmap)
        if(rect[2]==0 or rect[3]==0):
            return
        tracker = kcftracker.KCFTracker(True, True, True)
        #tracker = cv2.Tracker_create("KCF")
        rect = (min(rect[0], rect[0]+rect[2]),
                min(rect[1], rect[1]+rect[3]),
                abs(rect[2]),
                abs(rect[3]))
        tracker.init(rect, self.frame)
        self.model.addTrack([self.globalId, rect, tracker])
        self.globalId = self.globalId + 1

    def grabFrame(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frameNumber)
        ok, self.frame = self.cap.read()
        if(not ok):
            print 'can not read frame'
            return
        self.frameNumber = self.frameNumber+1
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        image = QtGui.QImage(frame, frame.shape[1], frame.shape[0],
                             frame.strides[0], QtGui.QImage.Format_RGB888)
        self.setPixmap(QtGui.QPixmap.fromImage(image))
        self.pixmap = QtGui.QPixmap.fromImage(image)
        self.track()
        self.model.filterTracks((self.pixmap.width(), self.pixmap.height()))
        self.drawExistingAnnotations()
        self.drawExistingRects()
        self.saveTracks()
        p = self.frameNumber*100/self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.progress.emit(p)

    def seekToPercent(self, percent):
        self.frameNumber = int(percent*int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))/100)
        self.grabFrame()
    
    def nextFrame(self):
        self.grabFrame()
    
    def prviousFrame(self):
        self.frameNumber = max(self.frameNumber - 2, 0)
        self.grabFrame()

    def saveTracks(self):
        ids = [track[0] for track in self.model.tracks]
        positions = [track[1] for track in self.model.tracks]
        if(len(ids) == 0):
            return
        df = pd.DataFrame(positions)
        df.columns = ['x', 'y', 'width', 'height']
        df['id'] = ids
        df['frameNumber'] = self.frameNumber
        self.annotations = pd.concat([self.annotations, df])
        ts = time.time()
        df['timestamp'] = ts
        # push to kafka
	df.set_index('id')
        if(self.kafkaTopic):
            for index, row in df.iterrows():
                print(row.to_json())
                self.kafkaProducer.send(self.kafkaTopic, row.to_json())

    def drawExistingAnnotations(self):
        if(len(self.annotations) < 2):
            return
        df_tracks = self.annotations[self.annotations['frameNumber'] == self.frameNumber]
        df_ids = df_tracks['id'].values
        df_positions = df_tracks[['x', 'y', 'width', 'height']].values
        for (id, rect) in zip(df_ids, df_positions):
            self.drawRect(id, rect)

    def drawExistingRects(self):
        for track in self.model.tracks:
            self.drawRect(track[0], track[1])
        self.setPixmap(self.pixmap)

    def track(self):
        for (index, track) in enumerate(self.model.tracks):
            tracker = track[2]
            if(tracker is not None):
                bbox = tracker.update(self.frame)
                if 1:
                    self.model.tracks[index][1] = bbox
            else:
                self.model.removeRow(index)
