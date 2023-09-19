#               -*- coding: utf-8 -*-
# @Author  : languang   @Time: 2022/5/28 0028 下午 03:52
# @Software: PyCharm    @FileName: 08_增加了拼接ts.py
"""
恢复简单模式
增加了自动拼接文件
自动下载电视剧
"""
import asyncio
import aiohttp
import os
import tools
import urllib3
import re
from bs4 import BeautifulSoup


async def mk_tasks(base_path: str, urls: list) -> None:
    """
创建下载任务，等待执行
    @param base_path:
    @param urls:
    """
    sem = asyncio.Semaphore(20)
    global names
    global page
    tasks = []
    i = 0
    conn = aiohttp.TCPConnector(ssl=False)  # 防止ssl报错
    # timeOut = aiohttp.ClientTimeout(total=60, sock_connect=60, connect=60, sock_read=60)    # 设置timeout
    async with aiohttp.ClientSession(connector=conn) as cs:
        for url in urls:
            file_name = base_path + str(page) + str(i).rjust(5, "0") + ".mp4"
            if os.path.exists(file_name):
                print(f'文件{file_name}已存在，无需下载！')
            else:
                task = asyncio.create_task(tools.download(cs, url, file_name, sem))
                tasks.append(task)
            names.append(file_name)
            i += 1
        await asyncio.wait(tasks)
        # done, pending = await asyncio.wait(tasks)
        # all_result = [done_task.result()for done_task in done]
        # print(all_result)


def parse(string, ts_prefix) -> list:
    """
解析m3u8文件，返回下载文件IP地址列表
    @param ts_prefix: m3u8内的URL的前缀
    @param string: m3u8文件字符串
    @return: 文件下载IP地址列表
    """
    lines = re.split(r'\n', string)
    urls = []
    for line in lines:
        # print(f"=============>{prefix + line}")
        if line.endswith('.ts'):
            urls.append(ts_prefix + line)
            # print(f"=============>{prefix + line}")
    return urls


def get_m3u8_url_1(url):
    """
访问给定集数页面url，取出里面的m3u8文件下载地址，返回
    @param url: 集数页面url
    @return: m3u8IP地址URL
    """
    html = tools.get_html(url)
    soup = BeautifulSoup(html, 'lxml')  # 创建BeautifulSoup对象
    div = soup.find('div', class_="playbox bofang")  # 找到URL所在的div
    script = div.find('script').text  # 取出 div下一个节点的text值
    dict_ = eval(re.split('=', script)[1])  # 取出值中的字典类型内容，还原为字典
    return dict_.get('url_next').replace('\\', '')  # 返回字典内的高清URL


if __name__ == '__main__':
    urllib3.disable_warnings()  # 去除警告类信息
    file_dir = f'{tools.get_base_path()}nunu/媳妇的catch/'  # 定义好下载的ts文件的缓存位置
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)  # 创建文件存储目录
    for page in range(36, 37):
        names = []  # 用来存储所有下载的ts文件的名字
        u = f'https://sarhotline.org/vodplay/83277-1-{page}.html'  # 循环得到集数页面URL
        # names = os.listdir(file_dir)
        all_file_name = f'K:/媳妇的美好时代/媳妇的美好时代{page}.mp4'  # 定义好拼接好的视频文件的存储位置，
        all_file_dir = os.path.split(all_file_name)[0]  # 分割路径的路径名和文件名
        if not os.path.exists(all_file_dir):
            os.makedirs(all_file_dir)  # 创建文件存储目录
        print(f"准备完毕，开始获取第{page}集m3u8，正在访问({u})。。。。。")
        m3u8_url_1 = get_m3u8_url_1(u)  # 得到m3u8第一个URL
        print(f'得到第{page}集m3u8第一个URL,正在访问({m3u8_url_1})。。。。。')
        
        # m3u8_url_1 = 'https://www.taopianplay.com/taopian/54fdb532-e89b-4567-bc07-aa93a0c6a79b/a891bf2e-a823-4ae0-ac07-107cdf1703d8/2714/2a15ade4-18fd-4b6a-8fc6-9a449f368e84/SD/playlist.m3u8'
        
        prefix = re.split('playlist', m3u8_url_1)[0]  # 切割URL，取出前缀
        m3u8 = tools.get_html(m3u8_url_1)  # 得到m3u8的内容
        print(f'得到第{page}集m3u8内容,开始解析并下载。。。。。')
        try:
            asyncio.run(mk_tasks(file_dir, parse(m3u8, prefix)))  # 解析m3u8并创建下载任务列表，循环执行下载任务
        except ValueError as msg:
            print(f'异常处理：Set of coroutines/Futures is empty.一秒钟之后加入下载队列！msg:{msg}')
            print(r'异常位置I:\python\PythonProject\nunu\10_页面抓取全部集数下载地址.py第103行。。。')
            print(f'异常文件：None')
            print(f'异常链接：None')
        print(f'第{page}集下载完成，开始合并！')
        tools.merge_video_files(names, all_file_name)  # 任务完成后合并文件
        for name in names:
            os.remove(name)  # 清除缓存文件
        print(f"缓存文件删除成功！开始缓存第{page + 1}集")
        
        # print('文件合并成功，是否删除缓存文件，是按e + enter，否按其他键 + enter')
        # e = input()
        # if e == 'e':
        #     for name in names:
        #         os.remove(name)
        #     if os.listdir(file_dir) is None:
        #         print("缓存文件删除成功！")
