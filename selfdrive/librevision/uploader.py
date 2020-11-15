#!/usr/bin/python3

import os
from time import sleep
#from natsort import natsorted

# iterate through ~/DATA and sort results
# check if no .tmp files exist
# compress and upload
# verify upload
# delete 

# TODO: threading and S3 uploader
#       replace natsort with a built in lib

def compress():
  # zip up the files to be uploaded
  path = os.path.expanduser("~") + "/DATA"
  folders = os.listdir(path)
  # compress to zip and delete mp4
  for d in folders:
    fullpath = path + "/"
    files = [x for x in os.listdir(fullpath + d)]
    if not any("tmp" in y for y in files) and not any(".zip" in y for y in files):
      #print("compressing {}".format(fullpath))
      os.system("cd {0}{1} && zip -r {1}.zip *".format(fullpath, d))
      os.system("find {0}{1} -name *.mp4 -delete".format(fullpath, d))
      os.system("find {0}{1} -name *.json -delete".format(fullpath, d))

  return(0)

def upload():
  # upload to S3 bucket
  path = os.path.expanduser("~") + "/.wocsor/uuid"
  with open(path, "r") as uuid_file:
    uuid = uuid_file.read().strip("\n")
    print(uuid)
  return(0)

def main():

  # delete incomplete segments
  path = os.path.expanduser("~") + "/DATA"
  folders = os.listdir(path)
  for d in folders:
    fullpath = path + "/"
    files = [x for x in os.listdir(fullpath + d)]
    if any("tmp" in y for y in files):
      os.system("rm -rf {0}{1}".format(fullpath, d))

  while True:
    compress()
    upload()
    sleep(30)

if __name__ == "__main__":

  main()
  
