# -*- coding: utf-8 -*-
# @Time    : 2022/11/29 9:58
# @Author  : Euclid-Jie
# @File    : Get_answers_of_question.py
import re
import time
from bs4 import BeautifulSoup
import pymongo
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm
from selenium.webdriver.support.wait import WebDriverWait


class Get_answers_of_question:
    def __init__(self):
        # para init
        self.mycol = None
        self.question_id = None

        # drive init
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(options=options)

        # pages rolling setting
        self.init = 0
        self.size = 2  # the huge size is meaning more answer

    def GetDataFromAnswer(self, soup):
        # 个人信息部分
        info = soup.find('div', 'AuthorInfo')
        answer_id = soup.find('div', 'ContentItem AnswerItem')['name']
        user_url = info.find('meta', {'itemprop': 'url'})['content']
        user_name = info.meta['content']
        action = soup.find('div', 'ContentItem-actions').text.replace(u'\u200b', ' ')
        answerRaw = soup.find('div', 'RichContent-inner').get_text().replace(u'\u200b', ' ')
        least_datetime = soup.find('div', 'ContentItem-time').get_text().replace('编辑于 ', '')
        first_datetime = soup.find('div', 'ContentItem-time').span['data-tooltip'].replace('发布于 ', '')

        mydict = {"question_id": self.question_id,
                  "answer_id": answer_id,
                  'user_url': user_url,
                  'user_name': user_name,
                  'least_datetime': least_datetime.replace("发布于 ", ""),
                  'first_datetime': first_datetime,
                  "action": action,
                  "answerRaw": answerRaw}
        self.t.set_postfix({"状态": "{}写入成功".format(answer_id)})

        return mydict

    def GetAnswerList(self):
        # 跳转指定关键词回答网页, 一个月, 需要手动滚动
        self.driver.get('https://www.zhihu.com/question/{}'.format(self.question_id))

        print(">> 自动翻页中......")
        pbar = tqdm(total=self.size)
        init = 0
        while init <= self.size:
            pbar.set_description("page:{}".format(init))  # 进度条左边显示信息
            self.driver.execute_script("document.documentElement.scrollTop={}".format(init * 10000))
            time.sleep(0.5)
            pbar.update(1)
            init += 1

    def MongoClient(self, DBName, collectionName):
        # 连接数据库
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient[DBName]  # 数据库名称
        mycol = mydb[collectionName]  # 集合（表）
        return mycol

    def GetActionDetails(self):
        for id in tqdm(self.mycol.distinct("_id")):
            action = self.mycol.find_one({'_id': id})['action']
            try:
                p = re.compile('(?<=赞同\D)[\d]+(?=\D)')  # #re#表示正则表达式
                Agree = p.findall(action)[0]  # text_raw表示原始字符串
                self.mycol.update_one({'_id': id}, {"$set": {'Agree': Agree}})
            except IndexError:
                pass

            try:
                p = re.compile('\d+(?=\D条评论)')  # #re#表示正则表达式
                comment = p.findall(action)[0]  # text_raw表示原始字符串
                self.mycol.update_one({'_id': id}, {"$set": {'comment': comment}})
            except IndexError:
                pass

    def main(self, question_id_list):
        for question_id in question_id_list:
            print("-*-" * 10)
            self.question_id = question_id
            print("当前问题为：{}".format(question_id))

            # 获取回答列表
            self.GetAnswerList()
            answerList = self.driver.find_elements(By.CLASS_NAME, 'List-item')

            # 连接数据库并写入
            print("\n>> 写入数据......")
            self.mycol = self.MongoClient("ZhiHu", question_id)
            with tqdm(answerList) as self.t:
                for answer in self.t:
                    try:
                        soup = BeautifulSoup(answer.get_attribute('outerHTML'), features='lxml')
                        self.mycol.insert_one(self.GetDataFromAnswer(soup))
                    except AttributeError:
                        pass
                    except Exception as e:
                        self.t.set_postfix({"状态": e.msg})

            # 拆分Action为赞同、评论数
            print("\n>> 开始拆分Action")
            self.GetActionDetails()


if __name__ == '__main__':
    question_id_list = ['22636295', '291200054']
    Get_answers_of_question().main(question_id_list)
