#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'cheshen'
__date__ = '2017-06-15'

"""
    管理后台登录界面
"""

import tornado.web
from public.db.commodity_db import CommodityDB


class LoginHandler(tornado.web.RequestHandler):

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.userkey = self.get_argument("userkey", "")
        self.weights = self.get_argument("weights", False)
        self.goods_id = self.get_argument("goods_id", False)
        self.commoditydb = CommodityDB()

    def post(self, *args, **kwargs):
        PASSWORD = "6@!a*Cjd+672P665{aac8.d5bQ(eb#fsS"

        if self.userkey == PASSWORD:
            if self.weights and self.goods_id:
                self.commoditydb.update_weights(self.weights, self.goods_id)
                self.write("success")
                self.finish()
            else:
                self.write("error")
                self.finish()


