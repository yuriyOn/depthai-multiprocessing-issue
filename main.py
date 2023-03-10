#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import multiprocessing
from workers import Worker


class MainProcess:
    def __init__(self,
                  IPs,
                  disable_depth):
        self.workers = []
        for i, ip in enumerate(IPs):
            stop_event = multiprocessing.Event()
            capture = i < 1  # Only capture with the first camera
            self.workers.append(Worker(ip,
                                       stop_event,
                                       capture,
                                       disable_depth))

    def __call__(self):
        try:
            for worker in self.workers:
                worker.start()

            while True:
                time.sleep(5)

        except Exception as e:
            print(e)

        finally:
            print('Main execution loop ended!')
            for worker in self.workers:
                worker.stop_event.set()
            for worker in self.workers:
                worker.join(timeout=5)
                if worker.is_alive():
                    worker.terminate()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d",
                        "--disable",
                        help="Disable depth queue of devices following the first one from loading",
                        action='store_true')
    args = parser.parse_args()

    IPs = ['1.0.0.109', '1.0.0.49']
    main = MainProcess(IPs, args.disable)
    main()
