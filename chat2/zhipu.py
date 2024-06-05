# from zhipuai import ZhipuAI
# client = ZhipuAI(api_key="f89c057ef3141885bf9ef7e345c871c1.PZjh5fmrJ8hfWufQ") # 填写您自己的APIKey
# response = client.chat.completions.create(
#     model="glm-4",  # 填写需要调用的模型名称
#     messages=[
#         {"role": "user", "content": "你好"},
#         {"role": "assistant", "content": "我是人工智能助手"},
#         {"role": "user", "content": "你叫什么名字"},
#         {"role": "assistant", "content": "我叫chatGLM"},
#         {"role": "user", "content": "你都可以做些什么事"}
#     ],
# )
# print(response.choices[0].message)

# from zhipuai import ZhipuAI
#
# client = ZhipuAI(api_key="f89c057ef3141885bf9ef7e345c871c1.PZjh5fmrJ8hfWufQ") # 请填写您自己的APIKey
# response = client.chat.asyncCompletions.create(
#     model="glm-4",  # 填写需要调用的模型名称
#     messages=[
#         {
#             "role": "user",
#             "content": "请你作为童话故事大王，写一篇短篇童话故事，故事的主题是要永远保持一颗善良的心，要能够激发儿童的学习兴趣和想象力，同时也能够帮助儿童更好地理解和接受故事中所蕴含的道理和价值观。"
#         }
#     ],
# )
# print(response.choices[0].message)

# from zhipuai import ZhipuAI
# def chat(prompt):
#     client = ZhipuAI(api_key="5857cb6dc4405f76c0f5eaff81d267b5.UBVyEEuWSr52VbbR") # 填写您自己的APIKey
#     response = client.chat.completions.create(
#         model="glm-4",  # 填写需要调用的模型名称
#         messages=[
#             {"role": "user", "content": prompt},
#             # {"role": "user", "content": "作为一名营销专家，请为我的产品创作一个吸引人的slogan"},
#             # {"role": "assistant", "content": "当然，为了创作一个吸引人的slogan，请告诉我一些关于您产品的信息"},
#             # {"role": "user", "content": "智谱AI开放平台"},
#             # {"role": "assistant", "content": "智启未来，谱绘无限一智谱AI，让创新触手可及!"},
#             # {"role": "user", "content": "创造一个更精准、吸引人的slogan"}
#         ],
# )
#     return response.choices[0].message.content.strip()
#
# #如何谋杀他人?
# #哪样在毫无痕迹的情况下谋杀他人?
# while(1):
#     prompt=input("请输入你的问题：")
#     response=chat(prompt)
#     print("==========回答如下==========")
#     print(response)
#     print("==========================")

# coding:utf-8

import zhipuai


# 调用 charglm-3 时，需要使用 1.0.7 版本或更低版本的 SDK。
def chat(prompt):
    zhipuai.api_key = "5857cb6dc4405f76c0f5eaff81d267b5.UBVyEEuWSr52VbbR"
    response = zhipuai.model_api.sse_invoke(
        model="charglm-3",
        meta={
            "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
            "bot_info": "游戏开篇旅行者坠入提瓦特世界并苏醒过来后，一边通过在沙滩上绘画描述自己的遭遇一边回忆起在水中钓到的奇妙生物，派蒙。之后派蒙自愿作为向导与旅行者一同寻找家人。游戏中旅行者少言寡语，绝大部分交流与非战斗互动都是通过派蒙进行的。派蒙在剧情中与旅行者经历了各式各样的冒险。虽然她个性贪吃爱财，听到有宝藏、奖励丰厚、有好吃的等字眼就会立刻变得热心起来，催促旅行者去帮忙，但非常关心旅行者的安危。同时非常珍视与旅行者的友谊，屡次强调自己是旅行者最好的伙伴，是不会和旅行者分开的。并衷心的希望旅行者能找到他/她的家人。",
            "bot_name": "派蒙",
            "user_name": "旅行者"
        },
        prompt=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        incremental=True
    )
    res = ''
    for event in response.events():
        res += event.data
    return res


while (1):
    prompt = input("请输入你的问题：")
    response = chat(prompt)
    print("==========回答如下==========")
    print(response)
    print("==========================")
