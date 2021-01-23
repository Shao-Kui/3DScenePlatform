from flask import Blueprint, request
import re
import uuid
from aip import AipSpeech
import librosa
import base64
import time
import datetime
import json
import os
import orm
# from generate_descriptor import sketch_search
from projection2d import objCatList, roomTypeDemo, objListCat, categoryRelation
import random

app_audio = Blueprint('app_audio', __name__)
audio_sketch_word = None
audio_sketch_eng = None
@app_audio.route("/sketchNaudio", methods=['POST', 'GET'])
def sketchNaudio():
    if request.method == 'POST':
        image_data = bytes(request.form.get('imgBase64'), encoding="ascii")
        imgdata = base64.b64decode(image_data)
        filename = './qs.png'
        with open(filename, 'wb') as f:
            f.write(imgdata)
        start_time = time.time()
        global audio_sketch_eng
        global audio_sketch_word
        if audio_sketch_word == '桌子':
            audio_sketch_eng = 'table'
        elif audio_sketch_word == '椅子':
            audio_sketch_eng = 'chair'
        elif audio_sketch_word == '办公椅':
            audio_sketch_eng = 'office_chair'
        elif audio_sketch_word == '扶手椅':
            audio_sketch_eng = 'armchair'
        elif audio_sketch_word == '长椅':
            audio_sketch_eng = 'bench_chair'
        elif audio_sketch_word == '书架':
            audio_sketch_eng = 'bookshelf'
        elif audio_sketch_word == '箱式凳':
            audio_sketch_eng = 'ottoman'
        elif audio_sketch_word == '橱柜':
            audio_sketch_eng = 'kitchen_cabinet'
        elif audio_sketch_word == "马桶":
            audio_sketch_eng = 'toilet'
        elif audio_sketch_word == '双人床':
            audio_sketch_eng = 'double_bed'
        elif audio_sketch_word == '单人床':
            audio_sketch_eng = 'single_bed'
        results = sketch_search('./qs.png', 400, audio_sketch_eng)
        end_time = time.time()
        tmp = []
        for i in results:
            if i not in tmp:
                tmp.append(i)
                if len(tmp) >= 50:
                    break
        results = tmp
        # print(tmp)
        print(results)

        results = orm.query_model_by_names(results)
        # print(results)
        ret = [
            {"id": m.id, "name": m.name, "semantic": m.category.wordnetSynset, "thumbnail": "/thumbnail/%d" % (m.id,)}
            for m in results]
        print("\r\n\r\n------- %s secondes --- \r\n\r\n" % (end_time - start_time))

        logger = {}
        logger['sketch_time'] = "-- %s secondes --" % (end_time - start_time)
        logger['sketch_t'] = (end_time - start_time)
        logger['audio_sketch_eng'] = audio_sketch_eng
        logger['audio_sketch_word'] = audio_sketch_word
        logger['ret'] = ret
        with open('./test/sketchtime/{}.json'.format(datetime.datetime.now().strftime('%y-%m-%d_%H-%M-%S')), 'w') as f:
            json.dump(logger, f)
        audio_sketch_eng = None
        audio_sketch_word = None
        return json.dumps(ret)
    return "Post image! "

@app_audio.route('/toy_uploader', methods=['GET', 'POST'])
def toy_uploader():
    uuid4 = uuid.uuid4()
    # 确保文件唯一，录音文件为 .wav 格式
    filename = f"{uuid4}.wav"
    # 保存语音文件
    print(request)
    print(request.files)
    request.files['record'].save(filename)
    # 开始语音转文字

    """ 你的 APPID AK SK """
    APP_ID = '17228695'
    API_KEY = 'pga4PIogoyENxqGvTlBljRau'
    SECRET_KEY = '2mmRMs2BwCPQi5BKprDGUgGAxD10VOAt'

    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
    # 读取文件
    y, sr = librosa.load(filename, sr=16000)
    y = librosa.to_mono(y)
    import soundfile
    soundfile.write(filename, y, sr, subtype='PCM_16')

    print(filename)

    def get_file_content(filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()

    # 识别本地文件

    result = client.asr(get_file_content(filename), 'wav', 16000, {
        'dev_pid': 1536,
    })
    global audio_sketch_word
    global audio_sketch_eng
    if 'result' in result:
        audio_sketch_word = result['result'][0]

    print(audio_sketch_word)
    # os.remove(filename)
    return json.dumps(result)

@app_audio.route('/audio_categoryObj/<catname>')
def audio_categoryObj(catname):
    res = {}
    res['modelId'] = random.choice(objListCat[catname])
    return json.dumps(res)
