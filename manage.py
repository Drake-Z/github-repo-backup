#! python3
# -*- coding: utf-8 -*-
# @Author: Drake-Z
# @Date:   2017-11-15 21:00:45
# @Last Modified time: 2017-11-15 22:46:42

import os
import sys
import yaml
import subprocess


def excute(cmd):
    p = subprocess.Popen(cmd,
                         bufsize=0,  # 0=unbuffered, 1=line-buffered, else buffer-size
                         stdout=subprocess.PIPE)
    # p.poll() 实时查询 程序运行是否完毕
    while p.poll() is None:
        line = p.stdout.readline()
        line = str(line, encoding="utf-8")
        if line:
            print(line)


def clone_repo(repo_list):
    for repo_name, repo_url in repo_list:
        cmd = ("git clone --recursive --depth 1 {repo_url} {repo_name}"
               ).format(repo_url=repo_url, repo_name=repo_name)
        excute(cmd=cmd)

repo_list_path = os.path.split(sys.argv[0])[0] + "\\repo_list.yaml"
with open(repo_list_path, "r", encoding="utf-8") as file:
    repo_list = [(z.split("/")[0], z) for z in yaml.load(repo_list_path)]


clone_repo(repo_list=repo_list)
