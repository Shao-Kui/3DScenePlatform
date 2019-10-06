import flask
from flask import Flask, request
from flask_cors import CORS
import orm
import json
import pdb
import os
# import smart_op
import base64
import re
from io import BytesIO
from PIL import Image
from rec_release import recommendation_ls_euclidean, fa_layout_pro
from flask import Flask,render_template,send_file,request
import uuid
from aip import AipSpeech
import librosa
from generate_descriptor import sketch_search


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app)


@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/")
def main():
    return flask.send_from_directory("static","index.html")

@app.route("/static/<fname>")
def send(fname):
    return flask.send_from_directory("static",fname)

@app.route("/objmeta/<obj>")
def objmeta(obj):
    m=orm.query_model_by_name(obj)
    if m is None:
        return json.dumps({})
    ret={"id":m.id,"name":m.name,"semantic":m.category.wordnetSynset,"thumbnail":"/thumbnail/%d/"%(m.id,)}
    if (m.format=="OBJ"):
        ret["mesh"]="/mesh/%s"%m.id
        ret["mtl"]="/mtl/%s"%m.id
        ret["texture"]="/texture/"
        return json.dumps(ret)

@app.route("/objmeta_by_id/<id>")
def objmeta_by_id(id):
    m=orm.query_model_by_id(id)
    ret={"id":m.id,"name":m.name,"semantic":m.category.wordnetSynset,"thumbnail":"/thumbnail/%d/"%(m.id,)}
    if (m.format=="OBJ"):
        ret["mesh"]="/mesh/%s"%m.id
        ret["mtl"]="/mtl/%s"%m.id
        ret["texture"]="/texture/"
        return json.dumps(ret)
@app.route("/mesh/<id>")
def mesh(id):
    m=orm.query_model_by_id(id)
    return flask.send_file(json.loads(m.resources)["mesh"])
@app.route("/thumbnail/<id>/<int:view>")
def thumbnail(id,view):
    m=orm.query_model_by_id(id)
    return flask.send_from_directory(os.path.join(".","suncg","objd20",m.name,"render20"),"render-%s-%d.png"%(m.name,view))
@app.route("/thumbnail/<id>")
def thumbnail_sk(id):
    m=orm.query_model_by_id(id)
    return flask.send_from_directory(os.path.join(".","suncg","object",m.name,"render20"),"render-%s-%d.png"%(m.name,10))
@app.route("/mtl/<id>")
def mtl(id):
    m=orm.query_model_by_id(id)
    return flask.send_file(json.loads(m.resources)["mtl"])

@app.route("/texture//<id>")
def texture(id):
    return flask.send_from_directory(os.path.join(".","suncg","texture"),id)
@app.route("/texture/<id>")
def texture_(id):
    return flask.send_from_directory(os.path.join(".","suncg","texture"),id)

@app.route("/query")
def textquery():
    kw=flask.request.args.get('kw', default = "", type = str) # keyword
    lo=flask.request.args.get('lo', default = 0, type = int) #
    hi=flask.request.args.get('hi', default = 20, type = int)
    models=orm.query_models(kw,(lo,hi))
    ret=[{"id":m.id,"name":m.name,"semantic":m.category.wordnetSynset,"thumbnail":"/thumbnail/%d"%(m.id,)} for m in models]
    return json.dumps(ret)

@app.route("/room/<houseid>/<roomid>")
def roominfo(houseid,roomid):
    structs={"c":"c.obj","w":"w.obj","f":"f.obj"}
    ret=[k for k in structs if os.path.isfile(os.path.join("suncg","room",houseid,roomid+structs[k]))]
    return json.dumps(ret)

@app.route("/room/<houseid>/<roomid>f.obj")
def floor(houseid,roomid):
    return flask.send_file(os.path.join("suncg","room",houseid,roomid+"f.obj"))
@app.route("/room/<houseid>/<roomid>w.obj")
def wall(houseid,roomid):
    return flask.send_file(os.path.join("suncg","room",houseid,roomid+"w.obj"))
@app.route("/room/<houseid>/<roomid>c.obj")
def ceil(houseid,roomid):
    return flask.send_file(os.path.join("suncg","room",houseid,roomid+"c.obj"))

@app.route("/room/<houseid>/<roomid>f.mtl")
def floor_mtl(houseid,roomid):
    return flask.send_file(os.path.join("suncg","room",houseid,roomid+"f.mtl"))
@app.route("/room/<houseid>/<roomid>w.mtl")
def wall_mtl(houseid,roomid):
    return flask.send_file(os.path.join("suncg","room",houseid,roomid+"w.mtl"))
@app.route("/room/<houseid>/<roomid>c.mtl")
def ceil_mtl(houseid,roomid):
    return flask.send_file(os.path.join("suncg","room",houseid,roomid+"c.mtl"))

@app.route("/set_scene_configuration", methods=['POST', 'GET'])
def set_scene_configuration():
    if request.method == 'POST':
        with open('./temp.json', 'w') as f:
            json.dump(request.json, f)
        return "POST scene configuration. "
    if request.method == 'GET':
        return "Do not support using GET to configurate scene. "

@app.route("/magic_position", methods=['POST', 'GET'])
def magic_position():
    objs = []
    if request.method == 'POST':
        for o in request.json["objList"]:
            if o is not None:
                objs.append(o)
        with open('./mp.json', 'w') as f:
            json.dump({"objList":objs, "translate": request.json["translate"]}, f)
        result = smart_op.find_category_and_rotate_given_placement("_",0,"_",objs,request.json["translate"])
        d = {'cat':result[0], 'rotate':[result[1][0], result[1][1], result[1][2]]}
        models=orm.query_models(result[0],(0,1))
        ret=[{"id":m.id,"name":m.name,"semantic":m.category.wordnetSynset,"thumbnail":"/thumbnail/%d"%(m.id,)} for m in models]
        if len(ret) == 0:
            return json.dumps({'valid':0})
        ret = ret[0]
        ret['rotate'] = d['rotate']
        ret['valid'] = 1
        return json.dumps(ret)
    if request.method == 'GET':
        return "Do not support using GET to using magic add. "

@app.route("/magic_category", methods=['POST', 'GET'])
def magic_category():
    objs = []
    if request.method == 'POST':
        for o in request.json["objList"]:
            if o is not None:
                objs.append(o)
        with open('./mp.json', 'w') as f:
            json.dump({"objList":objs, "category": request.json["category"], "origin": request.json["origin"], "modelId": request.json["modelId"]}, f)
        result = smart_op.find_placement_and_rotate_given_category(request.json["origin"], 0, request.json["modelId"], objs, request.json["category"], request.json["objectName"])
        d = {'translate':[result[0][0], result[0][1], result[0][2]], 'rotate':[result[1][0], result[1][1], result[1][2]]}
        return json.dumps(d)
    if request.method == 'GET':
        return "Do not support using GET to using magic add. "

@app.route("/sketch", methods=['POST', 'GET'])
def sketch():
    if request.method == 'POST':
        image_data = bytes(request.form.get('imgBase64'), encoding="ascii")
        imgdata = base64.b64decode(image_data)
        filename = './qs.png'
        with open(filename, 'wb') as f:
            f.write(imgdata)
        results = sketch_search('./qs.png',400)
        tmp = []
        for i in results:
            if i not in tmp:
                tmp.append(i)
                if len(tmp)>=20:
                    break
        results = tmp
        #print(tmp)
        print(results)

        results = orm.query_model_by_names(results)
        #print(results)
        ret=[{"id":m.id,"name":m.name,"semantic":m.category.wordnetSynset,"thumbnail":"/thumbnail/%d"%(m.id,)} for m in results]
        return json.dumps(ret)
    return "Post image! "

@app.route("/palette_recommendation", methods=['POST', 'GET'])
def palette_recommendation():
    if request.method == 'POST':
        rec_results = recommendation_ls_euclidean(request.json)
        result = []
        for item in rec_results:
            m = orm.query_model_by_name(item)
            ret = {"id":m.id,"name":m.name,"semantic":m.category.wordnetSynset,"thumbnail":"/thumbnail/%d"%(m.id,)}
            result.append(ret)
        print(result)
        return json.dumps(result)
    if request.method == 'GET':
        return "Do not support using GET to using recommendation. "

@app.route("/sklayout", methods=['POST', 'GET'])
def sklayout():
    if request.method == 'POST':
        return json.dumps(fa_layout_pro(request.json))
    if request.method == 'GET':
        return "Do not support using GET to using recommendation. "

@app.route('/toy_uploader', methods=['GET', 'POST'])
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
    y,sr = librosa.load(filename,sr=16000)
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

    print(result)
    os.remove(filename)
    return result

app.run(host="127.0.0.1",port=11425,debug=True)
