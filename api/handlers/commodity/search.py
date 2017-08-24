#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'cheshen'
__date__ = '2017-06-11'

"""
    查询商品的API
"""

import json
import re
from datetime import datetime
from decimal import Decimal
from collections import Counter

import jieba
import tornado.web
from tornado import gen

from public.db.search_db import SearchDB
from public.model import Page
from utils.search import chinese_to_number, splicing_path
from utils import os_path
from public.encoder.commodity_encoder import CommodityEncoder
from api.handlers.BaseHandler import BaseHandler


class SearchHandler(BaseHandler):
    def data_received(self, chunk):
        pass

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.search_db = SearchDB()

    def get(self, *args, **kwargs):
        name = self.get_argument('name', '')
        # 替换所有的空格
        name = name.replace(' ', '')
        self.page.page_index = self.__reverse_number__(self.get_argument('page_index', 1))
        self.page.page_size = self.__reverse_number__(self.get_argument('page_size', 50))
        volume = self.__reverse_number__(self.get_argument('volume', 0))

        self.page.page_count = 0
        self.page.total = 0

        if self.verification_page_volume(self.page, volume):
            start_index = self.page.page_index * self.page.page_size
            end_index = start_index + self.page.page_size
            if name:
                result = self.split_name(name)
                if result:
                    ids = list()
                    for r in result:
                        codes = chinese_to_number(r)
                        if codes[0]:
                            files = splicing_path(codes[1])
                            file_list = os_path.read_file_to_search(files.get('file_path'))
                            if file_list:
                                ids += file_list
                    if ids:
                        store_ids = Counter(ids)
                        # 获得记录总数
                        self.page.total = len(store_ids)

                        # 得到总页数
                        self.page.page_count = int(self.page.total / self.page.page_size)

                        # 最后一页可能除不尽
                        if self.page.page_count > 0:
                            if self.page.page_count > int(self.page.page_count):
                                # 说明除不尽，应该还有一页
                                self.page.page_count = int(self.page.page_count) + 1
                            else:
                                self.page.page_count = int(self.page.page_count)

                        total_ids = store_ids.most_common(self.page.total)
                        # 0, 50 | 50, 100
                        select_ids = total_ids[start_index:end_index]

                        sid = ""
                        for si in select_ids:
                            sid = sid + si[0] + ','
                        if sid:
                            sid = sid[:-1]
                            self.success['data'] = self.search_db.find_commoditys_by_ids(sid, volume)
                            page = {
                                'page_size': self.page.page_size,
                                'page_index': self.page.page_index,
                                'page_count': self.page.page_count,
                                'total': self.page.total
                            }
                            self.success['page'] = page
                            self.write(self.encoder.encode(self.success))
                        else:
                            self.write(self.not_found)
                    else:
                        self.write(self.not_found)
                else:
                    self.write(self.error_message)
            else:
                self.write(self.error_message)
        else:
            self.write(self.error_message)

    def split_name(self, name):
        """
        把搜索的条件拆分
        :param name: 
        :return: 
        """
        name = jieba.lcut_for_search(name)
        return name
