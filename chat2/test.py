import shutil

import requests
from bs4 import BeautifulSoup
import threading
import time
import os


#
# os.environ["http_proxy"] = "http://localhost:7890"
# os.environ["https_proxy"] = "http://localhost:7890"
class GetDailyNews(object):
    def __init__(self):
        """初始化"""
        self.folder_path = './new/'  # 存放新闻路径
        self.news = {'https://www.thepaper.cn/channel_25950': '时事',
                     'https://www.thepaper.cn/channel_122908': '国际',
                     'https://www.thepaper.cn/channel_25951': '财经',
                     'https://www.thepaper.cn/channel_119908': '科技',
                     'https://www.thepaper.cn/channel_119489': '智库',
                     'https://www.thepaper.cn/channel_25952': '思想',
                     'https://www.thepaper.cn/channel_25953': '生活'}

    def get_title(self, url):
        href_list = {}
        """获取新闻链接"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        }  # 伪装成浏览器的请求头
        proxy = {'http': '127.0.0.1:7890', 'https': '127.0.0.1:7890'}  # 设置代理
        try:
            response = requests.get(url, headers=headers, proxies=proxy)  # 对服务器发起get请求
        except:
            response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'  # 设置编码为utf-8，要不然会打印出乱码
        html = response.text  # 获取html元素

        soup = BeautifulSoup(html, "html.parser")  # 解析html元素
        body = soup.body  # 获取html的body部分

        news = body.findAll('a', {'class': 'index_inherit__A1ImK'})
        # print(news)
        time.sleep(1)
        threads = []
        for item in news[1:]:  # 第一个新闻是视频，所以不要
            if item.find('h2') and item.find('img'):
                title = item.find('h2').text
                # print("标题:", title)
                href = "https://www.thepaper.cn/" + item['href']
                # print("链接:", href)
                href_list[title] = href
        return href_list

        # thread = threading.Thread(target=self.get_text, args=(href, title))
        # threads.append(thread)
        # thread.start()

        # for thread in threads:
        #     thread.join()

    def get_text(self, href, title, path):
        """获取链接的内容"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        }  # 伪装成浏览器的请求头
        proxy = {'http': '127.0.0.1:7890', 'https': '127.0.0.1:7890'}  # 设置代理
        try:
            response = requests.get(href, headers=headers, proxies=proxy)  # 对服务器发起get请求
        except:
            response = requests.get(href, headers=headers)
        html = response.text  # 获取html元素

        soup = BeautifulSoup(html, "html.parser")  # 解析html元素
        body = soup.body  # 获取html的body部分
        text = body.find('div', {'class': 'index_cententWrap__Jv8jK'})  # 获取新闻内容
        try:
            news = text.findAll('p', {'class': ''})  # 获取新闻段落
            print('########################################')
            print('标题：', title)
            # 清空txt文件中的内容
            with open(f"{path}/{title}.txt", "w", encoding="utf-8") as f:
                f.close()
            for paragraph in news:  # 获取每段的文本
                ppp = '    ' + paragraph.text + '\n'
                with open(f"{path}/{title}.txt", "a", encoding="utf-8") as f:
                    # print(ppp)
                    f.write(ppp)
                    f.close()
            print('写入成功：', title)
        except:
            print("解析出错！")
        finally:
            time.sleep(1)

    def begin_craw(self, url):
        # 新建文件夹
        folder_path = self.folder_path + self.news[url]
        # if os.path.exists(folder_path):#删除旧新闻
        #     shutil.rmtree(folder_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # 获取接下来要遍历的url列表
        hrefList = self.get_title(url)
        print('遍历列表：', hrefList)
        threads=[]
        for title, href in hrefList.items():
            # self.get_text(href, title, folder_path)
            thread = threading.Thread(target=self.get_text, args=(href, title, folder_path))
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        print("处理完成")

        # with open("news/科技/“夸父一号”卫星新发现100多例太阳白光耀斑.txt", "r", encoding="utf-8") as f:
        #
        #     a=f.read()
        #     print(a)
        #     f.close()

    def main(self):
        news_urls = {'时事': 'https://www.thepaper.cn/channel_25950',
                     '国际': 'https://www.thepaper.cn/channel_122908',
                     '财经': 'https://www.thepaper.cn/channel_25951',
                     '科技': 'https://www.thepaper.cn/channel_119908',
                     '智库': 'https://www.thepaper.cn/channel_119489',
                     '思想': 'https://www.thepaper.cn/channel_25952',
                     '生活': 'https://www.thepaper.cn/channel_25953'}  # 新闻大列表
        start = time.time()
        # threads = []
        # for url in news_urls.values():
        #     thread = threading.Thread(target=self.begin_craw, args=(url,))
        #     threads.append(thread)
        # for thread in threads:
        #     thread.start()
        # for thread in threads:
        #     thread.join()

        for url in news_urls.values():
            self.begin_craw(url)
        end = time.time()

        print("本次新闻处理花费时间为: ", end - start)


if __name__ == '__main__':
    news = {'时事': 'https://www.thepaper.cn/channel_25950',
            '国际': 'https://www.thepaper.cn/channel_122908',
            '财经': 'https://www.thepaper.cn/channel_25951',
            '科技': 'https://www.thepaper.cn/channel_119908',
            '智库': 'https://www.thepaper.cn/channel_119489',
            '思想': 'https://www.thepaper.cn/channel_25952',
            '生活': 'https://www.thepaper.cn/channel_25953'}
    # url = "https://www.thepaper.cn/channel_119908"

    # start = time.time()
    # getDailyNews = GetDailyNews()
    # # for new in news.values():
    # getDailyNews.begin_craw(news['科技'])
    # end = time.time()
    # print("本次新闻处理花费时间为: ", end - start)

    getDailyNews = GetDailyNews()
    getDailyNews.main()
