#!/usr/bin/env python3

import depthai as dai


def create_RGBD_pipeline(control_queue_name,
                         rgb_queue_name,
                         depth_queue_name):
    queueNames = []
    queueNames.append(rgb_queue_name)

    # Create pipeline
    pipeline = dai.Pipeline()

    # Define source and output
    camRgb = pipeline.create(dai.node.ColorCamera)
    camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_12_MP)
    camRgb.setInterleaved(False)

    xoutRgb = pipeline.create(dai.node.XLinkOut)
    xoutRgb.setStreamName(rgb_queue_name)
    camRgb.still.link(xoutRgb.input)

    controlIn = pipeline.create(dai.node.XLinkIn)
    controlIn.setStreamName(control_queue_name)
    controlIn.out.link(camRgb.inputControl)

    queueNames.append(depth_queue_name)
    depth_resolution = dai.MonoCameraProperties.SensorResolution.THE_800_P
    mono_fps = 10

    # Define sources and outputs
    left = pipeline.create(dai.node.MonoCamera)
    right = pipeline.create(dai.node.MonoCamera)
    stereo = pipeline.create(dai.node.StereoDepth)
    depthOut = pipeline.create(dai.node.XLinkOut)
    depthOut.setStreamName(depth_queue_name)

    left.setResolution(depth_resolution)
    left.setBoardSocket(dai.CameraBoardSocket.LEFT)
    left.setFps(mono_fps)
    right.setResolution(depth_resolution)
    right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
    right.setFps(mono_fps)

    # Linking
    left.out.link(stereo.left)
    right.out.link(stereo.right)
    stereo.depth.link(depthOut.input)

    return pipeline
