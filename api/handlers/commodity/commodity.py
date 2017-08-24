#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'cheshen'
__date__ = '2017-05-14'

"""
    商品相关的API接口
"""

import re
from tornado import gen
from api.handlers.BaseHandler import BaseHandler


class CommodityHandler(BaseHandler):
    def data_received(self, chunk):
        pass

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        # 查询SQL
        self.sql = """
          select
            id,
            activity_id,
            item_id,
            shop_name,
            shop_type,
            image,
            price,
            coupon,
            reserve_price,
            volume,
            site_type,
            post_free,
            end_time
        from commodity where 1=1
    """

    @gen.coroutine
    def get(self):
        # 按销量查询
        """
        :volume
        0：默认排序
        1：销量从高到低排序
        2：按优惠率从高到低排序
        3：按价格从低到高排序
        """
        volume = self.get_argument('volume', 0)
        # 按照价格范围查询
        price_range = self.get_argument('price_range', None)
        # 按有效期查询
        valid_period = self.get_argument('valid_period', False)
        # 按分类查询
        shop_type = self.get_argument('shop_type', False)
        # 是否包邮
        post_free = self.get_argument('post_free', False)
        # 商品详情
        detail_id = self.get_argument('id', False)

        if detail_id:
            # 获取商品的详情信息
            detail_id = self.__reverse_number__(detail_id)
            if detail_id:
                result = yield self.__get_detail__(detail_id)
                if result is not None:
                    self.write(result)
                    return
                else:
                    self.write(self.not_found)
                    return
            else:
                self.write(self.error_message)
        else:
            query = dict()
            query['volume'] = volume
            query['price_range'] = price_range
            query['valid_period'] = valid_period
            query['shop_type'] = shop_type
            query['post_free'] = post_free

            # 第几页
            self.page.page_index = self.get_argument('page_index', None)
            # 查询多少条
            self.page.page_size = self.get_argument('page_size', None)
            self.page.page_index = self.__reverse_number__(self.page.page_index)
            self.page.page_size = self.__reverse_number__(self.page.page_size)

            if self.page.page_size > 50 or self.page.page_size <= 0:
                self.write(self.error_message['message': '一页最多获取50条数据'])
                return

            if self.page.page_index and self.page.page_size:
                yield self.__verification_index__(query)
            else:
                self.write(self.error_message)

    @gen.coroutine
    def __get_detail__(self, detail_id):
        sql = self.sql + " and id = %s "
        result = self.db.find_execute(sql, (detail_id,))
        if isinstance(result, dict):
            self.success['data'] = result
            result = self.encoder.encode(self.success)
        else:
            result = None
        raise gen.Return(result)

    @gen.coroutine
    def __verification_index__(self, query):
        """
        验证方法
        :param query: 
        :return: 
        """

        """
        按照价格查询
         0-10：  9.9包邮
         10-20： 20 元封顶
         20-49： 49元精选
       """
        price_range = query.get('price_range')
        if price_range is not None:
            price_range = price_range.split('-') if len(price_range.split('-')) == 2 else None

        if price_range is not None:
            # 不为空说明符合价格查询的格式，判断数据的正确性
            price_range[0] = self.__reverse_number__(price_range[0])
            price_range[1] = self.__reverse_number__(price_range[1])

            # 不是int数值类型，因为可能存在0所以不能去掉False条件
            if price_range[0] is False or price_range[1] is False:
                self.write(self.error_message)
                return

            price_range = price_range if price_range[1] - price_range[0] > 0 else None

            if price_range is None:
                query['price_range'] = False
            else:
                query['price_range'] = price_range

        if int(query.get('volume')) > 3:
            """按照销量查询"""
            query['volume'] = False

        if query.get('shop_type'):
            """按照分类查询"""
            if re.search(self.sql_LOCALinto, query.get('shop_type')).group():
                # 说明有人可能想SQL注入
                self.write(self.error_message)
                return

        if not self.__reverse_number__(query.get('valid_period')):
            """
            此处如果是0，也不计算
            过期时间是多少天以内的
            5： 代表 5 天以内
          """
            query['valid_period'] = False
        else:
            if query['valid_period'] <= 0:
                query['valid_period'] = 1

        if query['volume'] or query['price_range'] or query['valid_period'] or query['shop_type'] \
            or query['post_free']:
            result = yield self.__execute_index__(query)
            if result is not None:
                self.write(result)
                return  #只能返回数据
            else:
                self.write(self.not_found)
                return
        else:
            self.write(self.error_message)
            return

    @gen.coroutine
    def __execute_index__(self, query):
        # 精选推荐
        valid_period_sql = " and datediff(end_time, now()) <={day} and datediff(end_time, now()) >=0 "
        # 不能查过期的商品
        expired_store_sql = " and datediff(end_time, now()) >=0 "
        # 金额查询
        price_sql = " and price - coupon > {start_price} and price - coupon < {end_price} "
        # 按分类查询
        shop_type_sql = " and shop_type like '%{shop_type}%' "
        # 是否包邮
        post_free_sql = " and post_free = {post_free} "
        # 销量排序 销量最高的商品，不遵守基本规则，只按销量排序
        volume_sql = {
            "volume_sql_0": " order by weights desc ",
            "volume_sql_1": " order by volume desc ",
            "volume_sql_2": " order by coupon / price desc ",
            "volume_sql_3": " order by price asc ",
        }

        # 分页
        limit = " limit {this_page}, {page_size} "

        # 分页SQL
        page_sql = """
            select count(1) as total from commodity where 1=1
        """

        price_range = query.get('price_range')
        if price_range:
            self.sql += price_sql.format(start_price=price_range[0], end_price=price_range[1])
            page_sql += price_sql.format(start_price=price_range[0], end_price=price_range[1])

        valid_period = query.get('valid_period')
        if valid_period:
            self.sql += valid_period_sql.format(day=valid_period)
            page_sql += valid_period_sql.format(day=valid_period)
        else:
            self.sql += expired_store_sql
            page_sql += expired_store_sql
        shop_type = query.get('shop_type')
        if shop_type:
            self.sql += shop_type_sql.format(shop_type=shop_type)
            page_sql += shop_type_sql.format(shop_type=shop_type)

        # 是否包邮
        post_free = query.get('post_free')
        if post_free:
            if post_free == '0' or post_free == '1':
                self.sql += post_free_sql.format(post_free=post_free)
                page_sql += post_free_sql.format(post_free=post_free)

        if query.get('volume'):
            volume = volume_sql.get("volume_sql_" + query.get('volume'))
            self.sql += volume
            page_sql += volume

        # page 不能为 0
        self.page.page_index = 1 if self.page.page_index == 0 else self.page.page_index

        this_page = (self.page.page_index - 1) * self.page.page_size
        self.sql += limit.format(this_page=this_page, page_size=self.page.page_size)
        # 查询商品
        result = self.db.find_execute(self.sql, None, fetchone=False)
        # 查询分页
        total = self.db.find_execute(page_sql, None, fetchone=True)

        if total:
            total = int(total.get('total'))
            if total > 3000:
                self.page.total = 3000
            elif total == 0:
                result = None
            else:
                self.page.total = total
            if self.page.total:
                self.page.page_count = self.page.total / self.page.page_size
                if self.page.page_count > 0:
                    if self.page.page_count > int(self.page.page_count):
                        # 说明除不尽，应该还有一页
                        self.page.page_count = int(self.page.page_count) + 1
                    else:
                        self.page.page_count = int(self.page.page_count)
            else:
                result = None
        else:
            # 一页都没有，不用查了
            result = None

        if isinstance(result, list):
            page = {
                'page_size': self.page.page_size,
                'page_index': self.page.page_index,
                'page_count': self.page.page_count,
                'total': self.page.total
            }
            self.success['data'] = result
            self.success['page'] = page
            result = self.encoder.encode(self.success)
        else:
            result = None
        raise gen.Return(result)
