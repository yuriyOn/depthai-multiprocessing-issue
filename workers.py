#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import datetime
from multiprocessing import Process


class Worker(Process):
    def __init__(self,
                 ip,
                 stop_event,
                 capture=True,
                 disable_depth=False):
        Process.__init__(self)
        self.ip = ip
        self.stop_event = stop_event
        self.capture = capture
        self.disable_depth = disable_depth
        self.timeout = datetime.timedelta(seconds = 1)

    def run(self):
        try:
            import depthai as dai
            from utils import TimeSync
            from pipeline import create_RGBD_pipeline

            control_queue_name = f'control_{self.ip}'
            rgb_queue_name = f'rgb_{self.ip}'
            depth_queue_name = f'depth_{self.ip}'

            self.sync = TimeSync(rgb_queue_name,
                                 depth_queue_name)

            device_info = dai.DeviceInfo(self.ip)
            pipeline = create_RGBD_pipeline(control_queue_name,
                                            rgb_queue_name,
                                            depth_queue_name)
            pipeline.setOpenVINOVersion(dai.OpenVINO.Version.VERSION_2022_1)

            with dai.Device(pipeline, device_info) as device:
                print(f'Camera with ip "{self.ip}" set up correctly!', flush=True)
                control_queue = device.getInputQueue(control_queue_name)
                rgb_queue = device.getOutputQueue(rgb_queue_name, 1, blocking=False)

                # This is the part of code that creates issues when multiple Depth queues
                # coming from different cameras are loaded by a separate process per camera
                depth_queue = None
                if not self.disable_depth:
                    print(f'Loading depth queue for the device with ip {self.ip}', flush=True)
                    depth_queue = device.getOutputQueue(depth_queue_name, 1, blocking=False)
                elif self.disable_depth and not self.capture:
                    print(f'Not loading depth queue for the device with ip {self.ip}', flush=True)

                while not self.stop_event.is_set():
                    if not self.capture:
                        # Only capture any photos with the first camera, just load the others
                        print(f'Not capturing with camera with ip: {self.ip}', flush=True)
                        time.sleep(60)
                        continue

                    if depth_queue is None:
                        depth_queue = device.getOutputQueue(depth_queue_name, 1, blocking=False)

                    request_datetime = datetime.datetime.now()
                    ctrl = dai.CameraControl()
                    ctrl.setCaptureStill(True)
                    control_queue.send(ctrl)

                    rgb = None
                    depth = None

                    msgs = {}
                    while not msgs and datetime.datetime.now() - request_datetime < self.timeout:
                        queueEvents = device.getQueueEvents(queueNames=(rgb_queue_name, depth_queue_name),
                                                            timeout=self.timeout)
                        if depth_queue_name in queueEvents:
                            depth = depth_queue.tryGet()
                            if depth is not None:
                                msgs = self.sync.add_msg(depth_queue_name, depth)
                                if rgb_queue_name in msgs and depth_queue_name in msgs:
                                    # Received syncronised messages
                                    break

                        if rgb_queue_name in queueEvents:
                            rgb = rgb_queue.tryGet()
                            if rgb is not None:
                                msgs = self.sync.add_msg(rgb_queue_name, rgb)

                    time_taken = (datetime.datetime.now() - request_datetime).total_seconds()
                    print(f'Time taken: {round(time_taken * 1000)} ms', flush=True)
                    time.sleep(2)

        except Exception as e:
            print(e, flush=True)
        finally:
            print(f'Closing the device with ip {self.ip}!', flush=True)
            device.close()
