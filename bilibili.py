#!/user/bin/env python
# -*- coding:utf-8 -*-

from config import *
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
import re,time


USER = [USERNAME]
PASSWD = [PASSWD]

class CrackBiliBili():
    def __init__(self):
        self.broswer = webdriver.Chrome()
        self.url = 'https://passport.bilibili.com/login'
        self.wait = WebDriverWait(self.broswer,10)
        self.user = USER
        self.passwd = PASSWD
        self.BORDER = 6

    def open(self):
        '''
        账号登录
        :return:
        '''
        self.broswer.get(self.url)
        self.broswer.maximize_window()
        username = self.wait.until(EC.presence_of_element_located((By.ID,'login-username')))
        #username.clear()
        passwd = self.wait.until(EC.presence_of_element_located((By.ID,'login-passwd')))
        #passwd.clear()
        submit = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME,'gt_slider'))) #获元素取点击按钮
        username.send_keys(self.user)
        passwd.send_keys(self.passwd)
        submit.click()  #模拟点击

    def get_images(self, bg_filename='bg.jpg', fullbg_filename='fullbg.jpg'):
        """
        获取验证码图片
        :return: 图片的location信息
        bg: 带缺口背景图
        fullgb： 不带缺口背景图
        B站登录验证码为异步加载，还可以通过抓取图片来获取
        """
        bg = []
        fullgb = []
        while bg == [] and fullgb == []:
            bf = BeautifulSoup(self.broswer.page_source, 'lxml')
            bg = bf.find_all('div', class_='gt_cut_bg_slice')
            fullgb = bf.find_all('div', class_='gt_cut_fullbg_slice')
        bg_url = re.findall('url\(\"(.*)\"\);', bg[0].get('style'))[0].replace('webp', 'jpg')  #获取带缺口的验证码图片
        fullgb_url = re.findall('url\(\"(.*)\"\);', fullgb[0].get('style'))[0].replace('webp', 'jpg') # 获取原始验证码图片
        bg_location_list = []
        fullbg_location_list = []
        for each_bg in bg:
            location = {}
            location['x'] = int(re.findall('background-position: (.*)px (.*)px;', each_bg.get('style'))[0][0])  #[('-157', '-58')] 取出-157
            location['y'] = int(re.findall('background-position: (.*)px (.*)px;', each_bg.get('style'))[0][1]) #[('-157', '-58')]  取出-58
            bg_location_list.append(location)    #{'x': -145, 'y': -58}]{'x': -265, 'y': -58}]
        for each_fullgb in fullgb:
            location = {}
            location['x'] = int(re.findall('background-position: (.*)px (.*)px;', each_fullgb.get('style'))[0][0])
            location['y'] = int(re.findall('background-position: (.*)px (.*)px;', each_fullgb.get('style'))[0][1])
            fullbg_location_list.append(location)
        urlretrieve(url=bg_url, filename=bg_filename)   #将URL检索到磁盘上的临时位置。 即保存乱序图片到本地
        print('缺口图片下载完成')
        urlretrieve(url=fullgb_url, filename=fullbg_filename)
        print('背景图片下载完成')
        return bg_location_list, fullbg_location_list

    def get_merge_image(self, filename, location_list):
        """
        根据位置对图片进行合并还原
        :filename:图片
        :location_list:图片位置
        思路：将乱序图片中对应像素坐标的图片块，按照源代码中采集到的坐标顺序，组合到正确图片的对应位置
        """
        im = Image.open(filename)   #打开原始图
        im_list_upper = []                #上半部图片
        im_list_down = []                 #下半部图片
        for location in location_list:
            if location['y'] == -58:
                im_list_upper.append(im.crop((abs(location['x']), 58, abs(location['x']) + 10, 116)))   ##从此图像返回一个矩形区域。 盒子是一个4元组定义左，上，右和下像素坐标。
                                       # crop函数带的参数为(起始点的横坐标，起始点的纵坐标，宽度，高度）
            if location['y'] == 0:
                im_list_down.append(im.crop((abs(location['x']), 0, abs(location['x']) + 10, 58)))  #左，上，右，下
        new_im = Image.new('RGB', (260, 116))   #设定一个空白图片 大小
        x_offset = 0
        for im in im_list_upper:             #注意此处原图是上下两部分相反排布
            new_im.paste(im, (x_offset, 0))  #paste函数的参数为(需要修改的图片， (粘贴的起始点的横坐标，粘贴的起始点的纵坐标)   ）
            x_offset += im.size[0]
        x_offset = 0
        for im in im_list_down:
            new_im.paste(im, (x_offset, 58))
            x_offset += im.size[0]
        new_im.save(filename)
        return new_im

    def get_slider(self):
        """
        “点击按钮进行验证”获取滑块
        :return: 滑块对象
        """
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'gt_slider_knob')))
        return slider

    def get_gap(self, img1, img2):
        """
        获取缺口偏移量
        :param img1: 不带缺口图片
        :param img2: 带缺口图片
        :return:
        """
        left = 43          #阴影缺口出现距边框最小位置 x轴距离
        for i in range(left, img1.size[0]):
            for j in range(img1.size[1]):
                if not self.is_pixel_equal(img1, img2, i, j):
                    left = i
                    return left
        return left
    def is_pixel_equal(self, img1, img2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pix1 = img1.load()[x, y]
        pix2 = img2.load()[x, y]
        threshold = 60
        if (abs(pix1[0] - pix2[0] < threshold) and abs(pix1[1] - pix2[1] < threshold) and abs(
                pix1[2] - pix2[2] < threshold)):
            return True
        else:
            return False

    def get_track(self,distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        track = []                       #移动轨迹
        current = 0                      #当前位移
        mid = distance * 4 / 5           #减速阈值
        t = 0.2                          #计算间隔
        v = 0                            #初速度
        while current < distance:
            if current <mid:
                a = 2                     #加速度1
            else:
                a = -3                    #加速度2
            v0 = v
            v = v0 + a * t
            move = v0 * t +1/2 * a * t * t #位移
            current += move
            track.append(round(move))      #结果取整
        return track

    def move_to_gap(self,slider,track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.broswer).click_and_hold(slider).perform()  #模拟点击鼠标左键
        for x in track:
            ActionChains(self.broswer).move_by_offset(xoffset=x,yoffset=0).perform()  #移动鼠标从当前位置到 （x，y） 坐标
        time.sleep(0.5)
        ActionChains(self.broswer).release().perform()  #释放以上的action操作

    def crack(self):
        try:
            print('正在尝试登录...')
            self.open()
            bg_filename = 'bg.jpg'
            full_filename = 'fullbg.jpg'
            bg_location_list, fullbg_location_list = self.get_images(bg_filename,full_filename)  #获取乱序的小图
            bg_img = self.get_merge_image(bg_filename,bg_location_list)                          #还原成带缺口图片
            fullbg_img = self.get_merge_image(full_filename,fullbg_location_list)                #还原成原始图片
            slider = self.get_slider()                   #获取 ||| 按钮
            gap = self.get_gap(fullbg_img, bg_img)       #获取偏移量
            print('缺口位置', gap)
            gap -= self.BORDER                           #减去边框宽度
            track = self.get_track(gap)                  #模拟运动轨迹
            self.move_to_gap(slider, track)              #移动滑块
            print('登陆成功')
        except TimeoutException:
            self.crack()


if __name__ == '__main__':
    crack = CrackBiliBili()
    crack.crack()