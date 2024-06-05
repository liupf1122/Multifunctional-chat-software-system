import requests
data={
    "refer_wav_path": "./reference_audio/这「七圣召唤」虽说是游戏，但对局之中也隐隐有策算谋略之理。.wav",
    "prompt_text": "这「七圣召唤」虽说是游戏，但对局之中也隐隐有策算谋略之理。",
    "prompt_language": "zh",
    "text": "宝贝，一起去吃饭吧！",
    "text_language": "zh",
    "custom_sovits_path": "./SoVITS_weights/keqing.pth",
    "custom_gpt_path": "./GPT_weights/keqing.ckpt"
}

response=requests.post("http://localhost:9880",json=data)
print("开始合成")
if(response.status_code==400):
    raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
with open("success.wav","wb") as f:
    f.write(response.content)
    print("合成成功！")

import winsound

print("开始播放")
filename = "success.wav"
winsound.PlaySound(filename, winsound.SND_FILENAME)
print("播放完成")