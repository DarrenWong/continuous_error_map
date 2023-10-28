#!/usr/bin/env python3
import rosbag
from std_msgs.msg import Header
from sensor_msgs import point_cloud2
from sensor_msgs.msg import Imu
import glob
import rospy
import numpy as np
import open3d as o3d
from sensor_msgs.msg import PointCloud2
from sensor_msgs.msg import PointField
import math
import cv2
from cv_bridge import CvBridge

frequency_gnss = 100
frequency_imu = 100
frequency_lidar = 10.0
frequency_gt = 100
frequency_camera = 20.0

frequency_odometer = 100


import csv

imu_path = "imu/imu.csv"
ros_bag = rosbag.Bag('town03_lidar_noise_0.5_imu_noise_clearsunset.bag', 'w')
# lidar_rawdata_list = sorted(glob.glob("velodyne/*.npy"))
# print(lidar_rawdata_list)
index=0
with open(imu_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    print(reader)
    bridge = CvBridge()

    for row in reader:
        print(row['timestamp'], row['angular_velocity_x'])
        
        imu_msg = Imu()
        imu_msg.header.frame_id= 'velodyne'
        imu_msg.header.stamp= rospy.Time.from_sec(float(row['timestamp']))

        # Carla uses a left-handed coordinate convention (X forward, Y right, Z up).
        # Here, these measurements are converted to the right-handed ROS convention
        #  (X forward, Y left, Z up).
        imu_msg.angular_velocity.x = float(row['angular_velocity_x'])
        imu_msg.angular_velocity.y = float(row['angular_velocity_y'])
        imu_msg.angular_velocity.z = float(row['angular_velocity_z'])

        imu_msg.linear_acceleration.x = float(row['linear_acceleration_x'])
        imu_msg.linear_acceleration.y = float(row['linear_acceleration_y'])
        imu_msg.linear_acceleration.z = float(row['linear_acceleration_z'])

        imu_msg.orientation.w = float(row['orientation_w'])
        imu_msg.orientation.x = float(row['orientation_x'])
        imu_msg.orientation.y = float(row['orientation_y'])
        imu_msg.orientation.z = float(row['orientation_z'])  
        #print(imu_msg)  
        ros_bag.write('/carla/ego_vehicle/imu', imu_msg, rospy.Time.from_sec(float(row['timestamp'])))

        # write lidar 10hz
        if index%10 == 0:
            lidar_name = "{:0>10d}".format(int(row['frame']))
            lidar_name = "velodyne/"+str(lidar_name)+".npy"
            print(lidar_name)
            pointcloud_raw = np.load(lidar_name)
            o3d_pcd = o3d.geometry.PointCloud()
            o3d_pcd.points = o3d.utility.Vector3dVector(pointcloud_raw[:, 0:3])

            new_list = []
            for i in range(len(pointcloud_raw)):
                # cal ring    
                dis = math.sqrt(pointcloud_raw[i][0] * pointcloud_raw[i][0] + pointcloud_raw[i][1] * pointcloud_raw[i][1]);
                ele_rad = math.atan2(pointcloud_raw[i][2], dis);
                # for 32 line lidar
                factor = 31/(10-(-30))
                scan_id = int((math.degrees(ele_rad) - (-30)) * factor + 0.5)
                #print(math.degrees(ele_rad),scan_id)
                new_array = [pointcloud_raw[i][0],  pointcloud_raw[i][1], pointcloud_raw[i][2], pointcloud_raw[i][3],scan_id,0]
                new_list.append(new_array)
            header = Header()
            header.frame_id = "velodyne"
            header.stamp =  imu_msg.header.stamp

            fields = [
                PointField('x', 0, PointField.FLOAT32, 1),
                PointField('y', 4, PointField.FLOAT32, 1),
                PointField('z', 8, PointField.FLOAT32, 1),
                PointField('intensity', 12, PointField.FLOAT32, 1),
                PointField('ring', 16, PointField.UINT16, 1),
                PointField('time', 18, PointField.FLOAT32, 1)]

            msg = point_cloud2.create_cloud(header, fields, new_list)
            msg.is_dense = True

            ros_bag.write('/carla/ego_vehicle/lidar', msg, header.stamp)
        # write image data 5hz
        # if index%5 == 0:
        #     image_name = "{:0>10d}".format(int(row['frame']))
        #     image_name = "image_2/"+str(image_name)+".png"
        #     print(image_name)
        #     cv_image = cv2.imread(image_name)      
        #     image_message = bridge.cv2_to_imgmsg(cv_image, encoding="bgr8")
        #     image_message.header.stamp = imu_msg.header.stamp
        #     ros_bag.write("/carla/ego_vehicle/image", image_message,  imu_msg.header.stamp)

        index = index+1;
        # if index>10000:
        #     break
       
    # for row in spamreader:
    #     print(', '.join(row))
ros_bag.close()
