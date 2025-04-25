# # 目的只是调试dashscope的qwen2.5-vl-32b-instruct模型，跟本项目代码无关
# import os
# import dashscope
# messages = [
# {
#     "role": "system",
#     "content": [
#     {"text": "You are a helpful assistant."}]
# },
# {
#     "role": "user",
#     "content": [
#     {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
#     {"text": "图中描绘的是什么景象?"}]
# }]
# response = dashscope.MultiModalConversation.call(
#     #若没有配置环境变量， 请用百炼API Key将下行替换为： api_key ="sk-xxx"
#     api_key = "sk-17bdfe3406ef48608f062440bad3acf2",
#     model = 'qwen2.5-vl-32b-instruct',
#     messages = messages
# )

# # 添加错误处理
# if response is None:
#     print("请求返回为空，请检查API密钥是否正确或网络连接是否正常")
# elif hasattr(response, 'output') and response.output:
#     print(response.output.choices[0].message.content[0]["text"])
# else:
#     print("API响应异常:", response)

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage

chatLLM = ChatTongyi(
    model="qwen-max",   # 此处以qwen-max为例，您可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    dashscope_api_key='sk-17bdfe3406ef48608f062440bad3acf2',
    streaming=True,
    # other params...
)
res = chatLLM.stream([HumanMessage(content="hi")], streaming=True)
for r in res:
    print("chat resp:", r.content)
