# -*- coding: utf-8 -*-
# @Time    : 2022/11/29 9:58
# @Author  : Euclid-Jie
# @File    : AnswerSearch.py
import re
from bs4 import BeautifulSoup
import pymongo
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm


def GetDataFromAnswer(Answer, question_id):
    answer_id = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('div', 'ContentItem AnswerItem')['name']
    user_url = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('div', 'AuthorInfo').find('meta', {'itemprop': 'url'})['content']
    user_name = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('div', 'AuthorInfo').meta['content']
    try:
        action = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('div', 'ContentItem-actions').text.replace(u'\u200b', ' ')
    except:
        action = ''
    try:
        answerRaw = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('div', 'RichContent-inner').get_text().replace(u'\u200b', ' ')
    except:
        answerRaw = ''
    try:
        least_datetime = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('div', 'ContentItem-time').get_text().replace('编辑于 ', '')
    except:
        pass
    try:
        first_datetime = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('div', 'ContentItem-time').span['data-tooltip'].replace('发布于 ', '')
    except:
        pass
    mydict = {"question_id": question_id, "answer_id": answer_id, 'user_url': user_url, 'user_name': user_name, 'least_datetime': least_datetime,
              'first_datetime':first_datetime, "action": action, "answerRaw": answerRaw}
    return mydict


def GetAnswerList(question_id):
    # 跳转指定关键词回答网页, 一个月, 需要手动滚动
    # TODO 解决自动滚动问题
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=options)
    # driver.get('https://www.zhihu.com/question/{}'.format(question_id))
    # print('浏览器托管成功，请人工滚动至末尾, 操作完成后请键入任意值回车')
    # input()

    return driver


def MongoClient(DBName, collectionName):
    # 连接数据库
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient[DBName]  # 数据库名称
    mycol = mydb[collectionName]  # 集合（表）
    return mycol


def GetFullAnswer(mycol):
    print("开始更新回答全文")
    for id in tqdm(mycol.distinct("_id")):
        question_id = mycol.find_one({'_id': id})['question_id']
        answer_id = mycol.find_one({'_id': id})['answer_id']
        driver.get('https://www.zhihu.com/question/{}/answer/{}'.format(question_id, answer_id))
        try:
            answer_Full = driver.find_element(By.CLASS_NAME, 'RichContent-inner').text
            mycol.update_one({'_id': id}, {"$set": {'answerRaw': answer_Full}})
        except:
            continue


def GetActionDetails(mycol):
    print("开始拆分Action")
    for id in tqdm(mycol.distinct("_id")):
        action = mycol.find_one({'_id': id})['action']
        try:
            p = re.compile('(?<=赞同\D)[\d]+(?=\D)')  # #re#表示正则表达式
            Agree = p.findall(action)[0]  # text_raw表示原始字符串
            mycol.update_one({'_id': id}, {"$set": {'Agree': Agree}})
        except:
            pass

        try:
            p = re.compile('\d+(?=\D条评论)')  # #re#表示正则表达式
            comment = p.findall(action)[0]  # text_raw表示原始字符串
            mycol.update_one({'_id': id}, {"$set": {'comment': comment}})
        except:
            pass


if __name__ == '__main__':
    question_id_list = ['315914320']
    for question_id in question_id_list:
        print("当前问题为：{}".format(question_id))
        # 获取回答列表
        driver = GetAnswerList(question_id)
        answerList = driver.find_elements(By.CLASS_NAME, 'List-item')

        # 连接数据库并写入
        mycol = MongoClient("ZhiHu", question_id)
        for answer in answerList:
            try:
                mycol.insert_one(GetDataFromAnswer(answer, question_id))
            except:
                continue

    # 更新详细回答
    # GetFullAnswer(mycol)

    # 拆分Action为赞同、评论数
    GetActionDetails(mycol)
