#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'cheshen'
__date__ = '2017-05-13'

import tornado.ioloop
import tornado.web
from public import log
from api.handlers.commodity.commodity import CommodityHandler
from api.handlers.commodity.search import SearchHandler
from api.handlers.commodity.taobao import TaobaoHandler
from api.handlers.admin.user import LoginHandler


def make_app():
    return tornado.web.Application(
        [
            # 商品相关
            (r"/api/commodity", CommodityHandler),

            # 搜索商品
            (r"/api/search", SearchHandler),

            # 淘宝API
            (r"/api/taobao", TaobaoHandler),

            # 后台管理
            (r"/api/user", LoginHandler)
        ])


def start_web():
    app = make_app()
    app.listen(8808)
    log.logging.info('Start tornado with: http://127.0.0.1:8888')
    tornado.ioloop.IOLoop.current().start()


