#!/bin/bash

cd `dirname $0`
dirpath=`pwd`
str='s,Output=\",Output=\"'
str=$str$dirpath
str=$str'/,g'
cat genericCAM.cam | sed $str > preparedCAM.cam
