#! python3
# -*- coding: utf-8 -*-
# @Author: Drake-Z
# @Date:   2017-10-10 16:51:33
# @Last Modified time: 2017-11-17 15:26:56

"""
py-zip-file 压缩指定文件/目录到指定目录。
"""
import os
import zipfile


def get_zip_list(path_list):
    """
    输入待压缩路径列表，输出待压缩路径和相对压缩路径配对列表
    TODO: 对路径的合法性判断，需要重写一个函数。
    :param path_list:   待压缩路径列表
    :return:            路径配对列表
    """
    assert isinstance(path_list, list)
    zip_list = []
    for filepath in path_list:
        zip_list += zip_prepare(path=filepath)
    return zip_list


def zip_prepare(path):
    """
    输入待压缩路径，输出待压缩路径和相对压缩路径配对列表
    :param path_list:   待压缩路径
    :return:            路径配对列表
    """
    zip_list = []
    # - 1 是为了 relative_path 开头保持 X\\folder，可以使文件夹在 zipfile 里为一个文件夹，如果单为 \\folder 的话压缩文件有问题
    relative = len(os.path.dirname(path)) - 1
    if os.path.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                # 截取相对路径
                relative_path = filepath[relative:]
                # 在文件路径前面加上 \\?\ 可以处理路径名过长的问题
                zip_list.append(["\\\\?\\" + z for z in (filepath, relative_path)])
    else:
        relative_path = path[relative:].strip(os.path.sep)
        zip_list.append(["\\\\?\\" + z for z in (path, relative_path)])
    return zip_list


def zip_write(zip_list, output_path):
    """
    输入路径配对列表（[(filepath, relatpath), ...]）压缩对应文件输出到指定路径中
    :param zip_list:    待压缩文件/目录路径列表
    :param output_path: 压缩文件输出路径
    """
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as f:
        for files in zip_list:
            f.write(*files)


def main(zip_path, zip_name):
    """
    输入待压缩路径、输出路径、压缩文件名，执行压缩工作
    :param zip_path:    待压缩路径
    :param output_dir:  输出路径
    :param zip_name:    压缩文件名
    """

    zip_list = get_zip_list(path_list=zip_path)
    zip_write(zip_list=zip_list,
              output_path=zip_name + ".zip")
