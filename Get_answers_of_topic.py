# -*- coding: utf-8 -*-
# @Time    : 2023/3/3 23:08
# @Author  : Euclid-Jie
# @File    : Get_answers_of_topic.py
import json
import time

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from tqdm import tqdm

from Get_answers_of_question import Get_answers_of_question


class Get_answers_of_topic(Get_answers_of_question):
    def __init__(self, topic_id, proxies=None, collectionName=None):
        # super init
        super().__init__()

        # para init
        self.topic_id = topic_id
        self.proxies = proxies

        if not collectionName:
            self.collectionName = self.topic_id
        else:
            self.collectionName = collectionName
        self.url = 'https://www.zhihu.com/topic/{}/hot'.format(self.topic_id)

    def GetAnswerList(self):
        # 跳转指定关键词回答网页, 一个月, 需要手动滚动
        self.driver.get(self.url)
        print("当前问题为：{}".format(self.driver.title))
        print(">> 请手动翻页，完成后键入 y ")
        input()

    def GetDataFromAnswer(self, soup):
        # 回答基础信息
        title = soup.find('a', {'data-za-detail-view-element_name': 'Title'}).get_text()
        url = soup.find('a', {'data-za-detail-view-element_name': 'Title'})['href']
        if "zhuanlan" in url:
            zhuanlan = True
            question_id = None
            answer_id = None
        else:
            zhuanlan = False
            question_id = url.split("/")[-3]
            answer_id = url.split("/")[-1]

        # 个人信息
        info = soup.find('div', 'AuthorInfo')
        user_url = info.find('meta', {'itemprop': 'url'})['content']
        user_name = info.meta['content']
        action = soup.find('div', 'ContentItem-actions').text.replace(u'\u200b', ' ')
        answerRaw = soup.find('div', 'RichContent-inner').get_text().replace(u'\u200b', ' ').replace('\n', '')
        try:
            least_datetime = soup.find('div', 'ContentItem-time').get_text().replace('编辑于 ', '').replace("发布于 ", "")
            first_datetime = soup.find('div', 'ContentItem-time').span['data-tooltip'].replace('发布于 ', '')
        except AttributeError as e:
            least_datetime = None
            first_datetime = None

        mydict = {"zhuanlna": zhuanlan,
                  "title": title,
                  "answer_url": url,
                  "question_id": question_id,
                  "answer_id": answer_id,
                  'user_url': user_url,
                  'user_name': user_name,
                  'least_datetime': least_datetime,
                  'first_datetime': first_datetime,
                  "action": action,
                  "answerRaw": answerRaw}
        self.t.set_postfix({"状态": "{}写入成功".format(answer_id)})

        return mydict

    def main(self):
        # self.GetAnswerList()
        answerList = self.driver.find_elements(By.CLASS_NAME, 'List-item.TopicFeedItem')

        # 连接数据库并写入
        print("\n>> 写入数据......")
        self.mycol = self.MongoClient("ZhiHu", self.collectionName)
        with tqdm(answerList) as self.t:
            for answer in self.t:
                try:
                    soup = BeautifulSoup(answer.get_attribute('outerHTML'), features='lxml')
                    self.mycol.insert_one(self.GetDataFromAnswer(soup))
                # except AttributeError:
                #     pass
                except Exception as e:
                    self.t.set_postfix({"状态": e})

        # 拆分Action为赞同、评论数
        print("\n>> 开始拆分Action")
        self.GetActionDetails()


if __name__ == '__main__':
    demo = Get_answers_of_topic('21289642')
    demo.collectionName = 'topic_' + demo.topic_id

    demo.mycol = demo.MongoClient("ZhiHu", demo.collectionName)
    demo.GetActionDetails()
