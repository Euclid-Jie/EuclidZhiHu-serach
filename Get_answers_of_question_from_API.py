# -*- coding: utf-8 -*-
# @Time    : 2023/3/8 10:47
# @Author  : Euclid-Jie
# @File    : Get_answers_of_question_from_API.py
import json
from json import JSONDecodeError
import pandas as pd
import pymongo
import requests
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from tqdm import tqdm


class Get_answers_of_question_from_API:
    def __init__(self, proxies=None):
        # para init
        self.mycol = None
        self.collectionName = None
        self.page = None
        self.baseUrl = None
        self.proxies = proxies
        self.data = None
        self.data_json = None
        self.questions_id = None
        self.Url = None
        # base url set
        self.set_base_url('baseUrl.txt')
        # drive init
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(options=options)

    def MongoClient(self):
        # 连接数据库
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["ZhiHu"]  # 数据库名称
        self.mycol = mydb[self.collectionName]  # 集合（表）

    def set_base_url(self, baseUrlFileName):
        """
        API base url, if u know question_id, can use API to get data
        :param baseUrlFileName: baseUrl.txt
        :return: 请求头header,dict
        """
        with open(baseUrlFileName, 'rt', encoding='utf-8') as f:
            self.baseUrl = f.read().strip()

    def get_json_data_from_Url(self):
        """
        :return:
        """
        # response = requests.get(self.Url)
        # self.data_json = json.loads(response.content)
        self.driver.get(self.Url)
        html = self.driver.page_source
        content = BeautifulSoup(html, features="lxml").body.text.encode('gbk', 'ignore').decode('gbk')
        try:
            self.data_json = json.loads(content, strict=False)
        except JSONDecodeError as e:
            pass
        try:
            if len(self.data_json['data']) > 0:
                self.get_item_answer_json_data()
        except KeyError as e:
            print("请完成验证后键入 y")
            input()
            self.get_json_data_from_Url()

    def main_get(self, questions_list):
        for self.questions_id in questions_list:
            # collection name setting
            if not self.collectionName:
                self.collectionName = self.questions_id + '_API'
            # mongo init
            self.MongoClient()
            # get total answer num
            self.driver.get('https://www.zhihu.com/question/{}'.format(self.questions_id))
            total_answer = self.driver.find_element(By.CLASS_NAME, "List-headerText").text.split(' ')[0]
            total_answer = int(total_answer.replace(",", ""))
            with tqdm(total=total_answer) as self.pbar:
                # get base url of question: pages 1
                self.Url = self.baseUrl.format(self.questions_id)
                self.pbar.set_description("question:{}-page:{}".format(self.questions_id, 1))
                # rolling get data
                while True:
                    self.get_json_data_from_Url()
                    if not self.data_json['paging']['is_end']:
                        # update Url and page number
                        self.Url = self.data_json['paging']['next']
                        page = self.data_json['paging']['page']
                        self.pbar.set_description("question:{}-page:{}".format(self.questions_id, page))
                    else:
                        break

    def get_item_answer_json_data(self):
        for answer_i in self.data_json['data']:
            answer_i_json_data = {
                # use info
                'use_id': answer_i['target']['author']['id'],
                'use_name': answer_i['target']['author']['name'],
                # question info
                'question': answer_i['target']['question']['title'],
                # answer info
                'question_id': self.questions_id,
                'answer_id': answer_i['target']['id'],
                # answer content
                'content': BeautifulSoup(answer_i['target']['content'], features="lxml").text,
                # time
                'created_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(answer_i['target']['created_time'])),
                'updated_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(answer_i['target']['updated_time'])),
                # action
                'agree_count': answer_i['target']['voteup_count'],
                'comment_count': answer_i['target']['comment_count'],
                'thanks_count': answer_i['target']['thanks_count']
            }
            # insert data json to mongoDB
            self.mycol.insert_one(answer_i_json_data)
            self.pbar.update(1)
            self.pbar.set_postfix({"状态": "已写入question:{}-answer:{}"
                                  .format(self.questions_id, answer_i_json_data['answer_id'])})


if __name__ == '__main__':
    # print("请输入question id")
    # answer_id = str(input())
    # question_id_list = [answer_id]

    # question_id_list = ['22636295', '291200054']

    question_df = pd.read_csv('应用统计专硕就业.csv')
    question_id_list = question_df[question_df.zhuanlna == False]['question_id'].to_list()
    question_id_list = [str(int(question_id)) for question_id in question_id_list]
    demo = Get_answers_of_question_from_API()
    demo.collectionName = '应用统计专硕就业_API'
    # TODO 运行前请更新baseUrl.txt
    demo.main_get(question_id_list)
