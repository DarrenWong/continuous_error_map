#!/usr/bin/python3

import carla
import numpy as np
import os
import csv
import math
from transforms3d.euler import euler2quat

from recorder.sensor import Sensor


class IMU(Sensor):
    def __init__(self, uid, name: str, base_save_dir: str, parent, carla_actor: carla.Sensor):
        super().__init__(uid, name, base_save_dir, parent, carla_actor)
        self.save_dir = '{}/{}'.format(base_save_dir, self.name)
        self.first_tick = True

    def save_to_disk_impl(self, save_dir, sensor_data, debug=False) -> bool:
        os.makedirs(self.save_dir, exist_ok=True)
        fieldnames = ['frame',
                      'timestamp',
                      'angular_velocity_x', 'angular_velocity_y', 'angular_velocity_z',
                      'linear_acceleration_x', 'linear_acceleration_y', 'linear_acceleration_z',
                      'orientation_w', 'orientation_x', 'orientation_y','orientation_z']

        if self.first_tick:
            print("save_to_disk_impl")

            #self.save_vehicle_info()
            with open('{}/imu.csv'.format(self.save_dir), 'w', encoding='utf-8') as csv_file:
                print("csv",fieldnames,csv_file)
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                if self.first_tick:
                    writer.writeheader()
                    self.first_tick = False

        with open('{}/imu.csv'.format(self.save_dir), 'a', encoding='utf-8') as csv_file:
            print(csv_file, fieldnames)
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            print("test",sensor_data)

            roll = math.radians(sensor_data.transform.rotation.roll)
            pitch = -math.radians(sensor_data.transform.rotation.pitch)
            yaw = -math.radians(sensor_data.transform.rotation.yaw)
            print("test2")

            quat = euler2quat(roll, pitch, yaw)
            print("csv line",quat)
            print("test3")

            csv_line = {'frame': sensor_data.frame,
                        'timestamp': sensor_data.timestamp,
                        'angular_velocity_x': -sensor_data.gyroscope.x,
                        'angular_velocity_y': sensor_data.gyroscope.y,
                        'angular_velocity_z': -sensor_data.gyroscope.z,
                        'linear_acceleration_x': sensor_data.accelerometer.x,
                        'linear_acceleration_y': -sensor_data.accelerometer.y,
                        'linear_acceleration_z': sensor_data.accelerometer.z,
                        'orientation_w': quat[0],
                        'orientation_x': quat[1],
                        'orientation_y': quat[2],                       
                        'orientation_z': quat[3]                      
                        }
            print(csv_line)
            writer.writerow(csv_line)

        if debug:
           print("\tIMU data recorded: uid={} name={}".format(self.uid, self.name))
        return True

