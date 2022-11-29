# -*- coding: utf-8 -*-
# @Time    : 2022/11/29 9:58
# @Author  : Euclid-Jie
# @File    : AnswerSearch.py
from bs4 import BeautifulSoup
import pymongo
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm


def GetDataFromAnswer(Answer, KeyWord):
    Url = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('a', {"target": "_blank"})['href']
    question = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('h2', 'ContentItem-title').get_text().replace(u'\u200b', ' ')
    try:
        action = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('div', 'ContentItem-actions ContentItem-action css-q1mqvc').text.replace(u'\u200b', ' ')
    except:
        action = ''
    try:
        answerRaw = BeautifulSoup(Answer.get_attribute('outerHTML'), features='lxml').find('div', 'RichContent-inner').get_text().replace(u'\u200b', ' ')
    except:
        answerRaw = ''
    mydict = {"KeyWord": KeyWord, "Url": Url, 'question': question, "action": action, "answerRaw": answerRaw}
    return mydict


def GetAnswerList(KeyWord):
    # 跳转指定关键词回答网页, 一个月, 需要手动滚动
    # TODO 解决自动滚动问题
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.zhihu.com/search?q=' + KeyWord + '&type=content&vertical=answer&time_interval=a_month')
    print('浏览器托管成功，请人工滚动至末尾, 操作完成后请键入任意值回车')
    input()

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
        Url_i = mycol.find_one({'_id': id})['Url']
        driver.get('https://www.zhihu.com' + Url_i)
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
            p = re.compile('(?<=评论).+')  # #re#表示正则表达式
            date = p.findall(action)[0]  # text_raw表示原始字符串
            mycol.update_one({'_id': id}, {"$set": {'date': date}})
        except:
            pass

        try:
            p = re.compile('(?<=赞同\D)\d+(?=\D)')  # #re#表示正则表达式
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
    keywordList = ['北师大', '北京师范大学', '北京师范大学统计学院', 'BNU', '北师', '北京师范大学珠海校区']
    for keyword in keywordList:
        print("当前关键词为：{}".format(keyword))
        # 获取回答列表
        driver = GetAnswerList(keyword)
        answerList = driver.find_elements(By.CLASS_NAME, 'List-item')

        # 连接数据库并写入
        mycol = MongoClient("ZhiHu", '11月知乎舆情')
        for answer in answerList:
            try:
                mycol.insert_one(GetDataFromAnswer(answer, keyword))
            except:
                continue

    # 更新详细回答
    GetFullAnswer(mycol)

    # 拆分Action为时间、赞同、评论数
    GetActionDetails(mycol)
