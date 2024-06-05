import asyncio
import csv
import json

import aiofiles
import aiohttp
import time
import re
import os
import shutil
import concurrent.futures
import requests
import threading
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from fake_useragent import UserAgent


class WeatherCrawler:
    def __init__(self):
        self.headers = {
            "User-Agent": UserAgent().random,
            "Connection": "close"
        }
        self.proxies = {
            'http': f'http://101.89.207.240:16816',
            'https': f'https://101.89.207.240:16816',
        }
        self.base_url = 'http://www.weather.com.cn/weather/'  # +weatherCode+'.shtml'
        self.url_count = 0

    def start(self):
        """启动爬虫"""
        # 加载XML文件
        tree = ET.parse('./cityCode.xml')
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
        # threads = []
        # for data in weather_data:
        #     thread = threading.Thread(target=self.get_text,
        #                               args=(data['province_name'], data['city_name'], data['county_name'],
        #                                     self.base_url + data['weather_code'] + '.shtml'))
        #     threads.append(thread)
        # for thread in threads:
        #     thread.start()
        # for thread in threads:
        #     thread.join()

        for data in weather_data:
            self.get_text(data['province_name'], data['city_name'], data['county_name'],
                          self.base_url + data['weather_code'] + '.shtml')

    def get_text(self, province, city, county, url):
        """获取天气内容"""
        try:
            print(" 开始爬取：", url)
            self.url_count += 1
            response = requests.get(url, headers=self.headers)  # 对服务器发起get请求
            response.encoding = 'utf-8'  # 设置编码为utf-8，要不然会打印出乱码
            html = response.text  # 获取html元素
            time.sleep(0.5)
            print("爬取结果：", url, len(html))
            self.parse_text(province, city, county, html)  # 解析网页内容
        except Exception as e:  # 更新代理池
            print("爬取失败：", e)

    def parse_text(self, province, city, county, html):
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
            self.write_to_csv(province, city, county, final_data)
        except Exception as e:
            print('解析失败：', {county}, e)

    def write_to_csv(self, province, city, county, data):
        """保存为csv文件"""
        folder_path = f'./weather/{province}/{city}/{county}'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        with open(f'{folder_path}/weather.csv', 'w', encoding='utf-8', errors='ignore', newline='') as f:
            header = ['小时', '温度', '风力方向', '风级', '降水量', '相对湿度', '空气质量']
            f_csv = csv.writer(f)
            f_csv.writerow(header)
            f_csv.writerows(data)
        print(f'{county}写入完成')

    def main(self):
        folder_path = './weather'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        self.start()  # 启动函数


if __name__ == '__main__':
    start_time = time.time()
    crawler = WeatherCrawler()
    crawler.main()
    print("本次全部结束")
    print("本次花费时间：", time.time() - start_time)
    print("本次爬取链接个数：", crawler.url_count)
