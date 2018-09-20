#!/bin/bash

for file in `ls *.ui` ; do pyuic5 $file -o ui_${file%.*}.py; done
for file in `ls *.qrc` ; do pyrcc5 $file -o ${file%.*}_rc.py; done
