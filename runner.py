#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'MICROYU'

import os, subprocess, time
from threading import Timer
import logging
import csv

def get_tasklists(path='./tasklists/'):
    tasklists = []
    files = os.listdir(path)
    for file in files:
        if not os.path.isdir(file):
            tasklists.append(file)
    return path, tasklists

def delete_tasklist(dir='./tasklists/', filename='main.txt'):
    if filename != 'main.txt':
        os.remove(dir + filename)

class TaskRunner():
    def __init__(self):
        self.task_queue = []
        self.task_log_queue = []
        self.now_task = None
        self.timer = None
        self.proc = None

    def load_tasks(self, dir='./tasklists/', filename='main.txt'):
        self.reset()
        if not os.path.exists(dir):
            os.makedirs(dir)
        if not os.path.exists(dir + filename):
            ## os.mknod is not available on Windows
            f = open(dir + filename, 'w')
            f.close()
        csv_file = open(dir + filename, 'r')
        reader = csv.DictReader(csv_file)
        for row in reader:
            self.add(row['name'], row['cmd'], row['timeout'])

    def save_tasks(self, dir='./tasklists/', filename='main.txt'):
        csv_file = open(dir + filename, 'w')
        writer = csv.DictWriter(csv_file, fieldnames=('name', 'cmd', 'timeout'), lineterminator = '\n')
        writer.writeheader()
        for task in self.task_queue:
            epinfo = {"name": task['name'], "cmd": task['cmd'], "timeout": task['timeout']}
            writer.writerow(epinfo)

    def add(self, name, cmd, timeout):
        task = {'name': name, 'cmd': cmd, 'timeout': timeout, 'pid': None, 'status': 'ready', 'start_time': None}
        self.task_queue.append(task)
        self.task_log_queue.append("")
        self.save_tasks()
    
    def timeout_callback(self):
        os.system("TASKKILL /PID " + str(self.now_task['pid']) + " /F /T")

    def run(self):
        self.now_task = None
        now_task_index = 0
        for task in self.task_queue:
            if task['status'] == 'ready':
                self.now_task = task
                now_task_index = self.task_queue.index(task)
                break
        if self.now_task is None:
            return
        self.now_task['status'] = 'running'
        self.now_task['start_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
        
        self.proc = subprocess.Popen(self.now_task['cmd'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.now_task['pid'] = self.proc.pid
        
        if self.now_task['timeout'] != 'inf':
            self.timer = Timer(int(self.now_task['timeout']), self.timeout_callback)
            try:
                self.timer.start()
                stdout, stderr = self.proc.communicate()
            finally:
                self.timer.cancel()
        else:
            stdout, stderr = self.proc.communicate()
        self.task_log_queue[now_task_index] = stdout

        if self.is_running():
            self.now_task['status'] = 'done'
            self.run()

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timeout_callback()
        for task in self.task_queue:
            if task['status'] == 'running':
                task['status'] = 'ready'

    def reset_status(self):
        for task in self.task_queue:
            task['status'] = 'ready'
    
    def is_running(self):
        for task in self.task_queue:
            if task['status'] == 'running':
                return True
        return False

    def reset(self):
        self.task_queue = []
        self.task_log_queue = []

    def delete(self, index):
        self.task_queue.pop(int(index))
        self.task_log_queue.pop(int(index))
        self.save_tasks()

    def edit(self, index, name, cmd, timeout):
        index = int(index)
        self.task_queue[index]['name'] = name
        self.task_queue[index]['cmd'] = cmd
        self.task_queue[index]['timeout'] = timeout
        self.save_tasks()
    
    def get(self, index):
        index = int(index)
        return self.task_queue[index]['name'], self.task_queue[index]['cmd'], self.task_queue[index]['timeout']

    def get_log(self, index):
        return self.task_log_queue[int(index)]

if __name__ == "__main__":
    runner = TaskRunner()
    runner.load_tasks()
    runner.run()