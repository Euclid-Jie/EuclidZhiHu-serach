# -*- coding: utf-8 -*-
# @Time    : 2023/2/13 16:01
# @Author  : Euclid-Jie
# @File    : Get_comments_of_answer.py
import json
import time
import pandas as pd
import pymongo
import requests
from tqdm import tqdm
from EuclidDataTools import *


class Get_comments_of_answer:
    """
    this class is designed to get single answer' comments and comments' child_comment
        1、the answer url is like: https://www.zhihu.com/question/315914320/answer/681622656,
        this url tell us: the question id is 315914320, and the answer id is 681622656
        2、get comments of single answer by requests.get an url linked to answer id
         url: https://www.zhihu.com/api/v4/comment_v5/answers/681622656/root_comment?order_by=score&limit=20&offset=
         when we know the answer id ,get the url is easy to get
        3、get child_comment of single comments is similar to getting comments of single answer
        by requests.get url linked to comments id
        url: https://www.zhihu.com/api/v4/comment_v5/comment/646728923/child_comment?order_by=ts&limit=20&offset=
        the comments id can get in 2、

    the difference from comments and child_comment
    1、comments:
        id: comment id
        reply_comment_id: "0"
    2、child_comment:
        id: child_comment id
        reply_comment_id: comment id

    Fortunately, not use cookie and ip proxies, can get all comments
    What is suggested is that time.sleep() for item answer
    """

    def __init__(self, header, answer_id, mongo=False):
        self.mongo = mongo
        self.mycol = None
        self.proxies = None
        self.header = header
        self.answer_id = answer_id
        self.collectionName = "Comments_" + str(int(answer_id))
        self.url = None

    def get_data_json_form_url(self):
        """
        get the html content used by requests.get
        :return: BeautifulSoup
        """
        response = requests.get(self.url, headers=self.header, timeout=60, proxies=self.proxies)  # 使用request获取网页
        html = response.content.decode('utf-8', 'ignore')  # 将网页源码转换格式为html
        data_json = json.loads(html)
        return data_json

    def get_data_json(self, item):
        data_json = {
            'answer_id': self.answer_id,
            'reply_comment_id': item['reply_comment_id'],
            'id': item['id'],
            'author': item['author']['name'],
            'created_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['created_time'])),
            'text_raw': item['content'],
            'like_count': item['like_count'],
            'dislike_count': item['dislike_count'],
            'child_comment_count': item['child_comment_count'],
        }
        return data_json

    def get_child_comment(self, father_data_json):
        total_pages = father_data_json['child_comment_count']
        comment_id = father_data_json['id']
        self.url = 'https://www.zhihu.com/api/v4/comment_v5/comment/{}/child_comment?order_by=ts&limit=20&offset='.format(comment_id)
        for page in range(0, int(total_pages / 20) + 1):
            data = self.get_data_json_form_url()
            self.url = data['paging']['next']
            data_list = data['data']
            for item in data_list:
                data_json = self.get_data_json(item)
                self.mycol.insert_one(data_json)
                self.t.set_postfix({"状态": "已写入child_comment:{}-{}".format(data_json['reply_comment_id'], data_json['id'])})

    def MongoClient(self):
        # 连接数据库
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["ZhiHu"]  # 数据库名称
        self.mycol = mydb[self.collectionName]  # 集合（表）

    def main(self):
        if self.mongo:
            self.MongoClient()
        else:
            self.mycol = CsvClient(subFolder='outData', FileName=self.collectionName)
        self.url = 'https://www.zhihu.com/api/v4/comment_v5/answers/{}/root_comment?order_by=score&limit=40&offset'.format(int(answer_id))
        total_pages = self.get_data_json_form_url()['paging']['totals']
        with tqdm(range(0, int(total_pages / 20) + 1)) as self.t:
            for page in self.t:
                self.t.set_description("page:{}".format(page))  # 进度条左边显示信息
                data = self.get_data_json_form_url()
                data_list = data['data']
                for item in data_list:
                    data_json = self.get_data_json(item)
                    self.mycol.insert_one(data_json)
                    self.t.set_postfix({"状态": "已写入comments:{}".format(data_json['id'])})
                    # if comments have child_comment, get child_comment
                    # if data_json['child_comment_count'] > 0:
                    #     self.get_child_comment(data_json)
                self.url = data['paging']['next']


if __name__ == '__main__':
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    }
    # question_376738227: ['2291037475', '2666925246', '2764000004', '1715806477', '2743611338']
    # question_315914320 = ['948633721', '779651349', '1889296546', '1006650691', '1280485524', '903387921', '1280709300', '829298544']
    answer_df = pd.read_csv('topic_21289642.csv（120）.csv')
    for answer_id in answer_df['answer_id']:
        demo = Get_comments_of_answer(header, answer_id)
        demo.collectionName = 'comments_of_topic_21289642'
        demo.main()
