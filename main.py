#! /usr/local/bin/python3
# coding: utf-8
# __author__ = "Brady Hu"
# __date__ = 2017/10/16 16:11

from selenium import webdriver
import requests
import json
import time
import os
import settings
import transCoordinateSystem
import sys
import math

i = 1
qq_number_sides = 0
point_total = 0
spyder_list = []
file_output = open('C://Users//James//Desktop//stations_people.csv','w')

#创建一个异常类，用于在cookie失效时抛出异常
class CookieException(Exception):
    def __init__(self):
        Exception.__init__(self)

def main():
    """爬虫主程序，负责控制时间抓取"""
    while True:
        global i
        global qq_number_sides
        global point_total
        global spyder_list

        cookie = get_cookie(qq_number_sides)
        for item in spyder_list:
            
            print("此轮抓取开始")
            """这部分负责每个qq号码抓取的次数"""
            if i% settings.fre == 0:
                cookie = get_cookie(qq_number_sides)
                qq_number_sides += 1
                print("换号了")

            place = item[0]
            print(place)
            params = spyder_params(item)
            time_now = time.time()
            time_now_str = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time_now))
            path_file = 'C://Users//James//Desktop//data//'
            
            try:
                text = spyder(cookie, params)
                save(text, time_now_str, file_name= path_file + place + time_now_str+".csv")
            except CookieException as e:
                print("CookieExcepton启动")
                cookie = get_cookie(qq_number_sides)
                qq_number_sides += 1
                text = spyder(cookie, params)
                save(text, time_now_str, file_name= path_file + place + time_now_str+".csv")
            i+=1
            print("此轮抓取完成")
            file_output.write(place+','+str(point_total)+','+time_now_str+'\n')
            point_total = 0
        break


def get_cookie(num):
    """负责跟据传入的qq号位次，获得对应的cookie并返回，以便用于爬虫"""
    chromedriver = r'C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe'
    os.environ["webdriver.chrme.driver"] = chromedriver
    chrome_login = webdriver.Chrome(chromedriver)
    chrome_login.get(
        "http://c.easygo.qq.com/eg_toc/map.html?origin=csfw&cityid=110000")
    chrome_login.find_element_by_id("u").send_keys(settings.qq_list[num][0])
    chrome_login.find_element_by_id("p").send_keys(settings.qq_list[num][1])
    chrome_login.maximize_window()
    chrome_login.find_element_by_id("go").click()
    time.sleep(20)
    cookies = chrome_login.get_cookies()
    chrome_login.quit()
    user_cookie = {}
    for cookie in cookies:
        user_cookie[cookie["name"]] = cookie["value"]

    return user_cookie


def spyder(user_cookie, params):
    """根据传入的表单，利用cookie抓取宜出行后台数据"""
    user_header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Referer": "http://c.easygo.qq.com/eg_toc/map.html?origin=csfw"
    }
    url = "http://c.easygo.qq.com/api/egc/heatmapdata"
    while True:
        try:
            r = requests.get(url, headers=user_header,
                             cookies=user_cookie, params=params)
            if r.status_code == 200:
                return r.text
        except Exception as e:
            print(e.args)
        break

def spyder_params(item):
    """将传入的块转化为网页所需的表单"""
    station,lng_mini,lng_maxi,lat_mini,lat_maxi = item
    lng_mini,lat_mini = transCoordinateSystem.wgs84_to_gcj02(lng_mini,lat_mini)
    lng_maxi,lat_maxi = transCoordinateSystem.wgs84_to_gcj02(lng_maxi,lat_maxi)
    lng = (lng_mini+lng_maxi)*0.5
    lat = (lat_mini+lat_maxi)*0.5
    params = {"lng_min": lng_mini,
                "lat_max": lat_maxi,
                "lng_max": lng_maxi,
                "lat_min": lat_mini,
                "level": 16,
                "city": "%E6%88%90%E9%83%BD",
                "lat": lat,
                "lng": lng,
                "_token": ""}
    return params

def save(text, time_now,file_name):
    """将抓取下来的流数据处理保存到文本文件"""
    global point_total
    
    #判断文件是否存在，若不存在则创建文件并写入头
    try:
        with open(file_name,'r') as f:
            f.readline()
    except FileNotFoundError as e:
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write('count,wgs_lng,wgs_lat,time\n')
    #写入数据
    with open(file_name, "a", encoding="utf-8") as f:
        node_list = json.loads(text)["data"]
        try:
            min_count = node_list[0]["count"]
            for i in node_list:
                min_count = min(i['count'],min_count)
            for i in node_list:
                i['count'] = i['count']/min_count
                gcj_lng = 1e-6 * (250.0 * i['grid_x'] + 125.0) #此处的算法在宜出行网页后台的js可以找到，文件路径是http://c.easygo.qq.com/eg_toc/js/map-55f0ea7694.bundle.js
                gcj_lat = 1e-6 * (250.0 * i['grid_y'] + 125.0)
                lng, lat = transCoordinateSystem.gcj02_to_wgs84(gcj_lng, gcj_lat)
                point_total += i['count']
                f.write(str(i['count'])+","+str(lng)+","+str(lat)+","+time_now+"\n")
        except IndexError as e:
            pass
            # print("此区域没有点信息")
        except TypeError as e:
            print(node_list)
            raise CookieException

if __name__ == "__main__":
    path = 'C://Users//James//Desktop//stations_wgs.csv'
    file_input = open(path)
    file_output.write('站名,相对人数,时间\n')
    for line in file_input:
        line = line.strip()
        line = line.split(',')
        if (line[0] == '') or (line[1] =='') or (line[2] ==''):
            continue
        
        #中心经纬度，站点名称
        delta = math.pi*2*6371/360
        lng_center = float(line[1])
        lat_center = float(line[2])
        lng_range = 0.5/(delta*math.cos(lat_center/180*math.pi))
        lat_range = 0.5/delta

        #四至，城市
        lng_min = lng_center - lng_range
        lat_max = lat_center + lat_range
        lng_max = lng_center + lng_range
        lat_min = lat_center - lat_range

        #获取spyder_list
        spyder_list.append([line[0],round(lng_min,5),round(lng_max,5),round(lat_min,5),round(lat_max,5)])
    main()
    file_input.close()
file_output.close()
