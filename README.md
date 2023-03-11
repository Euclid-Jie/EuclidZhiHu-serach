## 前置条件

- 会使用MongoDB数据库（已更新excel(csv)存储方式）
- 会使用selenium接管指定端口的浏览器，可参考[这篇](https://blog.csdn.net/weixin_45081575/article/details/126389273)文章

# 目前已有功能
## 获取指定问题下的回答

`Get_answers_of_question_from_API`

- 更新`base_url`

  1、打开知乎的[某个](https://www.zhihu.com/question/266068728)指定问题

  2、打开浏览器开发工具（F12打开）

  3、刷新页面，往下滚动网页，找到`feed`的请求，如下图所示
  
  4、将末尾的数字更新至baseUrl.txt，即完成更新

![image-20230311122156648](https://euclid-picgo.oss-cn-shenzhen.aliyuncs.com/image/202303111221843.png)

- 参数修改

```python
question_id_list = ['22636295', '291200054'] # 问题id，以列表形式传入
question_id_list = ['22636295']  # 单个问题也需要写成这样
demo = Get_answers_of_question_from_API(MongoDB=False)  # 如需写入Mongo请设置Ture
# demo.collectionName = 'demoName'  # 如需设置文件名，请取消注释，默认文件名为qustion_id_API
demo.main_get(question_id_list)  # 运行前，请打9222端口的托管浏览器，并登录知乎
```

[旧版本]使用`Get_answers_of_question.py` 

- 调整参数

  ```python
  question_id_list = ['22636295', '291200054']  # 问题id
  ```

- 调用

  ```python
  Get_answers_of_question().main(question_id_list)  # 直接传入question_id_list调用
  ```



## 获取指定条件下的回答或专栏

使用`Get_answers_of_url.py`

- 进入高级搜索搜索过去一周内，指定关键词的知乎回答，如下图所示，获取[链接](https://www.zhihu.com/search?q=%E5%A6%82%E4%BD%95%E8%AF%84%E4%BB%B7%E5%BC%A0%E9%A2%82%E6%96%87&type=content&utm_content=search_preset&time_interval=a_week)

![image-20230223002246089](https://euclid-picgo.oss-cn-shenzhen.aliyuncs.com/image/202302230022113.png)

- 调整参数

  ```python
  demo = Get_answers_of_url()  # 实例化
  demo.collectionName = 'Test'  # 设置collection的名字
  url = 'https://www.zhihu.com/search?q=如何评价张颂文&type=content&utm_content=search_preset&time_interval=a_week'  # 上一步的网址
  ```
- 调用

  ```python
  demo.main(url)  # 直接传入url调用
  ```

## 获取某个回答下的评论和子评论

使用`Get_comments_of_answer.py`

- 调整参数

  ```python
  # 挑选某个问题下的某几个回答的id，写入list中
  question_315914320: ['948633721', '779651349', '1889296546', '1006650691', '1280485524', '903387921', '1280709300', '829298544']
  # 遍历这几个回答，获取其评论和子评论
  for answer_id in question_315914320:
      demo = Get_comments_of_answer(header, answer_id)
      # 设置collection的名字
      demo.collectionName = 'comments_of_question_315914320'
      demo.main()
  ```

## 数据输出

### 回答信息

| 字段名         | 字段含义     |
| -------------- | ------------ |
| action         | 转评赞信息   |
| answerRaw      | 回答全文     |
| answer_id      | 回答id       |
| first_datetime | 发布时间     |
| least_datetime | 修改时间     |
| question_id    | 问题id       |
| user_name      | 用户昵称     |
| user_url       | 用户主页链接 |

### 评价信息

| 字段名              | 字段含义 |
| ------------------- | -------- |
| answer_id           | 回答id   |
| reply_comment_id    | 父评论id |
| id                  | 评论id   |
| author              | 用户昵称 |
| created_time        | 创建时间 |
| text_raw            | 评论内容 |
| like_count          | 喜欢数   |
| dislike_count       | 不喜欢数 |
| child_comment_count | 子评论数 |

---

---

## 知乎数据结构（可略过）

本部分的内容，作为开发数据采集工具、理解数据结构的基础，将介绍知乎的几种数据构成方式

![img](https://euclid-picgo.oss-cn-shenzhen.aliyuncs.com/image/202302222310870.png)

### 主要数据来源

#### 问题：网友在知乎上的提问

知乎立身之本，有问题就会有答案，以这个[问题](https://www.zhihu.com/question/280691023)为例。

可获取的数据包括：

- 问题内容：中国为什么强大？
- 问题的关注者：共3242个
- 问题浏览量：6119977
- 问题评论：20条
- 问题点赞（好问题）：23次

![image-20230222231638869](https://euclid-picgo.oss-cn-shenzhen.aliyuncs.com/image/202302222316919.png)

#### 回答

有问题就会有回答，每个问题都会有很多回答，上述的例子中，共有1737个回答。

![image-20230222231951332](https://euclid-picgo.oss-cn-shenzhen.aliyuncs.com/image/202302222319384.png)

以第一条[回答](https://www.zhihu.com/question/280691023/answer/2862942939)为例。可以获取的数据包括：

- 答主的个人信息
  - 昵称：你开心就好
  - 个性签名：破乎药丸
  - Id：355eff4458f318fd78cabd425fef7a12
  - IP属地：广西
  - 个人主页链接：https://www.zhihu.com/people/peng-bao-hao
- 回答信息
  - 回答内容
  - 发布时间：2023-01-11 10:48
  - 编辑时间：2023-01-15 00:32
  - IP属地：广西
  - 回答赞同数：1.7万（17190）
  - 评论数：429
  - 喜欢数：2924
  - 收藏数：3850

![image-20230222232208962](https://euclid-picgo.oss-cn-shenzhen.aliyuncs.com/image/202302222322016.png)

- 回答的评论及其子评论

  - 评论人的个人信息
    - 昵称：清风徐来
    - id：7a51f0f3999c8571b4643c8948caff0b
    - IP属地：江苏
  - 评论信息
    - 评论内容
    - 评论id：10411961541
    - 点赞数：68
    - 子评论数：3
    - 创建时间：2023-1-11 19:14:11

  ![image-20230223001000630](https://euclid-picgo.oss-cn-shenzhen.aliyuncs.com/image/202302230010666.png)

  - 子评论信息

    - 评论人的个人信息
      - 昵称：illlidan03
      - id：cca096fcdb26dcbc1a6dbceb9b1c1ab0
      - IP属地：北京
    - 子评论内容
      - 子评论内容
      - 子评论id：10413152004
      - 父评论id：10411961541
      - 子评论创建时间：2023-1-12 16:3:6

    ![image-20230223001322180](https://euclid-picgo.oss-cn-shenzhen.aliyuncs.com/image/202302230013206.png)

#### 专栏
