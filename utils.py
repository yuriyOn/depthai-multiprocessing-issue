#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime


class TimeSync:
    def __init__(self,
                 rgb_queue_name,
                 depth_queue_name):
        self.rgb_queue_name = rgb_queue_name
        self.depth_queue_name = depth_queue_name
        self.reset_data()
        self.desired_delay = datetime.timedelta(microseconds = 100 * 1000)

    def reset_data(self):
        self.data = {self.rgb_queue_name: [],
                     self.depth_queue_name: []}

    def add_msg(self, name, msg):
        assert name in self.data, f'The {name} is not supported.'
        self.data[name].append({'msg': msg, 'seq': msg.getTimestamp()})
        # print(f'Received {name} at {msg.getTimestamp()}', flush=True)

        synced = {}
        for name, arr in self.data.items():
            for i, obj in enumerate(arr):
                if msg.getTimestamp() > obj['seq'] - self.desired_delay and \
                    msg.getTimestamp() < obj['seq'] + self.desired_delay:
                    synced[name] = obj['msg']
                    break
        if len(synced) == 2:  # depth and mono (or color)
            # Remove old msgs
            self.reset_data()
            return synced
        return {}
