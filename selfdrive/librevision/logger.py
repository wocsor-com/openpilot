#! /usr/bin/python3

import cv2
from threading import Thread
import os
import datetime
import numpy as np
import json
from time import clock

from cereal import log
import cereal.messaging as messaging
from cereal.services import service_list

# TODO:
# - DATA LOGGING
#   - GPS, SPEED, ACCEL, STEER ANGLE, STEER TORQUE, GYRO, BRAKES, GAS, STEER_RATE, and many others
# - UPLOADER BY API
#   - upload each folder with video files and corresponding file
# - OBJECT RECOGNITION AND REPORTING ON CAN

class Cameras:
  def __init__(self, cam, path):

    self.frame_id = 0
    self.frame = 0
    self.ret = 0
    self.cam = cam
    self.cap = cv2.VideoCapture("/dev/" + cam)
    self.stop = False

    self.window_name = ''

    if path == 'pci-0000:03:00.0-usb-0:1:1.0':
      self.window_name = 'f_cam'
    elif path == 'pci-0000:03:00.0-usb-0:2:1.0':
      self.window_name = 'b_cam'
    elif path == 'pci-0000:04:00.0-usb-0:1:1.0':
      self.window_name = 'l_cam'
    elif path == 'pci-0000:04:00.0-usb-0:2:1.0':
      self.window_name = 'r_cam'

    self.logger(self.window_name)

  def start_thread(self):

    self.thread = Thread(target=self.update, args=())
    self.thread.daemon=True
    self.thread.start()

  def reset_cam(self):

    self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5) #brightness
    self.cap.set(cv2.CAP_PROP_SATURATION, 0.5) #saturation
    self.cap.set(cv2.CAP_PROP_GAIN, 0) #gain

  def night_mode(self):

    self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 1.0) #brightness
    self.cap.set(cv2.CAP_PROP_SATURATION, 0.5) #saturation
    self.cap.set(cv2.CAP_PROP_GAIN, 0.5) #gain

  def logger(self, cam):

    self.logdir = os.path.expanduser('~') + "/DATA/" + datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-00.000Z")
    if not os.path.exists(self.logdir):
      os.makedirs(self.logdir)
    self.out = cv2.VideoWriter(self.logdir + "/" + cam + ".tmp.mp4",cv2.VideoWriter_fourcc(*"mp4v"), 20, (800,600))
    self.frame_id = 0

  def write_video(self):

    if self.frame_id >= 3600:
      # 3 min segments
      self.out.release()
      # rename .tmp to mp4
      print(self.logdir+'/'+self.window_name)
      os.system("mv {0}/{1}.tmp.mp4 {0}/{1}.mp4".format(self.logdir, self.window_name))
      self.logger(self.window_name)
    if self.ret:
      self.out.write(self.frame)
    else: 
      # camera wasn't ready, write a black frame
      self.out.write(np.zeros((800,600,3), np.uint8))
    self.frame_id += 1
    return(self.logdir)

  def update(self):

    while True:
      self.ret, self.frame = self.cap.read()
      if self.stop:
        break

  def get_frame(self):

    return self.frame

  def get_prop(self, prop):

    return self.cap.get(prop)

  def set_cam(self, width, height, codec):

    # TODO: a string to float conversion
    if codec == "YUYV":
      set_codec = 1448695129.0
    elif codec == "MJPG":
      set_codec = 1196444237.0
    else:
      print("INVALID CODEC %s")
      set_codec = 1196444237.0
    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    self.cap.set(cv2.CAP_PROP_FPS, 30)
    self.cap.set(cv2.CAP_PROP_FOURCC, set_codec)

  def end(self):

    self.stop = True
    self.thread.join()
    self.cap.release()
    self.out.release()

class StateLog:

  def __init__(self):
    self.carstate = messaging.sub_sock('carState')
    self.gps_loc = messaging.sub_sock('gpsLocationExternal')
    self.car_state = None
    self.gps_info = None

  def update(self, logdir):
    ret = {}
    cs = messaging.recv_sock(self.carstate)
    gps = messaging.recv_sock(self.gps_loc)
    if cs is not None:
      self.car_state = cs
    if gps is not None:
      self.gps_info = gps
    if self.car_state is not None:    
      ret.update(self.car_state.to_dict())
    if self.gps_info is not None:
      ret.update(self.gps_info.to_dict())
    filename = logdir + '/' + 'log.json'
    with open(filename, 'a') as out:
      out.write(json.dumps(ret) + '\n')

def main():
  # get car info
  sl = StateLog()

  # get all cameras out of /dev and only list the even numbered devices
  devs =  [element for idx, element in enumerate(os.listdir("/dev")) if element.__contains__("video")]
  devices = devs[1::2]
  cameras = []

  campaths = {}

  for i in devices:
    campaths.update({i:os.popen('udevadm info --name=/dev/{} | grep ID_PATH= | cut -d "=" -f 2'.format(i)).read().rstrip()})

  print("VIDEO DEVICES FOUND: ")
  for dev, path in campaths.items():
    # do not address video0 (internal webcam)
    print(dev, path)
    cameras.append(Cameras(dev, path)) 
    
  print("PRESS ESC TO QUIT, N FOR NIGHT MODE, M FOR DAY MODE")

  ii = 0
  for cam in cameras:
    cam.set_cam(800, 600, "MJPG") # YUYV needs more bandwidth, this may change on the launch hardware.
    cam.start_thread()
    ii += 1
    
  while True:
    
    target_time = clock() + 0.05
    while clock() < target_time:
      pass

    for cam in cameras:
      frame = cam.get_frame()
      if cam.window_name == 'b_cam':
        # b_cam is inverted
        frame = cv2.flip(frame, 0)
      logdir = cam.write_video()

    current_logdir = logdir
    sl.update(logdir) 

if __name__ == "__main__":

  main()

  for cam in cameras:
    cam.end()
