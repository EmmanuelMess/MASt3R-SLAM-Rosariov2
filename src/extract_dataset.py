#!/usr/bin/python

import argparse

import os

import cv2

import numpy as np

from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

imu_topic = "/realsense/imu"
rgb_image_topic = "/realsense/color/image_raw"
depth_image_topic = "/realsense/depth/image_rect_raw"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bag", type=str)
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("-s", "--start", type=float, default=0.0)
    parser.add_argument("-e", "--end", type=float, default=float('inf'))

    args = parser.parse_args()

    # Create a typestore and get the string class.
    typestore = get_typestore(Stores.LATEST)
    
    os.makedirs(f"{args.output}", exist_ok=True)

    # Create reader instance and open for reading.
    with Reader(args.bag) as reader:
        print("Writing IMU data")    
        with open(f"{args.output}/accelerometer.txt", "wt") as imu:
            imu.write("# accelerometer data\n")
            imu.write(f"# file: '{args.bag}'\n")
            imu.write("# timestamp ax ay az\n")
        
            connections = [x for x in reader.connections if x.topic == imu_topic]
            for connection, timestamp, rawdata in reader.messages(connections=connections):
                timestamp_seconds = timestamp * 1e-9
                if not (args.start <= timestamp_seconds <= args.end):
                    continue
          
                msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
                imu.write(f"{timestamp_seconds} {msg.linear_acceleration.x} {msg.linear_acceleration.y} {msg.linear_acceleration.z}\n")
            
        print("Writing RGB data")    
        with open(f"{args.output}/rgb.txt", "wt") as rgb:                
            os.makedirs(f"{args.output}/rgb", exist_ok=True)
            
            rgb.write("# color images\n")
            rgb.write(f"# file: '{args.bag}'\n")
            rgb.write("# timestamp filename\n")
            
            connections = [x for x in reader.connections if x.topic == rgb_image_topic]
            for connection, timestamp, rawdata in reader.messages(connections=connections):
                timestamp_seconds = timestamp * 1e-9
                if not (args.start <= timestamp_seconds <= args.end):
                    continue
                
                path = f"rgb/{timestamp_seconds}.png"
            
                msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
                rgb.write(f"{timestamp_seconds} {path}\n")
                
                success = cv2.imwrite(f"{args.output}/{path}", msg.data.reshape(msg.height, msg.width, 3))
        
        print("Writing depth data")    
        with open(f"{args.output}/depth.txt", "wt") as depth:            
            os.makedirs(f"{args.output}/depth", exist_ok=True)
            
            depth.write("# depth maps\n")
            depth.write(f"# file: '{args.bag}'\n")
            depth.write("# timestamp filename\n")
            
            connections = [x for x in reader.connections if x.topic == depth_image_topic]
            for connection, timestamp, rawdata in reader.messages(connections=connections):
                timestamp_seconds = timestamp * 1e-9
                if not (args.start <= timestamp_seconds <= args.end):
                    continue
                
                path = f"depth/{timestamp_seconds}.png"
                msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
                depth.write(f"{timestamp_seconds} {path}\n")
                
                images = msg.data.reshape(msg.height, msg.width, 2)
                image = np.uint16(images[:, :, 1]) * (2**8) + np.uint16(images[:, :, 0])

                success = cv2.imwrite(f"{args.output}/{path}", image)
           
if __name__ == '__main__':
    main()
    

