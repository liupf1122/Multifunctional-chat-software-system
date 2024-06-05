import asyncio
import aiofiles
import aiohttp
import time
import re
import os
import shutil
import concurrent.futures
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class NewsCrawler:
    """线程池+异步"""

    def __init__(self):
        self.headers = {
            "User-Agent": UserAgent().random
        }
        self.proxies = {
            'http': f'http://101.89.207.240:16816',
            'https': f'https://101.89.207.240:16816',
        }
        self.base_url = 'https://www.thepaper.cn/'
        self.url_count = 7

    async def get_text(self, session, url, name):
        """获取新闻内容"""
        folder_path = f'./news/{name}'
        if os.path.exists(folder_path):  # 删除旧新闻
            shutil.rmtree(folder_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        print(" 开始爬取：", url)
        async with session.get(url, headers=self.headers, verify_ssl=False) as res:
            html = await res.text()
            print("爬取结果：", url, len(html))
            try:
                p = re.compile(r'<h1.*?">(.*?)</h1>')
                title = p.findall(html)[0]
                soup = BeautifulSoup(html, "html.parser")  # 解析html元素
                body = soup.body  # 获取html的body部分
                text = body.find('div', {'class': 'index_cententWrap__Jv8jK'})  # 获取新闻内容

                news = text.findAll('p', {'class': ''})  # 获取新闻段落
                async with aiofiles.open(f"./news/{name}/{title}.txt", "w", encoding="utf-8") as f:
                    for paragraph in news:  # 获取每段的文本
                        if paragraph.text.strip():  # 检查段落文本是否为空
                            ppp = '    ' + paragraph.text + '\n'
                            await f.write(ppp)
                print('写入成功：', title)
            except Exception as e:
                print("解析出错！", e)

    async def start(self, urls, name):
        """启动爬虫"""
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(self.get_text(session, url, name)) for url in urls]
            for task in tasks:
                # await asyncio.sleep(0.5)  # 添加延迟
                await task
            done, pending = await asyncio.wait(tasks)

    def get_href(self, url, name):
        """获取新闻链接"""
        try:
            print(" 发送请求：", url)
            response = requests.get(url, headers=self.headers)#,proxies=self.proxies
            response.encoding = 'utf-8'  # 设置编码为utf-8，要不然会打印出乱码
            html = response.text
            print("得到结果：", url, len(html))
            p = re.compile(r'newsDetail_forward_\d+')  # 正则表达式找出所有href
            text = p.findall(html)
            href_list = []
            for aa in text:  # 将href变成可访问链接
                href_list.append(self.base_url + aa)
                self.url_count += 1

            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # 防止报错
            asyncio.run(self.start(href_list, name))  # 创建一个新的事件循环并运行异步函数
        except Exception as e:
            print("爬取失败：")
            print(e)
    def main(self):
        """线程池获取链接"""
        folder_path = './news'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)  # 新建文件夹
        news_column_urls = {'时事': 'https://www.thepaper.cn/channel_25950',
                            '国际': 'https://www.thepaper.cn/channel_122908',
                            '财经': 'https://www.thepaper.cn/channel_25951',
                            '科技': 'https://www.thepaper.cn/channel_119908',
                            '智库': 'https://www.thepaper.cn/channel_119489',
                            '思想': 'https://www.thepaper.cn/channel_25952',
                            '生活': 'https://www.thepaper.cn/channel_25953'
                            }
        with concurrent.futures.ThreadPoolExecutor(7) as executor:
            for name, url in news_column_urls.items():
                executor.submit(self.get_href, url, name)


if __name__ == '__main__':
    start_time = time.time()
    crawler = NewsCrawler()
    crawler.main()
    print("本次全部结束")
    print("本次花费时间：", time.time() - start_time)
    print("本次爬取链接个数：", crawler.url_count)
