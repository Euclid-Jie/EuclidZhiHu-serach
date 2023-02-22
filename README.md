因为所在部门有舆情分析项目，所以需要一个知乎数据采集工具。但是已有的工具多是基于知乎的API，据我所知知乎已经关停了API，所以自己写了一份知乎数据采集代码，目前的略显粗糙，将慢慢补充。

## 目前已有功能
- 获取指定问题下的回答，需指定question_id
- 搜索过去一个月，指定关键词的知乎回答，如下图所示

<img src="https://euclid-picgo.oss-cn-shenzhen.aliyuncs.com/image/202211291110085.png" alt="image-20221129111043022" style="zoom: 80%;" />

- 获取指定回答的评论，及其子评论
可使用Get_comments_of_answer.py实现
## 数据输出

| 字段名    | 字段含义             |
| --------- | -------------------- |
| KeyWord   | 关键词               |
| Url       | 问答详细页           |
| answerRaw | 回答详情             |
| date      | 该回答最后的修改时间 |
| Agree     | 赞同数               |
| comment   | 评论数               |

## 前置条件

- 会使用MongoDB数据库（后续将更新Pandas存储方式）
- 会使用selenium接管指定端口的浏览器，可参考[这篇](https://blog.csdn.net/weixin_45081575/article/details/126389273)文章

## 调用方式

- 设置数据库链接参数（数据库名，表名）
- 设置关键词列表

