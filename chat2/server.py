import socket
import threading
import json

SERVER = socket.gethostbyname(socket.gethostname())  # 自动获取本机IP地址
PORT = 5050  # 端口号，5050比较安全
ADDR = (SERVER, PORT)  # 地址元组
BUFFER_SIZE = 1024  # 每次可以接收的最大字节数
FORMAT = 'utf-8'  # 字符编码
DISCONNECT_MSG = 'exit'  # 断开连接标志

clients = {}  # 客户端字典 key为addr，value为con
users = {}  # 在线用户字典 key为user，value为ip+port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建服务器


def hande_client(con, addr):
    """处理客户端"""
    print(f"[INFO]{addr}已连接")
    connected = True
    while connected:
        msg = con.recv(BUFFER_SIZE).decode(FORMAT)  # 一直阻塞，直至收到新消息
        data = json.loads(msg)  # 客户端发来的数据
        ip = data["ip"]
        port = data["port"]
        mode = data["mode"]
        sender = data["sender"]
        receiver = data["receiver"]
        format = data["format"]
        online = data["online"]
        message = data["message"]
        users[sender] = addr  # 得到在线用户列表
        print("用户们如下：")
        print(users)

        if message == DISCONNECT_MSG:
            connected = False
            del clients[addr]
        print(f'模式：{mode}，发送者：{sender}，接收者：{receiver}，内容：{message}，在线用户：{online}')

        if mode == "group_chat":
            broadcast(sender, message)  # 向所有用户广播
        # elif mode == "alone_chat":
        #     alone(id, user, message, receiver)  # 向指定用户发送
        # elif mode == "refresh":
        #     refresh(id, user, message, user)  # 向指定用户刷新
        elif mode == "init":  # 初始化
            init(sender, message)  # 向所有用户广播
        elif mode == "group_alone":  # 初始化
            alone(sender, message, receiver)  # 向所有用户广播
    print(f"[INFO]{addr}断开连接！")
    con.close()  # 断开连接


def start():
    """运作服务器"""
    print('[INFO]服务器已连接')
    s.bind(ADDR)  # 绑定地址
    s.listen(5)
    print(f'[INFO]服务器正在监听{SERVER}')
    while True:
        con, addr = s.accept()  # 一直阻塞，直到有新的连接
        clients[addr] = con
        # 开启多线程处理客户端
        thread = threading.Thread(target=hande_client, args=(con, addr))  # 一个客户端占用一个线程
        thread.start()  # 启动线程
        print(f"[INFO]当前线程数是{threading.activeCount() - 1}")  # 客户端线程数量


def broadcast(sender, msg):
    """向所有已连接的客户端广播消息"""
    # 先把所有在线用户遍历一遍，得到用户名列表传过去
    userList = []
    for k in users.keys():
        userList.append(k)

    data = {
        "ip": SERVER,
        "port": PORT,
        "mode": "group_chat",
        "sender": sender,
        "receiver": "all",
        "format": "text",
        "online": userList,
        "message": msg,
    }

    for con in clients.values():
        print("广播：")
        print(data)
        con.send(json.dumps(data).encode(FORMAT))


def init(sender, msg):
    """向所有已连接的客户端广播消息"""
    # 先把所有在线用户遍历一遍，得到用户名列表传过去
    userList = []
    for k in users.keys():
        userList.append(k)

    data = {
        "ip": SERVER,
        "port": PORT,
        "mode": "init",
        "sender": sender,
        "receiver": "all",
        "format": "text",
        "online": userList,
        "message": msg,
    }

    for con in clients.values():
        print("广播：")
        print(data)
        con.send(json.dumps(data).encode(FORMAT))


def alone(sender, msg, receiver):
    """给指定用户发消息"""
    # 先把所有在线用户遍历一遍，得到用户名列表传过去
    userList = []
    for k in users.keys():
        userList.append(k)

    data = {
        "ip": SERVER,
        "port": PORT,
        "mode": "group_alone",
        "sender": sender,
        "receiver": receiver,
        "format": "text",
        "online": userList,
        "message": msg,
    }

    # for con in clients.values():
    print("私聊：")
    print(data)
    clients[users[receiver]].send(json.dumps(data).encode(FORMAT))


# def alone(id, user, msg, rec):
#     """向指定客户端发送消息"""
#     # 先把所有在线用户遍历一遍，得到用户名列表传过去
#     userList = []
#     for u in users.values():
#         userList.append(u)
#
#     Information = {
#         "ip": SERVER,
#         "port": PORT,
#         "mode": "alone_chat",
#         "id": id,
#         "user": user,
#         "receiver": rec,
#         "format": "text",
#         "online": userList,
#         "message": msg,
#     }
#     me = get_key(users, user)
#     addr = get_key(users, rec)
#     # addr=users[rec]
#     print("私聊：")
#     print(addr)
#     print(Information)
#     clients[me].send(json.dumps(Information).encode(FORMAT))
#     clients[addr].send(json.dumps(Information).encode(FORMAT))
#
#
# def refresh(id, user, msg, rec):
#     """向指定客户端发送消息"""
#     # 先把所有在线用户遍历一遍，得到用户名列表传过去
#     userList = []
#     for u in users.values():
#         userList.append(u)
#
#     Information = {
#         "ip": SERVER,
#         "port": PORT,
#         "mode": "refresh",
#         "id": id,
#         "user": user,
#         "receiver": rec,
#         "format": "text",
#         "online": userList,
#         "message": msg,
#     }
#     addr = get_key(users, rec)
#     # addr = users[rec]
#     print("刷新：")
#     print(addr)
#     print(Information)
#     clients[addr].send(json.dumps(Information).encode(FORMAT))
#
#
# def get_key(dict, value):
#     """获取用户的套接字"""
#     for k, v in dict.items():
#         if v == value:
#             return k
#     return None


if __name__ == '__main__':
    start()
