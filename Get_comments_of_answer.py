# -*- coding: utf-8 -*-
# @Time    : 2023/2/13 16:01
# @Author  : Euclid-Jie
# @File    : Get_comments_of_answer.py
import json
import time
import pymongo
import requests
from tqdm import tqdm


def get_data_json_form_url(url, header):
    """
    get the html content used by requests.get
    :param header:
    :param url:
    :return: BeautifulSoup
    """
    response = requests.get(url, headers=header, timeout=60)  # 使用request获取网页
    html = response.content.decode('utf-8', 'ignore')  # 将网页源码转换格式为html
    data_json = json.loads(html)
    return data_json


def get_data_json(item):
    data_json = {
        'comment_id': item['id'],
        'author': item['author']['name'],
        'created_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['created_time'])),
        'text_raw': item['content'],
        'like_count': item['like_count'],
        'dislike_count': item['dislike_count'],
        'child_comment_count': item['child_comment_count'],
    }
    return data_json


def get_child_data_json(item):
    data_json = {
        'reply_comment_id': item['id'],
        'author': item['author']['name'],
        'created_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['created_time'])),
        'text_raw': item['content'],
        'like_count': item['like_count'],
        'dislike_count': item['dislike_count'],
        'child_comment_count': item['child_comment_count'],
    }
    return data_json


def get_child_comment(father_data_json, mycol):
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0',
    }
    total_pages = father_data_json['child_comment_count']
    comment_id = father_data_json['comment_id']
    url = 'https://www.zhihu.com/api/v4/comment_v5/comment/{}/child_comment?order_by=ts&limit=20&offset='.format(comment_id)
    for page in range(0, int(total_pages / 20) + 1):
        data = get_data_json_form_url(url, header)
        url = data['paging']['next']
        data_list = data['data']
        for item in data_list:
            data_json = get_child_data_json(item)
            mycol.insert_one(data_json)


def MongoClient(DBName, collectionName):
    # 连接数据库
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient[DBName]  # 数据库名称
    mycol = mydb[collectionName]  # 集合（表）
    return mycol


if __name__ == '__main__':
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0',
    }
    answer_id = '681622656'
    url = 'https://www.zhihu.com/api/v4/comment_v5/answers/{}/root_comment?order_by=score&limit=40&offset'.format(answer_id)
    total_pages = get_data_json_form_url(url, header)['paging']['totals']
    mycol = MongoClient("ZhiHu", answer_id)
    for page in tqdm(range(0, int(total_pages / 20) + 1)):
        data = get_data_json_form_url(url, header)
        url = data['paging']['next']
        data_list = data['data']
        for item in data_list:
            data_json = get_data_json(item)
            mycol.insert_one(data_json)
            get_child_comment(data_json, mycol)
