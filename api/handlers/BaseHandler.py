#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'cheshen'
__date__ = '2017-06-17'


"""
    所有 Handler 的父类
"""

import re

import tornado.web
from tornado import gen

from public.db.data_base import DataBase
from public.model import Page
from public.encoder.commodity_encoder import CommodityEncoder


class BaseHandler(tornado.web.RequestHandler):

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.db = DataBase()
        self.success = {"status": "success", "message": "成功"}
        self.error_message = {"status": "error"}
        self.not_found = {"status": "not_found", "message": "查询商品不存在"}
        self.number = re.compile(r'0|([1-9]\d*)')
        self.float_number = re.compile(r'\d+\.\d+')
        # 防止sql注入的正则
        self.sql_into = re.compile(r'([a-zA-Z0-9\(\)\=])*')
        self.page = Page()
        self.encoder = CommodityEncoder()

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'GET')

    def __reverse_number__(self, count, float_num=False):
        """
        判断是否是数字
        :param count: 需要匹配的字符串
        :return: 
        """
        if count is None:
            return False

        number_str = str(count)

        if float_num:
            result = re.match(self.float_number, number_str)
            if result:
                return float(result.group())
            else:
                return False
        else:
            result = re.match(self.number, number_str)
            if result:
                return int(result.group())
            else:
                return False

    def write_error(self, status_code, **kwargs):
        """
        如果出现异常，自动调用本方法
        :param status_code: 
        :param kwargs: 
        :return: 
        """
        self.error_message["code"] = status_code
        self.write(self.error_message)

    def verification_page_volume(self, page, volume):
        """
        验证分页和排序是否符合当前规则
        :param page: 
        :param volume: 
        :return: 
        """
        page_index = page.page_index
        page_size = page.page_size

        if page_index <= 0 or page_size > 100:
            return False

        if volume not in (0, 1, 2, 3):
            return False

        return True

