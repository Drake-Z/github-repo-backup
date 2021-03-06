#! python3
# -*- coding: utf-8 -*-
# @Author: Drake-Z
# @Date:   2017-11-15 21:00:45
# @Last Modified time: 2018-01-20 17:02:44

import os
import yaml
import subprocess
import logging
from git import Repo
from datetime import datetime
import pytz


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
    repo = Repo(f"{dir_path}")
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
        logger.info(f"clone repo: {dir_name}")
        dir_path = f"repos-backup/{dir_name}"

        cmd = ("git submodule add --force {repo_url} {dir_path}"
               ).format(repo_url=repo_url, dir_path=dir_path)
        excute(cmd=cmd)

        logger.debug(f"clone {dir_name} other branch")
        try:
            sha1 = pull_other_branch(dir_name=dir_name, dir_path=dir_path)
        except Exception as e:
            logger.info(repr(e))
            continue

        filename = export_repo(dir_name=dir_name, dir_path=dir_path, sha1=sha1)
        filepath = f"repos-backup/{filename}"
        excute(cmd=f"rm -rf {dir_path}")
        split_file(dir_name=dir_name, filepath=filepath)

        assert os.path.exists(dir_path) is False, dir_path + " 没有被删除"

        logger.info("repo {dir_name} clone 完毕\n\n".format(dir_name=dir_name))
    return None


def pull_other_branch(dir_name, dir_path):
    branchs, sha1 = match_branch(dir_path=dir_path)
    try:
        os.chdir(dir_path)
    except FileNotFoundError:
        raise Exception(("{dir_path} 文件夹不存在！！请确认 {dir_name} 项目没有删除。"
                         "克隆 {dir_path} 失败\n\n"
                         ).format(dir_path=dir_path, dir_name=dir_name))
    logger.debug("cd 到 repo 文件夹: " + os.getcwd())
    for remote_branch in branchs:
        cmd = ("git branch --track {local_branch} {remote_branch}"
               ).format(local_branch=remote_branch.split("/")[1], remote_branch=remote_branch)
        excute(cmd=cmd)
    excute(cmd="git fetch --all")
    excute(cmd="git pull --all")
    os.chdir("../..")
    logger.debug("已 cd 到主文件夹: " + os.getcwd())
    return sha1


def export_repo(dir_name, dir_path, sha1):
    excute(cmd=f"rm -rf {dir_path}*bundle")
    logger.debug(f"{dir_name} 删除之前的导出包")
    logger.debug(f"开始导出 {dir_path}")
    zone = pytz.timezone("Asia/Shanghai")
    timenow = datetime.now(tz=zone).strftime("%Y-%m-%d_%H.%M")
    filename = f"{dir_name}_@{sha1}_{timenow}.bundle"
    # py_zip_file.main(zip_path=[dir_path], zip_name=name)
    os.chdir(dir_path)
    cmd = f"git bundle create ../{filename} --all"
    excute(cmd=cmd)
    logger.debug(f"{dir_path} 导出完毕")
    os.chdir("../..")
    logger.debug("已 cd 到主文件夹: " + os.getcwd())
    return filename


def split_file(dir_name, filepath):
    logger.debug("导出包大小: {size}".format(size=int(os.path.getsize(filepath) / 1024 / 1024)))
    logger.debug("是否分割: {bool}".format(bool=int(os.path.getsize(filepath) / 1024 / 1024) > 95))
    if int(os.path.getsize(filepath) / 1024 / 1024) > 95:
        zip_dir = filepath + "_bundle"
        os.makedirs(zip_dir)
        cmd = ("split -b 95M -d -a 3 {filepath} {zip_dir}/{dir_name}"
               ).format(filepath=filepath,
                        zip_dir=zip_dir,
                        dir_name=dir_name)
        excute(cmd=cmd)
        logger.debug("导出文件夹下文件:\n" + str(os.listdir(zip_dir)))
        assert bool(os.listdir(zip_dir)) is True, "导出文件夹下没有文件！"
        excute(cmd=f"rm -rf {filepath}")
        assert os.path.exists(filepath) is False, filepath + " 没有被删除"


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
                                "    %(message)s"),
                        datefmt="%H:%M:%S",)
    global logger
    logger = logging.getLogger(__name__)
    level = [logging.INFO, logging.DEBUG][debug]
    logger.setLevel(level)

repo_list = get_repo_list()
create_logger(debug=1)
# repo_list = [(".".join(z.split("/")[-2:]), z) for z in ["https://github.com/Drake-Z/drake-z.github.io"]]
clone_repo(repo_list=repo_list)
