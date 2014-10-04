#!/usr/bin/env python

import sys, cv, numpy, time
import os

from cuav.lib import cuav_util
from cuav.image import scanner
from MAVProxy.modules.lib import mp_image
from MAVProxy.modules.lib.mp_settings import MPSettings, MPSetting
from MAVProxy.modules.lib.wxsettings import WXSettings
from MAVProxy.modules.lib.mp_menu import *

from optparse import OptionParser
parser = OptionParser("thermal_view.py [options] <filename>")
(opts, args) = parser.parse_args()

if len(args) < 1:
    print("please supply an image file name")
    sys.exit(1)

def convert_image(filename, threshold, blue_threshold, green_threshold):
    '''convert a file'''
    pgm = cuav_util.PGM(filename)
    im_640 = numpy.zeros((480,640,3),dtype='uint8')
    scanner.thermal_convert(pgm.array, im_640, threshold, blue_threshold, green_threshold)

    color_img = cv.CreateImageHeader((640, 480), 8, 3)
    cv.SetData(color_img, im_640)
    return color_img

view_image = mp_image.MPImage(title='ThermalView',
                              width=640,
                              height=480,
                              mouse_events=False,
                              key_events=True,
                              can_zoom=True,
                              can_drag=True)

menu = MPMenuTop([])
view_menu = MPMenuSubMenu('View',
                          [MPMenuItem('Next Image\tCtrl+N', 'Next Image', 'nextImage'),
                           MPMenuItem('Previous Image\tCtrl+P', 'Previous Image', 'previousImage')
                          ])
menu.add(view_menu)
view_image.set_menu(menu)


settings = MPSettings(
    [ MPSetting('threshold', int, 6100, 'High Threshold', tab='Settings', range=(0,65535)),
      MPSetting('blue_threshold', float, 0.75, 'Blue Threshold', range=(0,1)),
      MPSetting('green_threshold', float, 0.4, 'Green Threshold', range=(0,1))])

changed = True

def settings_callback(setting):
    '''called on a changed setting'''
    global changed
    changed = True

settings.set_callback(settings_callback)

WXSettings(settings)

image_idx = 0

def file_list(directory, extensions):
  '''return file list for a directory'''
  flist = []
  for (root, dirs, files) in os.walk(directory):
    for f in files:
      extension = f.split('.')[-1]
      if extension.lower() in extensions:
        flist.append(os.path.join(root, f))
  return sorted(flist)

if os.path.isdir(args[0]):
    args = file_list(args[0], ['pgm'])

while True:
    if changed:
        if image_idx >= len(args):
            image_idx = 0
        if image_idx < 0:
            image_idx = len(args)-1
        filename = args[image_idx]
        view_image.set_title('View: %s' % filename)
        color_img = convert_image(filename, settings.threshold, settings.blue_threshold, settings.green_threshold)
        view_image.set_image(color_img, bgr=True)
        changed = False
    if view_image.is_alive():
        for event in view_image.events():
            if isinstance(event, MPMenuGeneric):
                if event.returnkey == 'nextImage':
                    image_idx += 1
                elif event.returnkey == 'previousImage':
                    image_idx -= 1
                changed = True
    time.sleep(0.1)
