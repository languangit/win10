#               -*- coding: utf-8 -*-
# @Author  : languang   @Time: 2022/5/28 0028 下午 03:52
# @Software: PyCharm    @FileName: 08_增加了拼接ts.py
"""
恢复简单模式
增加了自动拼接文件
"""
from threading import Thread
import math
import os
import requests
from Crypto.Cipher import AES
from tqdm import tqdm
from spider_helper import spider_model
import tools
import urllib3
import re


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
    return {'urls': urls, 'key': k}


def get_domain(url):
    lst = url.split("/", 3)
    return lst[0] + '//' + lst[2]


def get_url_prefix(url):
    return url.rsplit('/', 1)[0] + '/'


def create_task(url_list: list):
    global all_file_name
    t_download_lst = []
    i = 0
    for urls in url_list:
        file_name = os.path.split(all_file_name)[0] + '/' + str(i) + '.mp4'
        if urls:
            t = DownloadThread(urls, file_name)
            t_download_lst.append(t)
        i += 1
    return t_download_lst


class DownloadThread(Thread):
    def __init__(self, urls, file_name):
        self.urls = urls
        self.file_name = file_name
        super(DownloadThread, self).__init__()
    
    def run(self):
        print(f"正在下载。。。。。。urls:{self.urls}")
        global key
        for url in tqdm(self.urls, desc=f"正在合并文件{self.file_name}："):
            resp = requests.get(url).content
            if resp:
                if key:
                    aes = AES.new(key, mode=AES.MODE_CBC, iv=key)
                    cont = aes.decrypt(resp)
                else:
                    cont = resp
                with open(self.file_name, 'ab') as f:
                    f.write(cont)
            else:
                print(f'下载不成功，URL：{url}')


def main():
    global key
    global all_file_name
    base_url = 'https://ikcdn01.ikzybf.com/20221004/bKXYnl9W/2000kb/hls/index.m3u8'
    file_name = '神话_意大利(1985)'
    domain = get_domain(base_url)
    prefix_url = get_url_prefix(base_url)
    file_dir = f'{tools.get_base_path()}nunu/{file_name}/'
    # all_file_name = f'K:/{file_name}.mp4'
    all_file_name = f'{file_dir + file_name}.mp4'
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    all_file_dir = os.path.split(all_file_name)[0]  # 分割路径和文件名,
    if not os.path.exists(all_file_dir):
        os.makedirs(all_file_dir)  # 创建文件存储目录
    m3u8 = spider_model.get_response(base_url).text
    # print(m3u8)
    dict_ = parse(m3u8, domain, prefix_url)
    key = dict_['key']
    urls = dict_['urls']
    num = len(urls)
    n = math.ceil(num / 20)
    # print(num)
    i = 0
    url_list = []
    for j in range(20):
        l = []
        url_list.append(l)
    q = 0
    for url in urls:
        if i == n:
            i = 0
            q += 1
        if i < n:
            url_list[q].append(url)
            i += 1
    print(len(url_list[q]))
    # print(url_list)
    t_down_lst = create_task(url_list)
    for t_download in t_down_lst:
        t_download.start()
    for t in t_down_lst:
        t.join()


def download(urls, file_name):
    print(f"正在下载。。。。。。urls:{urls}")
    global key
    for url in tqdm(urls, desc=f"正在合并文件{file_name}："):
        resp = requests.get(url).content
        if resp:
            if key:
                aes = AES.new(key, mode=AES.MODE_CBC, iv=key)
                cont = aes.decrypt(resp)
            else:
                cont = resp
            with open(file_name, 'ab') as f:
                f.write(cont)
        else:
            print(f'下载不成功，URL：{url}')


if __name__ == '__main__':
    urllib3.disable_warnings()
    global key
    global all_file_name
    names = []
    main()
