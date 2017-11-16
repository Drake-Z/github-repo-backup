#! python3
# -*- coding: utf-8 -*-
# @Author: Drake-Z
# @Date:   2017-11-15 21:00:45
# @Last Modified time: 2017-11-16 17:52:24

import os
import sys
import yaml
import subprocess
import logging
from git import Repo


def excute(cmd):
    """
    执行 command
    :param cmd: command 字符串
    :type return: NoneType
    :return: None
    """
    logger.debug(cmd)
    p = subprocess.Popen(cmd,
                         shell=True,
                         bufsize=0,  # 0=unbuffered, 1=line-buffered, else buffer-size
                         stdout=subprocess.PIPE)
    # p.poll() 实时查询 程序运行是否完毕
    while p.poll() is None:
        line = p.stdout.readline()
        line = str(line, encoding="utf-8")
        if line:
            print("[cmd] " + line.strip())
    return None


def match_branch(dir_name):
    """
    输出 git 仓库的所有本地 HEAD 以外的远程分支名列表
    :param dir_name: git 仓库路径
    :type return: list
    :return: ["origin/xxxxx",...]
    """
    repo = Repo("{dir_name}/".format(dir_name=dir_name))
    git = repo.git
    branch_str = git.branch("-a")
    logger.debug("repo 所有 branch:\n{str}".format(str=branch_str))
    str_list = [z[10:] for z in branch_str.split("\n") if "->" not in z and "remotes/" in z]
    logger.debug("得到所有远程 branch:\n{str_list}".format(str_list=str_list))
    return str_list


def clone_repo(repo_list):
    """
    clone 输入列表中的所有 git 仓库
    :param repo_list: git 仓库路径列表 list
    :type return: NoneType
    :return: None
    """
    logger.debug("repo_list:\n" + yaml.dump(repo_list, default_flow_style=False) + "\n")
    logger.info("将 clone 以下 repo:\n" + "\n".join([z[0] for z in repo_list]))
    for dir_name, repo_url in repo_list:
        logger.info("clone repo: {dir_name}".format(dir_name=dir_name))
        cmd = ("git submodule add --force {repo_url} {dir_name}"
               ).format(repo_url=repo_url, dir_name=dir_name)
        excute(cmd=cmd)

        logger.debug("clone {dir_name} other branch".format(dir_name=dir_name))
        branchs = match_branch(dir_name=dir_name)
        os.chdir("{dir_name}/".format(dir_name=dir_name))
        logger.debug("cd 到 repo 文件夹: " + os.getcwd())
        for remote_branch in branchs:
            cmd = ("git branch --track {local_branch} {remote_branch}"
                   ).format(local_branch=remote_branch.split("/")[1], remote_branch=remote_branch)
            excute(cmd=cmd)
        excute(cmd="git fetch --all")
        excute(cmd="git pull --all")
        os.chdir("..")
        logger.debug("cd 到主文件夹: " + os.getcwd())
        logger.info("repo {dir_name} clone 完毕\n".format(dir_name=dir_name))
    return None


def get_repo_list():
    """
    加载 repo_list.yaml 获得仓库链接列表
    :type return: list
    :return: [(repo_name, repo_url),...]
    """
    repo_list_path = os.path.split(sys.argv[0])[0] + "/repo_list.yaml"
    with open(repo_list_path, "r", encoding="utf-8") as file:
        content = yaml.load(file)
        repo_list = [(".".join(z.split("/")[-2:]), z) for z in content]
        return repo_list


def create_logger(debug):
    """
    创建 logger
    :param debug: 是否 debug
    :type return: logging.Logger
    :return: logger
    """
    logging.basicConfig(format=("[%(asctime)s %(levelname)s "
                                "module:%(module)s func:%(funcName)s line:%(lineno)d]\n"
                                " %(message)s"),
                        datefmt="%H:%M:%S",)
    global logger
    logger = logging.getLogger(__name__)
    level = [logging.INFO, logging.DEBUG][debug]
    logger.setLevel(level)

repo_list = get_repo_list()
create_logger(debug=1)
clone_repo(repo_list=repo_list)
