#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: Matt Sweeney
"""

from PyQt5 import QtWidgets, QtCore, QtGui
import sys
from DrawableMovieLabel import DrawableMovieLabel
import pandas as pd

sys.path.append('forms')
from ui_MainWindow import Ui_MainWindow
from kafka import KafkaProducer
import json

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.movie = DrawableMovieLabel()
        self.ui.horizontalLayout_2.addWidget(self.movie)
        self.ui.pushButton_browse.clicked.connect(self.openFile)
        self.ui.pushButton_start.clicked.connect(self.start_stop)
        self.ui.pushButton_remove.clicked.connect(self.removeTrack)
        self.ui.pushButton_save_annotation.clicked.connect(
                self.save_annotations)
        self.ui.pushButton_browse_annotaion.clicked.connect(
                self.open_annotations)
        self.ui.pushButton_next.clicked.connect(self.movie.nextFrame)
        self.ui.pushButton_previous.clicked.connect(self.movie.prviousFrame)
        self.ui.listView.setModel(self.movie.model)
        self.ui.listView.setEditTriggers(
                QtWidgets.QAbstractItemView.DoubleClicked)
        self.ui.horizontalSlider.setMinimum(0)
        self.ui.horizontalSlider.setMaximum(100)
        self.ui.horizontalSlider.valueChanged.connect(self.movie.seekToPercent)
        self.movie.progress.connect(self.ui.horizontalSlider.setValue)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.autoSave)
        self.timer.start(60*1000)
        self.ui.pushButton_kafkaConnect.clicked.connect(self.connectKafka)
    def connectKafka(self):
        try:
            self.movie.kafkaProducer = KafkaProducer(bootstrap_servers=self.ui.lineEdit_kafkaAddress.text())
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Kafka Connection", "Error in connection" + str(e))
        else:
            self.movie.kafkaTopic = self.ui.lineEdit_kafkaTpoic.text()
            QtWidgets.QMessageBox.information(self, "Kafka Connection", "Successfully Connect")



    def open_annotations(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                            'Annotation File')
        self.movie.annotations = pd.read_csv(fileName)
        if(len(self.movie.annotations) > 0):
            self.movie.globalId = self.movie.annotations['id'].max()+1
        self.ui.lineEdit_annotaion.setText(fileName)

    def save_annotations(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                                                            'Annotation File',
                                                            'annotation.csv')
        if(fileName):
            self.movie.annotations.to_csv(fileName)

    def autoSave(self):
        self.movie.annotations.to_csv('annotations_autosave.csv')

    def removeTrack(self):
        row = self.ui.listView.currentIndex().row()
        self.movie.model.removeRow(row)

    def start_stop(self):
        if(self.ui.pushButton_start.text() == 'Start'):
            self.movie.start()
            self.ui.pushButton_start.setText('Stop')
        else:
            self.movie.stop()
            self.ui.pushButton_start.setText('Start')

    def openFile(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'open video')
        if(fileName):
            self.ui.lineEdit.setText(fileName)
            self.movie.openVideo(fileName)
