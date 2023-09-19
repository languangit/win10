#               -*- coding: utf-8 -*-
# @Author  : languang   @Time: 2022/5/28 0028 下午 03:52
# @Software: PyCharm    @FileName: 08_增加了拼接ts.py
"""
恢复简单模式
增加了自动拼接文件
"""
import asyncio
import aiohttp
import os
from tqdm import tqdm
import tools
import urllib3
import re


# from functools import wraps
# from asyncio.proactor_events import _ProactorBasePipeTransport
#
#
# def silence_event_loop_closed(func):
#     @wraps(func)
#     def wrapper(self, *args, **kwargs):
#         try:
#             return func(self, *args, **kwargs)
#         except RuntimeError as e:
#             if str(e) != 'Event loop is closed':
#                 raise
#     return wrapper
#
#
# _ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)


async def download(cs, url, file_dir_name, sem, key=None, total_urls=None):
    """
下载文件，断线重连，
    @param total_urls: 总共需要下载多少个ts文件
    @param cs: aiohttp.ClientSession(timeout=60)
    @param url: 下载文件IP地址URL
    @param file_dir_name: 下载文件的存储位置（包括文件名）
    @param sem: 每次下载在的任务最多个数
    @param key: 如果为加密文件，需要key，默认为None
    """
    global video_list
    async with sem:
        print(f'总共<<<{total_urls}>>>个文件，开始下载{file_dir_name}。。。。。。')
        print(f'url:{url}')
        i = 0
        while True:
            if i != 5:
                c = await tools.download_handler(cs, url, file_dir_name, key)
                if c is not None:
                    video_list[file_dir_name] = c
                    print(f"{file_dir_name}下载成功！")
                    break
                else:
                    i += 1
            else:
                print(f"{file_dir_name}下载失败！")
                break


async def mk_tasks(dict_: dict) -> None:
    """
创建下载任务，等待执行
    @param dict_: 字典，里面应该有key和urls
    """
    sem = asyncio.Semaphore(20)
    urls = dict_.get('urls')
    key = dict_.get('key')
    total_urls = dict_.get('total_urls')
    async with aiohttp.ClientSession() as session:
        tasks = []
        i = 0
        for url in tqdm(urls, desc=f"正在创建下载任务{file_name}："):
            file_dir_name = str(i).rjust(5, "0") + ".mp4"
            task = asyncio.create_task(download(session, url, file_dir_name, sem, key=key, total_urls=total_urls))
            tasks.append(task)
            i += 1
        print('任务创建成功，等待下载！')
        await asyncio.wait(tasks)


def parse(string, domain_, prefix) -> dict:
    """
解析m3u8文件，返回下载文件IP地址列表
    @param domain_: 主机域名
    @param prefix: 主机域名+路径
    @param string: m3u8文件字符串
    @return: 文件下载IP地址列表
    """
    lines = re.split(r'\n', string)
    k = None
    urls = []
    for line in lines:
        url = None
        if line.find("EXT-X-KEY:METHOD=AES-128") > 0:  # 判断是否加密
            if line.find('"') != -1:  # 判断是否有双引号
                key_url = re.split('"', line)[1]  # 使用双引号做切片
                if key_url.startswith('http'):
                    print("key_url = ", key_url)
                    response = tools.getResponse(key_url).content
                    k = response
                elif line.find('/') != -1:
                    key_url = domain_ + key_url
                    print("key_url = ", key_url)
                    response = tools.getResponse(key_url).content
                    k = response
                else:
                    key_url = prefix + key_url
                    print("key_url = ", key_url)
                    response = tools.getResponse(key_url).content
                    k = response
        elif line.startswith('http'):
            url = line
        elif line.endswith('ts'):
            if line.find("/") != -1:
                url = domain_ + line
                
                print(url)

            else:
                url = prefix + line
        if url:
            urls.append(url)
        # if len(urls) > 10:
        #     break
    total_urls = len(urls)
    print(total_urls)
    return {'urls': urls, 'key': k, 'total_urls': total_urls}


def get_domain(url):
    """
    获取m3u8的url域名
    @param url: m3u8的url
    @return: 获取的m3u8的url域名
    """
    
    lst = url.split("/", 3)
    return lst[0] + '//' + lst[2] + '/'


def get_url_prefix(url):
    """
    获取m3u8的URL的前缀，去掉最后的 / 后面的 index.m3u8
    @param url: m3u8的url
    @return: 获取的m3u8的URL的前缀
    """
    
    return url.rsplit('/', 1)[0] + '/'


if __name__ == '__main__':
    video_list = {}
    urllib3.disable_warnings()
    base_url = 'https://vod.hw8.live/m3u8/1ec17902b32225193be9808ef37d7273'
    file_name = '赛琳娜的黄金'
    domain = get_domain(base_url)
    prefix_url = get_url_prefix(base_url)
    print(f'domain--->{domain} ******** prefix_url----> {prefix_url}')
    file_dir = 'd:/'
    all_file_name = f'{file_dir + file_name}.mp4'
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    # all_file_dir = os.path.split(all_file_name)[0]  # 分割路径和文件名,
    # if not os.path.exists(all_file_dir):
    #     os.makedirs(all_file_dir)  # 创建文件存储目录
    # m3u8 = spider_model.get_response(base_url).text
    m3u8 = tools.getResponse(base_url).text
    print(m3u8)
    try:
        # 使程序结束时不出现 RuntimeError: Event loop is closed 异常
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(mk_tasks(parse(m3u8, domain, prefix_url)))
    except ValueError as m:
        print(f'异常处理：Set of coroutines/Futures is empty。 msg信息==>{m}')
        print(r'异常位置I:\python\PythonProject\nunu\单个文件下载09.py第69行。。。')
        print(f'异常文件：None')
        print(f'异常链接：None')
    
    tools.merge_video_files_with_append(video_list, all_file_name)
