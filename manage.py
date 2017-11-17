#! python3
# -*- coding: utf-8 -*-
# @Author: Drake-Z
# @Date:   2017-11-15 21:00:45
# @Last Modified time: 2017-11-17 15:52:17

import os
import yaml
import subprocess
import logging
from git import Repo
from datetime import datetime
import time

import py_zip_file


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
    p.communicate()
    return None


def match_branch(dir_path):
    """
    输出 git 仓库的所有本地 HEAD 以外的远程分支名列表
    :param dir_path: git 仓库路径
    :type return: list
    :return: ["origin/xxxxx",...]
    """
    def condition(z):
        if "->" not in z and "issue" not in z and "remotes/" in z:
            return True
        else:
            return False
    logger.debug("GitPython 加载 {dir_name}".format(dir_name=dir_path.split("/")[-1]))
    repo = Repo("{dir_path}".format(dir_path=dir_path))
    git = repo.git
    sha1 = repo.commit("HEAD").hexsha[:7]
    branch_str = git.branch("-a")
    logger.debug("repo 所有 branch:\n{str}".format(str=branch_str))
    str_list = [z[10:] for z in branch_str.split("\n") if condition(z)]
    logger.debug("得到所有远程 branch:\n{str_list}".format(str_list=str_list))
    return str_list, sha1


def clone_repo(repo_list):
    """
    clone 输入列表中的所有 git 仓库
    :param repo_list: git 仓库路径列表 list
    :type return: NoneType
    :return: None
    """
    excute(cmd="rm -rf repos-backup/manage.py")
    assert isinstance(repo_list, list)
    logger.debug("repo_list:\n" + yaml.dump(repo_list, default_flow_style=False) + "\n")
    logger.info("将 clone 以下 repo:\n" + "\n".join([z[0] for z in repo_list]))
    for dir_name, repo_url in repo_list:
        logger.info("clone repo: {dir_name}".format(dir_name=dir_name))
        dir_path = "repos-backup/{dir_name}".format(dir_name=dir_name)

        cmd = ("git submodule add --force {repo_url} {dir_path}"
               ).format(repo_url=repo_url, dir_path=dir_path)
        excute(cmd=cmd)

        logger.debug("clone {dir_name} other branch".format(dir_name=dir_name))
        branchs, sha1 = match_branch(dir_path=dir_path)
        try:
            os.chdir(dir_path)
        except FileNotFoundError:
            logger.info(("{dir_path} 文件夹不存在！！请确认 {dir_name} 项目没有删除。"
                         "克隆 {dir_path} 失败\n\n"
                         ).format(dir_path=dir_path, dir_name=dir_name))
            continue
        logger.debug("cd 到 repo 文件夹: " + os.getcwd())
        for remote_branch in branchs:
            cmd = ("git branch --track {local_branch} {remote_branch}"
                   ).format(local_branch=remote_branch.split("/")[1], remote_branch=remote_branch)
            excute(cmd=cmd)
        excute(cmd="git fetch --all")
        excute(cmd="git pull --all")
        os.chdir("../..")
        logger.debug("已 cd 到主文件夹: " + os.getcwd())

        excute(cmd="rm -rf {dir_path}*zip".format(dir_path=dir_path))
        logger.debug("{dir_name} 删除之前的压缩包".format(dir_name=dir_name))
        filepath = zip_repo(dir_path=dir_path, sha1=sha1) + ".zip"

        logger.debug("压缩包大小: {size}".format(size=int(os.path.getsize(filepath) / 1024 / 1024)))
        logger.debug("是否分割: {bool}".format(bool=int(os.path.getsize(filepath) / 1024 / 1024) > 95))
        if int(os.path.getsize(filepath) / 1024 / 1024) > 95:
            zip_dir = filepath[:-4] + " zip"
            os.makedirs(zip_dir)
            cmd = ("zipsplit -n 99614720  -b {filepath} {zip_dir}"
                   ).format(filepath=filepath.replace(" ", "\ "), zip_dir=zip_dir.replace(" ", "\ "))
            excute(cmd=cmd)
            logger.debug("压缩文件夹下文件:\n" + str(os.listdir(zip_dir)))
            excute(cmd="rm -rf {filepath}".format(filepath=filepath.replace(" ", "\ ")))
            assert os.path.exists(filepath) is False, filepath + " 没有被删除"

        logger.debug("压缩 {dir_name} 完毕".format(dir_name=dir_name))
        excute(cmd="rm -rf {dir_path}".format(dir_path=dir_path))
        assert os.path.exists(dir_path) is False, dir_path + " 没有被删除"

        logger.info("repo {dir_name} clone 完毕\n\n".format(dir_name=dir_name))
    return None


def zip_repo(dir_path, sha1):
    logger.debug("开始压缩 {dir_path}".format(dir_path=dir_path))
    name = ("{dir_path} @ {sha1} {date}"
            ).format(dir_path=dir_path, sha1=sha1, date=str(datetime.now())[:-10].replace(":", "."))
    py_zip_file.main(zip_path=[dir_path], zip_name=name)
    logger.debug("{dir_path} 压缩完毕".format(dir_path=dir_path))
    return name


def get_repo_list():
    """
    加载 repo_list.yaml 获得仓库链接列表
    :type return: list
    :return: [(repo_name, repo_url),...]
    """
    repo_list_path = "./repo_list.yaml"
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
# repo_list = [(".".join(z.split("/")[-2:]), z) for z in ["https://github.com/Drake-Z/drake-z.github.io"]]
clone_repo(repo_list=repo_list)
