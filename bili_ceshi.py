#!/user/bin/env python
# -*- coding:utf-8 -*-
import time

from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from config import *

EMAIL = [USERNAME]
PASSWD = [PASSWD]
BORDER = 6      #移动滑块距边框距离
class CrackGeetest():
    def __init__(self):
        self.url = 'https://passport.bilibili.com/login'
        self.broswer = webdriver.Chrome()
        self.wait = WebDriverWait(self.broswer,10)
        self.email = EMAIL
        self.passwd = PASSWD

    def open(self):
        """
        打开网页输入用户名密码
        :return: None
        """
        self.broswer.get(self.url)
        self.broswer.find_element_by_id('login-username').clear()
        self.broswer.find_element_by_id('login-username').send_keys(self.email)
        self.broswer.find_element_by_id('login-passwd').clear()
        self.broswer.find_element_by_id('login-passwd').send_keys(self.passwd)

    def get_gap(self,image_1,image_2):
        """
        获取缺口的偏移量
        """
        left= 60
        for i in range(left,image_1.size[0]):  #size[0] 横坐标
            for j in range(image_1.size[1]):   #size[1] 纵坐标
                if not self.is_pixel_equal(image_1,image_2,i,j):   #RGB值 不 小于60
                    left = i
                    return left     #注意return的位置
        return left

    def is_pixel_equal(self,image_1,image_2,x,y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pixel_1 = image_1.load()[x,y]          #获取该点处的RGB值  如：(117, 201, 249)
        pixel_2 = image_2.load()[x,y]
        threshold = 60                         #阈值设置为60
        if abs(pixel_1[0] - pixel_2[0]) < threshold and abs(pixel_1[1] - pixel_2[1]) < threshold and abs(
                pixel_1[2] - pixel_2[2]) < threshold:          #R G B 三个值相比较
            return True                      #绝对值小于60
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

    def click_slider(self):
        """
        模拟点击 滑块 按钮
        :return:
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'gt_guide_tip ')))
        ActionChains(self.broswer).click_and_hold(button).perform()  # 模拟点击鼠标左键不放

    def click_button(self):
        """
        模拟点击 ||| 按钮
        :return:
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'gt_slider_knob ')))
        ActionChains(self.broswer).click_and_hold(button).perform()  # 模拟点击鼠标左键不放

    def get_position_bg(self,image):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME,image)))
        location = img.location  #获取图片截图位置
        size = img.size          #获取图片大小
        top, bottom, left, right = location['y'], location['y']+size['height'], location['x'], location['x']+size['width']
        return (top, bottom,left,right)

    def get_slider(self):
        """
        “点击按钮进行验证”获取滑块
        :return: 滑块对象
        """
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'gt_slider_knob')))
        return slider

    def get_geetest_image(self,image_className, name='captcha.png'):
        """
        获取验证码截图
        :param name:
        :return:
        """
        top,bottom,left,right = self.get_position_bg(image_className)
        print('验证码位置',top,bottom,left,right)
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left,top,right,bottom))  #从此图像返回一个矩形区域。 盒子是一个4元组定义左，上，右和下像素坐标。
        captcha.save(name)
        return captcha

    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.broswer.get_screenshot_as_png()   #Gets the screenshot of the current window as a binary data.
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot

    def crack(self):
        try:
            self.open()                         #输入用户名、密码
            self.click_slider()                 #点击滑块栏，使初始验证码图片出现
            imagebg = 'gt_cut_bg'
            image_1 = self.get_geetest_image(imagebg, 'captcha1.png') #获取第一张验证码图片  ,默认参数只能放在参数列表的最后边
            time.sleep(1)
            slider = self.click_button()   # 点击滑块按钮，使带缺口验证码出现
            imagefullbg = 'gt_cut_bg'
            image_2 = self.get_geetest_image(imagefullbg,'captcha2.png') #获取第二张带缺口验证码图片
            time.sleep(1)
            gap = self.get_gap(image_1 , image_2) #获取拼图移动的距离
            print('缺口位置：',gap)
            gap -= BORDER                       ##减去移动滑块距边框的距离
            track = self.get_track(gap)         #为使模拟真实操作，多移动速度做处理
            print('滑动轨迹',track)
            self.move_to_gap(slider,track)      #移动滑块
        except TimeoutException:
            return self.crack()                #失败，执行迭代


if __name__ == '__main__':
    crack = CrackGeetest()
    crack.crack()