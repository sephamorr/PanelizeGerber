#!/usr/bin/python
import ConfigParser, math, sys
import Queue as queue
import os
from subprocess import call
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''



width=0 
height =0
boardarea=0
maxWidth =0
maxHeight=0
Config=0
def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def calculateUsage(rows, cols):
   usedSpace=rows*cols*width*height
   return usedSpace/boardarea
def getMargins(rows, cols,rotate):
  if rotate==0:
    h=height
    w=width
  else:
    h=width
    w=height
  if rows*h>maxHeight:
    return -1
  if cols*w>maxWidth:
    return -1

  rt=(h+w) * (h+w) -4*(h*w-boardarea/rows/cols)
  top=math.sqrt(rt)-(h+w)
  return top/4

def place(rows , cols,rotate):
  print bcolors.OKBLUE
  print("placing (%s rows, %s cols)" % (rows, cols))
  print bcolors.ENDC
  #swap if it makes it better
  if rotate!=0:
    #print "Swapping to prefer horizontal"
    rold=rows
    rows=cols
    cols=rold


  margin=getMargins(rows,cols,rotate)
  file = open('placement.txt','w')
  x=1*margin;
  y=1*margin;
  if rotate==1:
    nStr='n*rotated90'
    oldRows=rows
    rows=cols
    cols=oldRows
    h=width
    w=height
  else:
    nStr='n'
    w=width
    h=height
  for i in range(0,rows):
    for j in range(0,cols):
      a=x+j*w+(1+(2*j))*margin;
      b=y+i*h+(1+(2*i))*margin;
      file.write(nStr + ' ' + "%.5f" % a + ' ' + "%.5f" % b + '\n')
  file.close();

def callGerbMerge():
  os.system("echo 'y' | python -B gerbmerge/gerbmerge.py --place-file=placement.txt gerbmerge/layout2.cfg")
  os.system("mkdir output 2>/dev/null")
  os.system("mv merge* output/")
  os.system("rm placement.txt")
def main():

    try:
      from simpleparse.parser import Parser                    
    except ImportError:
      print "cannot import simpleparse, it's probably not installed."
      print "look here: http://sourceforge.net/projects/simpleparse/files/simpleparse/"
      quit()

    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    global Config
    Config = ConfigParser.ConfigParser()
    Config.read("config.cfg")
    global width
    global height
    global boardarea 
    global maxWidth 
    global maxHeight
    #width = float(ConfigSectionMap("def")['width'])
    #height = float(ConfigSectionMap("def")['height'])
    (width, height)=detectDimensions(4)
    #quit()
    maxWidth = float(ConfigSectionMap("def")['maxwidth'])
    maxHeight = float(ConfigSectionMap("def")['maxheight'])

    boardarea =  float(ConfigSectionMap("def")['maxarea'])

    maxNumberOfBoards = int(boardarea / width / height)
    q=queue.PriorityQueue()
    for rows in range(1,maxNumberOfBoards+1):
     for cols in range(1,maxNumberOfBoards+1):
      area=rows*height*cols*width
      for rotate in range(0,2):
        if(area<boardarea):
          usage=calculateUsage(rows,cols)
          margins=getMargins(rows,cols,rotate)
          t = {'rows': rows, 'cols': cols}
          if rotate==0:
            deltaDimensions=cols*width-rows*height
          else:
            deltaDimensions=cols*height-rows*width
            #give a 1% bonus to wider preference
          q.put((-usage,-margins,math.fabs(deltaDimensions)*(1+(1-float(rotate)/100)),rotate,t))

    while not q.empty():

      option=q.get()
      t=option[4]
      #print("%s" % t)
      usage=-option[0]
      rotate=option[3]
      margins=-option[1]
      if margins<=0:
        continue
      print bcolors.WARNING
      if rotate==1:
        rot=", rotated"
        dimx=t['cols']*height
        dimy=t['rows']*width
      else:
        rot=""
        dimx=t['cols']*width
        dimy=t['rows']*height
      print("Option: (%s rows, %s cols %s)=(%s , %s)" % (t['rows'],t['cols'],rot,dimx,dimy))
      print(bcolors.ENDC + "Usage:%.1f%%" % (float(usage)*100))
      print("Margins:%.3fin" % margins)
      var = raw_input("Sufficient?y/n: ")
      if var=="y":
        place(t['rows'],t['cols'],rotate)
        callGerbMerge()
        return

    #check ideal max number
    #try line
    
def detectDimensions(gerberDecimals):
  searchfile = open("n.oln", "r")
  inches=1
  #detect unit type
  for line in searchfile:
    if "G71*" in line:
      inches=0
  searchfile.seek(0)

  xmin=sys.float_info.max
  ymin=sys.float_info.max
  xmax=sys.float_info.min
  ymax=sys.float_info.min

  for line in searchfile:
    #print "LINE:"
    #print line
    if line.find("X")!=0:
      #print "X%f" % line.find("X")
      continue
    ypos=line.find("Y")
    #print "Y%f" %ypos
    dpos=line.find("D")
    #print "D%f" %dpos
    if (dpos-ypos)!=(ypos):
      continue
    #is a good line
      #note, supports eagle 2.4 units (actually X.4, change here)

    dimX=float(line[1:ypos])/math.pow(10,gerberDecimals)
    dimY=float(line[ypos+1:dpos])/math.pow(10,gerberDecimals)
    if dimX>xmax:
      xmax=dimX
    elif dimX<xmin:
      xmin=dimX

    if dimY>ymax:
      ymax=dimY
    elif dimY<ymin:
      ymin=dimY

    #print "(%.4f,%.4f)" % (dimX,dimY)
  #print "MIN:(%.4f,%.4f)" %(xmin,ymin)
  #print "MAX:(%.4f,%.4f)" %(xmax,ymax)
  print "DIMENSIONS detected as: (%.4f, %.4f)" %(xmax-xmin,ymax-ymin)
  xtot=xmax-xmin
  ytot=ymax-ymin
  if inches==0:
    xtot/=25.4
    ytot/=25.4
  searchfile.close()
  return (xtot, ytot)
# call main
if __name__ == '__main__':
  main()
