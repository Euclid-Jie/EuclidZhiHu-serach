# -*- coding: utf-8 -*-
# @Time    : 2023/2/20 23:47
# @Author  : Euclid-Jie
# @File    : Get_answers_of_url.py
import time

import pandas as pd
import pymongo
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from tqdm import tqdm

from Get_answers_of_question import Get_answers_of_question


class Get_answers_of_url(Get_answers_of_question):
    def __init__(self):
        super().__init__()
        self.url = None
        self.collectionName = None

    def GetFullAnswer(self):
        print("开始更新回答全文")
        for id in tqdm(self.mycol.distinct("_id")):
            question_id = self.mycol.find_one({'_id': id})['question_id']
            answer_id = self.mycol.find_one({'_id': id})['answer_id']
            self.driver.get('https://www.zhihu.com/question/{}/answer/{}'.format(question_id, answer_id))
            try:
                answer_Full = self.mycol.find_element(By.CLASS_NAME, 'RichContent-inner').text
                self.mycol.update_one({'_id': id}, {"$set": {'answerRaw': answer_Full}})
            except Exception as e:
                print(e.msg)

    def GetAnswerList(self):
        # 跳转指定关键词回答网页, 一个月, 需要手动滚动
        self.driver.get(self.url)
        print("当前问题为：{}".format(self.driver.title))

        print(">> 自动翻页中......")
        pbar = tqdm(total=self.size)
        init = 0
        while init <= self.size:
            pbar.set_description("page:{}".format(init))  # 进度条左边显示信息
            self.driver.execute_script("document.documentElement.scrollTop={}".format(init * 10000))
            time.sleep(0.5)
            pbar.update(1)
            init += 1

    def GetDataFromAnswer(self, Answer):
        # 是否需要展开，如果是，则点击展开
        if "阅读全文" in Answer.find_element(By.CLASS_NAME, "RichContent-inner").text:
            button = Answer.find_element(By.CLASS_NAME, "Zi.Zi--ArrowDown.ContentItem-arrowIcon")
            self.driver.execute_script("arguments[0].scrollIntoView();", button)
            button.click()

        # 个人信息部分
        soup = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml')
        info = soup.find('div', 'AuthorInfo')
        user_url = info.find('meta', {'itemprop': 'url'})['content']
        user_name = info.meta['content']
        # id部分
        answer_url = soup.find('a', {"target": "_blank"})['href']
        if "zhuanlan" in answer_url:
            zhuanlan = True
            question_id = None
            answer_id = None
        else:
            zhuanlan = False
            question_id = answer_url.split("/")[2]
            answer_id = answer_url.split("/")[4]

        action = soup.find('div', 'ContentItem-actions').text.replace(u'\u200b', ' ')
        answerRaw = soup.find('div', 'RichContent-inner').get_text().replace(u'\u200b', ' ')
        least_datetime = soup.find('div', 'ContentItem-time').get_text().replace('编辑于 ', '')
        first_datetime = soup.find('div', 'ContentItem-time').span['data-tooltip'].replace('发布于 ', '')
        mydict = {"zhuanlna": zhuanlan,
                  "question_id": question_id,
                  "answer_id": answer_id,
                  "answer_url": answer_url,
                  'user_url': user_url,
                  'user_name': user_name,
                  'least_datetime': least_datetime.replace("发布于 ", ""),
                  'first_datetime': first_datetime,
                  "action": action,
                  "answerRaw": answerRaw}
        self.t.set_postfix({"状态": "{}写入成功".format(answer_id)})

        return mydict

    def main(self, url):
        print("-*-" * 10)
        self.url = url

        # 获取回答列表
        self.GetAnswerList()
        answerList = self.driver.find_elements(By.CLASS_NAME, 'List-item')

        # 连接数据库并写入
        print("\n>> 写入数据......")
        self.mycol = self.MongoClient("ZhiHu", self.collectionName)
        with tqdm(answerList) as self.t:
            for answer in self.t:
                try:
                    self.mycol.insert_one(self.GetDataFromAnswer(answer))
                except AttributeError:
                    pass
                except Exception as e:
                    self.t.set_postfix({"状态": e.msg})

        # 拆分Action为赞同、评论数
        print("\n>> 开始拆分Action")
        self.GetActionDetails()


def MongoClient(DBName, collectionName):
    """
    :param DBName: mongoDB dataBase's name
    :param collectionName: mongoDB dataBase's collection's name
    :return: collection
    """
    # client to mongodb at default host
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient[DBName]
    mycol = mydb[collectionName]
    return mycol


def read_mongo(DBName, collectionName, query=None, no_id=True):
    """
    Read from Mongo and Store into DataFrame
    :param DBName: mongoDB dataBase's name
    :param collectionName: mongoDB dataBase's collection's name
    :param query: a selection for data
    :param no_id: do not write _id column to data
    :return: pd.DataFrame
    """
    # Connect to MongoDB
    if query is None:
        query = {}
    col = MongoClient(DBName, collectionName)
    # Make a query to the specific DB and Collection
    cursor = col.find(query)
    # Expand the cursor and construct the DataFrame
    df = pd.DataFrame(list(cursor))
    # Delete the _id
    if no_id and '_id' in df:
        del df['_id']
    return df.drop_duplicates()


if __name__ == '__main__':
    demo = Get_answers_of_url()
    demo.collectionName = '北京师范大学测试'
    url = 'https://www.zhihu.com/search?q=%E5%8C%97%E4%BA%AC%E5%B8%88%E8%8C%83%E5%A4%A7%E5%AD%A6&type=content&vertical=answer&time_interval=a_month'
    demo.size = 20
    demo.main(url)

    # write data to a csv file
    read_mongo("ZhiHu", "北京师范大学测试").to_csv("Test.csv", index=False, encoding='utf_8_sig')
