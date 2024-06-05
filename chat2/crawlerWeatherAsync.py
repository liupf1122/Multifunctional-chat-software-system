import asyncio
import csv
import json
import random

import aiofiles
import aiohttp
import time
import re
import os
import shutil
import concurrent.futures
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from fake_useragent import UserAgent


class WeatherCrawler:
    def __init__(self):
        self.headers = {
            "User-Agent": UserAgent().random,
            "Connection": "close"
        }
        self.proxies = 'http://36.7.252.231:23536'
        self.base_url = 'http://www.weather.com.cn/weather/'  # +weatherCode+'.shtml'
        self.url_count = 0
        self.PROXY_POOL = []  # 代理IP池

    async def start(self,provinces):
        """启动爬虫"""
        # 加载XML文件
        tree = ET.parse('./cityCode2.xml')
        root = tree.getroot()
        # 定义一个空列表来存储提取的信息
        weather_data = []
        # 遍历XML树
        for province in root.findall('province'):
            province_name = province.attrib['name']
            for city in province.findall('city'):
                city_name = city.attrib['name']
                for county in city.findall('county'):
                    county_name = county.attrib['name']
                    weather_code = county.attrib['weatherCode']
                    # 将提取的信息存储为字典
                    data = {
                        'province_name': province_name,
                        'city_name': city_name,
                        'county_name': county_name,
                        'weather_code': weather_code
                    }
                    # 将字典添加到列表中
                    weather_data.append(data)
        timeout = aiohttp.ClientTimeout(total=600)  # 将超时时间设置为600秒
        connector = aiohttp.TCPConnector(force_close=True, limit=50)  # 将并发数量降低
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(
                self.get_text(session, data['province_name'], data['city_name'], data['county_name'],
                              self.base_url + data['weather_code'] + '.shtml')) for data in weather_data if data['province_name'] == provinces]
            for task in tasks:
                #await asyncio.sleep(random.uniform(1.1, 1.3))  # 添加延迟
                await task
            done, pending = await asyncio.wait(tasks)

    async def get_text(self, session, province, city, county, url):
        """获取天气内容"""
        global proxy
        try:
            self.url_count += 1
            print(" 开始爬取：", url)
            proxy = random.choice(self.PROXY_POOL)  # 从代理IP池中随机选择一个代理IP
            async with session.get(url, headers=self.headers) as res: #, proxy=proxy
                html = await res.text()
                print("爬取结果：", url, len(html))
                await self.parse_text(province, city, county, html)  # 解析网页内容
        except Exception as e:  # 更新代理池
            print("爬取失败：", e)
            self.PROXY_POOL.remove(proxy)
            print("剔除代理：", proxy)
            if not self.PROXY_POOL:
                self.get_ip_port()
                time.sleep(1.1)

    async def parse_text(self, province, city, county, html):
        """解析网页内容"""
        try:
            soup = BeautifulSoup(html, "html.parser")  # 解析html元素
            body = soup.body  # 获取html的body部分
            data = body.find_all('div', {'class': 'left-div'})  # 当日天气数据
            text = data[2].find('script').string  # 获取第三个left-div容器中的json内容
            text = text[text.index('=') + 1:-2]  # 移除var observe24h_data = 将其变为json数据
            jd = json.loads(text)  # 解析json数据为python的字典格式
            day_data = jd['od']['od2']  # 找到当天的数据
            final_data = []  # 存放当天的数据
            count = 0
            for data in reversed(day_data):
                temp = []
                if count <= 24:
                    temp.append(data['od21'])  # 添加时间
                    temp.append(data['od22'])  # 添加当前时刻温度
                    temp.append(data['od24'])  # 添加当前时刻风力方向
                    temp.append(data['od25'])  # 添加当前时刻风级
                    temp.append(data['od26'])  # 添加当前时刻降水量
                    temp.append(data['od27'])  # 添加当前时刻相对湿度
                    temp.append(data['od28'])  # 添加当前时刻空气质量
                    final_data.append(temp)
                    count = count + 1
            print("解析完成:", county)
            await self.write_to_csv(province, city, county, final_data)
        except:
            print('解析失败：', {county})

    async def write_to_csv(self, province, city, county, data):
        """保存为csv文件"""
        folder_path = f'./weather/{province}/{city}/{county}'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        async with aiofiles.open(f'{folder_path}/weather.csv', 'w', encoding='utf-8', errors='ignore', newline='') as f:
            header = ['小时', '温度', '风力方向', '风级', '降水量', '相对湿度', '空气质量']
            f_csv = csv.writer(f)
            await f_csv.writerow(header)
            # await f_csv.writerows(data)
            for row in data:  # 逐行写入
                await f_csv.writerow(row)
        print(f'{county}写入完成')

    def get_ip_port(self):
        # API接口，返回格式为json
        api_url = "http://www.zdopen.com/ExclusiveProxy/GetIP/?api=202405101534495882&akey=4d4784815f626c60&count=20&pro=1&order=2&type=10"
        # API接口返回的ip
        proxy_ip = requests.get(api_url).text
        # print(proxy_ip)
        with open('ip_port.txt', 'w') as f:
            for line in proxy_ip.split('\n'):  # 按行分割
                line = line.strip()  # 去除每行末尾的空白字符
                if line:  # 只写入非空行
                    f.write(line + '\n')
        self.PROXY_POOL.clear()
        with open('ip_port.txt', 'r') as f:
            for line in f.readlines():
                line = line.strip()  # 去除每行末尾的空白字符
                if line:  # 如果行不为空
                    if not line.startswith('http://') and not line.startswith('https://'):
                        line = 'http://' + line  # 如果行不包含协议前缀，则添加
                    self.PROXY_POOL.append(line)
        print("代理池如下：")
        print(self.PROXY_POOL)

    def main(self,provinces):
        folder_path = './weather'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        self.get_ip_port()
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # 防止报错
        asyncio.run(self.start(provinces))  # 创建一个新的事件循环并运行异步函数


if __name__ == '__main__':
    start_time = time.time()
    crawler = WeatherCrawler()
    crawler.main("河南")
    print("本次全部结束")
    print("本次花费时间：", time.time() - start_time)
    print("本次爬取链接个数：", crawler.url_count)
