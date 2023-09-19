#               -*- coding: utf-8 -*-
# @Author  : languang   @Time: 2022/5/24 0024 下午 03:05
# @Software: PyCharm    @FileName: tools.py

import asyncio
import base64
import json
import os
import re
import time
import aiofile
import aiohttp
import requests
from Crypto.Cipher import AES
from tqdm import tqdm
import sys

# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context


frame = sys._getframe()
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32 "
}


# headers2 = {
#     "user-agent": 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko)'
#                   ' Chrome/109.0.0.0 Mobile Safari/537.36 Edg/109.0.1518.95'
# }


def getResponse(url):
    try:
        return requests.get(url, headers=headers)
    except requests.exceptions.SSLError as e:
        print(f'异常处理：SSLError{e}，一秒钟之后加入下载队列！')
        print(f'异常位置{get_base_path()}第{frame.f_lineno}行。。。')
        print(f'异常文件：Response')
        print(f'异常链接：{url}')
        time.sleep(1)
        getResponse(url)
    except ConnectionError as msg:
        print(f'异常处理：ConnectionError{msg}，一秒钟之后加入下载队列！')
        print(f'异常位置{get_base_path()}第{frame.f_lineno}行。。。')
        print(f'异常文件：Response')
        print(f'异常链接：{url}')
        time.sleep(1)
        getResponse(url)


def get_html(url):
    resp = getResponse(url)
    if resp.status_code in [200, 301, 302]:
        return resp.text
    else:
        print(f'{url}本次访问失败，开始重新开始访问。。。。。。')
        get_html(url)


def getResponseByFile(path):
    with open(path, "r") as f:
        response = f.read()
        return response


def setResponseINFile(path, response):
    with open(path, "w") as f:
        f.write(response)


def b16decode_to_byte(s):
    """
    把16进制数据转为字节数据（8位）
    :param s: 16进制数据
    :return: 字节数据
    """
    s = base64.b16decode(s.upper())
    return s


def get_base_path():
    return f'{os.path.dirname(os.path.abspath(__file__))}'


def get_video2(names: list, file_name: str) -> None:
    """
    把下载的文件追加合并为一个文件，保存，删除缓存
    @param names:需要合并文件的目录文件列表
    @param file_name:合并文件后存储到的目录和名字
    """
    try:
        with open(file_name, 'ab') as f2:  # 以追加方式创建或打开合并后文件的保存位置
            for file in tqdm(names, desc=f"正在合并文件{file_name}："):
                if os.path.exists(file):  # 判断文件是否存在
                    with open(file, 'rb') as f1:  # 以读取二进制文件方式打开文件

                        f2.write(f1.read())  # 追加二进制数据
                    os.remove(file)
                else:
                    print("合并文件需要的元素不存在，未进行合并！")
    except Exception as msg:
        print(f'合并文件失败，msg：{msg}')


def merge_video_files_with_append(video_dict: dict, file_name: str) -> None:
    """
    合并文件，保存，删除缓存， 以追加方式创建或打开合并后文件
    @param video_dict:需要合并文件的字典,字典的key为数字，value为需要合并的每一个文件
    @param file_name:合并文件后存储到的目录和名字
    """
    try:
        names = list(video_dict.keys())
        names.sort()
        # print(names)
        with open(file_name, 'ab') as f:
            for name in tqdm(names, desc=f"正在合并文件{file_name}："):
                f.write(video_dict[name])
            print("下载成功！")
    except Exception as msg:
        print(f'合并文件失败，msg：{msg}')


def merge_file_with_cmd(names: list, file_name: os.path) -> bool:
    """
    合并下载的ts缓存文件， 利用cmd命令将.ts文件合成为mp4格式
    :param names: list 所有缓存文件的目录
    :param file_name: 合并后文件的存放位置目录包括文件名
    """
    try:
        catch_dir = os.path.split(file_name)[0] + '/'  # 分割路径和文件名,
        catch_dir = catch_dir.replace("/", "\\")  # 转换路径分隔符
        file_name = file_name.replace("/", "\\")
        # 利用cmd命令将.ts文件合成为mp4格式
        cmdTask = "copy /b {}*.mp4 {}".format(catch_dir, file_name)
        # completed = subprocess.run(cmdTask, stdout=False)
        # print(completed)
        os.system(cmdTask)
        if os.path.exists(file_name):
            print(f"{catch_dir}里面的ts文件转换{file_name}成功")
            for n in names:
                name = n.replace('/', '\\')
                print(f'正在删除{name}.........')
                try:
                    os.remove(n)
                except FileNotFoundError as msg:
                    print(f'删除文件出现错误！==>{msg}')
            print('缓存文件已全部删除！')
            return True
        else:
            print(f"{catch_dir}里面的ts文件转换{file_name}失败！")
            return False
    except Exception as msg:
        print(f'合并失败，msg：{msg}')
        return False


async def download_handler(cs, url, file_dir_name, key=None):
    try:
        timeOut = aiohttp.ClientTimeout(total=60, sock_connect=60, connect=60, sock_read=60)
        try:
            async with cs.get(url, timeout=timeOut) as resp:
                if resp.status in [200, 301, 302]:
                    try:
                        c = await resp.content.read()
                        if c:
                            if key:
                                print(f"有key：{key}，需要解密，正在解密{file_dir_name}。。。。。。")
                                aes = AES.new(key, mode=AES.MODE_CBC, iv=key)
                                c = aes.decrypt(c)
                                # print(f"{file_dir_name}下载成功！")
                                return c
                            else:
                                # print(f"无需解密，{file_dir_name}下载成功！")
                                return c
                        else:
                            print("没有下载到数据!")
                            print(f'异常位置{os.path.abspath(__file__)}第178行。。。')
                            print(f'异常文件：{file_dir_name}')
                            print(f'异常链接：{url}')
                            return None
                    except aiohttp.ClientPayloadError as clientPayloadError:
                        print(f'异常处理：ClientPayloadError {clientPayloadError}！')
                        print(f'异常位置{os.path.abspath(__file__)}第184行。。。')
                        print(f'异常文件：{file_dir_name}')
                        print(f'异常链接：{url}')
                        return None
                else:
                    print(f'{file_dir_name}下载出错！！！连接不上服务器！！！！')
                    print(f'异常位置{os.path.abspath(__file__)}第190行。。。')
                    print(f'异常文件：{file_dir_name}')
                    print(f'异常链接：{url}')
                    return None
        except aiohttp.ServerDisconnectedError as msg:
            print(f'异常处理：aiohttp.ServerDisconnectedError {msg}！')
            print(f'异常位置{os.path.abspath(__file__)}第196行。。。')
            print(f'异常文件：{file_dir_name}')
            print(f'异常链接：{url}')
            return None
        except aiohttp.ClientConnectorError as msg:
            # print(f'异常处理：aiohttp.ServerDisconnectedError {msg}，链接错误无法下载！')
            print(f'异常处理：aiohttp.ClientConnectorError {msg}！')
            print(f'异常位置{os.path.abspath(__file__)}第203行。。。')
            print(f'异常文件：{file_dir_name}')
            print(f'异常链接：{url}')
            return None
        except aiohttp.ClientOSError as msg:
            print(f'异常处理：aiohttp.ClientOSError {msg}，一秒钟之后加入下载队列！')
            print(f'异常位置{os.path.abspath(__file__)}第209行。。。')
            print(f'异常文件：{file_dir_name}')
            print(f'异常链接：{url}')
            return None
    except asyncio.TimeoutError as msg:  # 此处msg不会输出任何内容
        print(f'异常处理：TimeoutError {msg}，一秒钟之后加入下载队列！')
        print(f'异常位置{os.path.abspath(__file__)}第215行。。。')
        print(f'异常文件：{file_dir_name}')
        print(f'异常链接：{url}')
        return None


async def download(cs, url, file_dir_name, sem, key=None):
    """
下载文件，断线重连，
    @param cs: aiohttp.ClientSession(timeout=60)
    @param url: 下载文件IP地址URL
    @param file_dir_name: 下载文件的存储位置（包括文件名）
    @param sem: 每次下载在的任务最多个数
    @param key: 如果为加密文件，需要key，默认为None
    """
    async with sem:
        print('开始下载。。。。。。')
        print(f'url:{url}')
        print(f'name:{file_dir_name}')
        try:
            timeOut = aiohttp.ClientTimeout(total=60, sock_connect=60, connect=60, sock_read=60)
            try:
                async with cs.get(url, timeout=timeOut) as resp:
                    if resp.status in [200, 301, 302]:
                        try:
                            c = await resp.content.read()
                            async with aiofile.async_open(file_dir_name, 'wb') as f:
                                if c:
                                    if key:
                                        print(f"有key：{key}，需要解密，正在解密{file_dir_name}。。。。。。")
                                        aes = AES.new(key, mode=AES.MODE_CBC, iv=key)
                                        c = aes.decrypt(c)
                                        await f.write(c)
                                        print(f"{file_dir_name}下载成功！")
                                    else:
                                        await f.write(c)
                                        print(f"{file_dir_name}下载成功！")
                                else:
                                    print("没有下载到数据，一秒钟之后重新加入下载队列！")
                                    await asyncio.sleep(1)
                                    await download(cs, url, file_dir_name, sem, key)
                        except aiohttp.ClientPayloadError as clientPayloadError:
                            print(f'异常处理：ClientPayloadError {clientPayloadError}，一秒钟之后重新加入下载队列！')
                            print(f'异常位置：{__file__}第{frame.f_lineno }行。。。')
                            print(f'异常文件：{file_dir_name}')
                            print(f'异常链接：{url}')
                            await asyncio.sleep(1)
                            await download(cs, url, file_dir_name, sem, key)
                    else:
                        print("下载出错，一秒钟之后重新加入下载队列！")
                        await asyncio.sleep(1)
                        await download(cs, url, file_dir_name, sem, key)
            except aiohttp.ServerDisconnectedError as msg:
                print(f'异常处理：aiohttp.ServerDisconnectedError {msg}，一秒钟之后加入下载队列！')
                print(f'异常位置：{__file__}第{frame.f_lineno }行。。。')
                print(f'异常文件：{file_dir_name}')
                print(f'异常链接：{url}')
                await asyncio.sleep(1)
                await download(cs, url, file_dir_name, sem, key)
            except aiohttp.ClientConnectorError as msg:
                print(f'异常处理：aiohttp.ClientConnectorError {msg}，一秒钟之后加入下载队列！')
                print(f'异常位置：{__file__}第{frame.f_lineno }行。。。')
                print(f'异常文件：{file_dir_name}')
                print(f'异常链接：{url}')
                await asyncio.sleep(1)
                await download(cs, url, file_dir_name, sem, key)
            except aiohttp.ClientOSError as msg:
                print(f'异常处理：aiohttp.ClientOSError {msg}，一秒钟之后加入下载队列！')
                print(f'异常位置：{__file__}第{frame.f_lineno }行。。。')
                print(f'异常文件：{file_dir_name}')
                print(f'异常链接：{url}')
                await asyncio.sleep(1)
                await download(cs, url, file_dir_name, sem, key)
        except asyncio.TimeoutError as msg:  # 此处msg不会输出任何内容
            print(f'异常处理：TimeoutError {msg}，一秒钟之后加入下载队列！')
            print(f'异常位置：{__file__}第{frame.f_lineno }行。。。')
            print(f'异常文件：{file_dir_name}')
            print(f'异常链接：{url}')
            await asyncio.sleep(1)
            await download(cs, url, file_dir_name, sem, key)


def dict2json(file_name, pattern, the_dict):
    """
    将字典文件写如到json文件中
    @param file_name: 要写入的数据，dict类型
    @param pattern: 写入文件的方式，追加 a 或者重建 w
    @param the_dict: 要写入的json文件名(需要有.json后缀),str类型
    @return: 1代表写入成功,0代表写入失败
    """
    try:
        json_str = json.dumps(the_dict, indent=4, ensure_ascii=False)
        with open(file_name, pattern) as json_file:
            json_file.write(json_str)
        return 1
    except Exception as msg:
        m = str(msg)
        print(m)
        if '\\' in m:
            print(m.split("'")[4])
            # 'gbk' codec can't encode character '\uc57c' in position 10965: illegal multibyte sequence

        return 0


def del_symbol(str_temp):
    """
    格式化文件名
    :param str_temp: 要格式化的文件名
    :return: 已格式化的文件名
    """
    rstr = r"[\/\\\:\*\?\"\<\>\|.!,' ']"  # '/ \ : * ? " < > |'
    new_str_temp = re.sub(rstr, "_", str_temp)  # 替换为下划线
    return new_str_temp.strip()

