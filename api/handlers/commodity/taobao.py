#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'cheshen'
__date__ = '2017-06-27'

"""
    淘宝相关API
"""

import re
import json
from tornado import gen
from api.handlers.BaseHandler import BaseHandler
from public.ali_sdk import taobao_wireless_share_tpwd_create
from public.settings import TAO_BAO_URL, PID, NOWAKE


class TaobaoHandler(BaseHandler):
    def data_received(self, chunk):
        pass

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    @gen.coroutine
    def get(self, *args, **kwargs):
        api_type = self.get_argument("api_type", False)
        if not api_type:
            self.write(self.error_message)
            return

        if api_type == "taobao.wireless.share.tpwd.create":
            item_id = self.get_argument("itemId", False)
            activity_id = self.get_argument("activityId", False)
            text = self.get_argument("text", False)
            url = TAO_BAO_URL.format(item_id=item_id, activity_id=activity_id, pid=PID, nowake=NOWAKE)
            if not item_id or not activity_id or not text:
                self.write(self.error_message)
                return

            tpwd_param = json.dumps({
                "url": url,
                "text": text
            })
            result = taobao_wireless_share_tpwd_create(tpwd_param)
            if result:
                self.success['data'] = result
                self.write(self.success)
            else:
                self.error_message["message"] = "错误的请求参数"
                self.write(self.error_message)
