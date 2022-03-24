import eventlet
eventlet.monkey_patch()
import flask
from flask_cors import CORS
# import orm
import json
import os
import base64
import time
import datetime
# from rec_release import fa_reshuffle
from layoutmethods.autolayoutv2 import sceneSynthesis
# from layoutmethods.layout1 import fa_layout_pro
from layoutmethods.planit.method import roomSynthesis as roomSynthesisPlanIT
from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room
import uuid
from sketch_retrieval.generate_descriptor import sketch_search,sketch_search_non_suncg
from main_audio import app_audio
from main_magic import app_magic
from autoview import app_autoView, autoViewsRes, autoViewRooms
import random
from subprocess import check_output
import difflib
import sk

app = Flask(__name__, template_folder='static')
app.register_blueprint(app_audio)
app.register_blueprint(app_magic)
app.register_blueprint(app_autoView)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'Ghost of Tsushima. '
CORS(app)
socketio = SocketIO(app, manage_session=False, cors_allowed_origins="*")

with open('./latentspace/obj-semantic.json') as f:
    obj_semantic = json.load(f)

@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/")
def main():
    now = datetime.datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H-%M-%S")
    print(request.remote_addr, dt_string)
    return flask.render_template("index.html", onlineGroup="OFFLINE")

@app.route("/static/<fname>")
def send(fname):
    return flask.send_from_directory("static", fname)

@app.route("/mesh/<name>")
def mesh(name):
    # m = orm.query_model_by_id(id)
    # return flask.send_file(json.loads(m.resources)["mesh"])
    objDir = f'./dataset/object/{name}/{name}.obj'
    if os.path.exists(objDir):
        return flask.send_file(objDir)
    else:
        return ""

@app.route("/thumbnail/<name>")
def thumbnail_sk(name):
    # m = orm.query_model_by_id(id)
    # return flask.send_from_directory(os.path.join(".", "dataset", "object", m.name, "render20"), "render-%s-%d.png" % (m.name, 10))
    return flask.send_from_directory(os.path.join(".", "dataset", "object", name, "render20"), "render-%s-%d.png" % (name, 10))

@app.route("/mtl/<name>")
def mtl(name):
    mtlDir = f'./dataset/object/{name}/{name}.mtl'
    if os.path.exists(mtlDir):
        return flask.send_file(mtlDir)
    else:
        return ""

@app.route("/texture//<id>")
def texture(id):
    return flask.send_from_directory(os.path.join(".", "dataset", "texture"), id)

@app.route("/texture/<id>")
def texture_(id):
    return flask.send_from_directory(os.path.join(".", "dataset", "texture"), id)

@app.route("/texture/maps/<id>")
def texture_maps(id):
    return flask.send_file(f"./dataset/texture/maps/{id}")

"""
@app.route("/thumbnail/<id>/<int:view>")
def thumbnail(id, view):
    m = orm.query_model_by_id(id)
    return flask.send_from_directory(os.path.join(".", "dataset", "objd20", m.name, "render20"),
                                     "render-%s-%d.png" % (m.name, view))

@app.route("/objmeta/<obj>")
def objmeta(obj):
    m = orm.query_model_by_name(obj)
    if m is None:
        return json.dumps({})
    ret = {"id": m.id, "name": m.name, "semantic": m.category.wordnetSynset, "thumbnail": "/thumbnail/%d/" % (m.id,)}
    if (m.format == "OBJ"):
        ret["mesh"] = "/mesh/%s" % m.id
        ret["mtl"] = "/mtl/%s" % m.id
        ret["texture"] = "/texture/"
        return json.dumps(ret)

@app.route("/objmeta_by_id/<id>")
def objmeta_by_id(id):
    m = orm.query_model_by_id(id)
    ret = {"id": m.id, "name": m.name, "semantic": m.category.wordnetSynset, "thumbnail": "/thumbnail/%d/" % (m.id,)}
    if (m.format == "OBJ"):
        ret["mesh"] = "/mesh/%s" % m.id
        ret["mtl"] = "/mtl/%s" % m.id
        ret["texture"] = "/texture/"
        return json.dumps(ret)

@app.route("/query")
def textquery():
    kw=flask.request.args.get('kw', default = "", type = str) # keyword
    lo=flask.request.args.get('lo', default = 0, type = int) #
    hi=flask.request.args.get('hi', default = 100, type = int)
    models=orm.query_models(kw,(lo,hi))
    modelofid = orm.query_model_by_name(kw)
    if modelofid is not None:
        models.append(modelofid)
    ret=[{"id":m.id,"name":m.name,"semantic":m.category.wordnetSynset,"thumbnail":f"/thumbnail/{m.name}"} for m in models]
    if os.path.exists(f'./dataset/object/{kw}/{kw}.obj'):
        ret.append({
            "id": -1,
            "name": kw,
            "semantic": 'currentlyUnknown',
            "thumbnail":f"/thumbnail/{kw}"})
    return json.dumps(ret)
"""

with open('./dataset/ChineseMapping.json', encoding='utf-8') as f:
    ChineseMapping = json.load(f)
@app.route("/query2nd")
def query2nd():
    ret = []
    kw = flask.request.args.get('kw', default = "", type = str) # keyword
    num = flask.request.args.get('num', default = 20, type = int) # keyword
    if os.path.exists(f'./dataset/object/{kw}/{kw}.obj'):
        ret.append({"name": kw, "semantic": sk.getobjCat(kw), "thumbnail":f"/thumbnail/{kw}"})
    catMatches = difflib.get_close_matches(kw, list(ChineseMapping.keys()), 1)
    if len(catMatches) != 0:
        cat = ChineseMapping[catMatches[0]]
        print(f'get query: {cat}. ')
        random.shuffle(sk.objListCat[cat])
        if len(sk.objListCat[cat]) >= num:
            modelIds = sk.objListCat[cat][0:num]
        else:
            modelIds = sk.objListCat[cat]
        ret += [{"name":modelId, "semantic":cat, "thumbnail":f"/thumbnail/{modelId}"} for modelId in modelIds]
    modelIdlist = kw.split(';')
    for modelId in modelIdlist:
        if os.path.exists(f'./dataset/object/{modelId}/{modelId}.obj'):
            ret.append({"name": modelId, "semantic": sk.getobjCat(modelId), "thumbnail":f"/thumbnail/{modelId}"})
    if kw == '骁逸':
        xiaoyiids1 = ['bed', 'cabinet', 'cabinet1', 'chair', 'Chest of drawer', 'ClassicKitchenChair2', 
        'ClassicRoundTable1', 'CoffeeMaker', 'Cutlery Prefab', 'diining_furnitures_29__vray', 'DiningTable', 'DiningTable_006', 
        'DiningTable_007', 'FanV2', 'FridgeSBS', 'kitchen_shelf', 'lamp', 'lamp1', 'Lamp_ON', 'laptop', 'MicrowaveOven', 'mirror', 
        'Mixer', 'modular_kitchen_table', 'PlateWithFruit', 'projector', 'rack', 'RTChair_low', 'shower', 'sofa', 'sofa_large', 
        'sofa_small', 'speaker', 'Stove', 'Stovetop', 'table', 'table1', 'TableAngular', 'Table_Black', 'Table_original', 
        'Table_White', 'toilet', 'Trash', 'tv', 'tv_table', 'wall_lighter', 'washbasin', 'Washer', 'word_table', 'work_chair']
        ret += [{"name":modelId, "semantic": 'Unknown', "thumbnail":f"/thumbnail/{modelId}"} for modelId in xiaoyiids1]
    if kw == '灰色现代风':
        greyMordenStyle = ['2624','1456','1138','3740','6129','8829','6855','7735','2715','3088','7209,1394','1806','5933','3232','4455',
        '5253','6096','1993','8983','10198','10855','2043','9767','8185','5010','7763','10414','1830','1288','10053','5218','10480','9018',
        '8760','2560','3585','9886','4522','10952','2504','3337','1023','2611','3911','10364','6892','3163','9112','6824','7781']
        ret += [{"name":modelId, "semantic": 'Unknown', "thumbnail":f"/thumbnail/{modelId}"} for modelId in greyMordenStyle]
    if kw == 'cgs' or kw == 'CGS':
        cgseriesDom = os.listdir('./layoutmethods/cgseries')
        ret += [{"name":modelId, "semantic": 'Unknown', "thumbnail":f"/thumbnail/{modelId}"} for modelId in cgseriesDom]
    if kw == 'CGS-床':
        ret += [{"name":modelId, "semantic": 'Unknown', "thumbnail":f"/thumbnail/{modelId}"} for modelId in ['1034','1040','1050',
        '1217','1238','1262','1305','1397','1409','1526','1677','3169','4338','4478','4912','5010','5259','5312','5608','6200','6313',
        '9226','9416','9778']]
    if kw == 'CGS-茶几':
        ret += [{"name":modelId, "semantic": 'Unknown', "thumbnail":f"/thumbnail/{modelId}"} for modelId in ['1023','1025','1049',
        '1240','1359','1394','1484','1806','1830','1908','10126','10198','10216','10487','10909','2624','2919','4314',
        '5933','7644','7896','8493','9532']]
    if kw == 'CGS-餐桌':
        ret += [{"name":modelId, "semantic": 'Unknown', "thumbnail":f"/thumbnail/{modelId}"} for modelId in ['1041','1133','1198','1993'
        ,'10568','2096','3118','3429','4839','6824','8983','9363','9704']]
    return json.dumps(ret)

ROOMDIR = "room2021"

@app.route("/room/<houseid>/<roomid>")
def roominfo(houseid, roomid):
    structs = {"c": "c.obj", "w": "w.obj", "f": "f.obj"}
    ret = [k for k in structs if os.path.isfile(os.path.join("dataset", ROOMDIR, houseid, roomid + structs[k]))]
    if(len(ret) == 0):
        ret = [k for k in structs if os.path.isfile(os.path.join("dataset", "room", houseid, roomid + structs[k]))]
    return json.dumps(ret)

@app.route("/room/<houseid>/<roomid>f.obj")
def floor(houseid, roomid):
    p = os.path.join("dataset", ROOMDIR, houseid, roomid + "f.obj")
    if os.path.isfile(p):
        return flask.send_file(p)
    p = os.path.join("dataset", "room", houseid, roomid + "f.obj")
    if os.path.isfile(p):
        return flask.send_file(p)
    return ""

@app.route("/room/<houseid>/<roomid>w.obj")
def wall(houseid, roomid):
    p = os.path.join("dataset", ROOMDIR, houseid, roomid + "w.obj")
    if os.path.isfile(p):
        return flask.send_file(p)
    p = os.path.join("dataset", "room", houseid, roomid + "w.obj")
    if os.path.isfile(p):
        return flask.send_file(p)
    return ""

@app.route("/room/<houseid>/<roomid>c.obj")
def ceil(houseid, roomid):
    p = os.path.join("dataset", ROOMDIR, houseid, roomid + "c.obj")
    if os.path.isfile(p):
        return flask.send_file(p)
    p = os.path.join("dataset", "room", houseid, roomid + "c.obj")
    if os.path.isfile(p):
        return flask.send_file(p)
    return ""

@app.route("/GeneralTexture/<imgname>")
def GeneralTexture(imgname):
    return flask.send_file(f'./dataset/GeneralTexture/{imgname}')

@app.route("/manyTextures")
def manyTextures():
    res = []
    for imgname in os.listdir('./dataset/GeneralTexture'):
        res.append({
            'imgpath': f'/GeneralTexture/{imgname}'
        })
    return json.dumps(res)

@app.route("/room/<houseid>/<roomid>f.mtl")
def floor_mtl(houseid, roomid):
    return flask.send_file(os.path.join("dataset", ROOMDIR, houseid, roomid + "f.mtl"))

@app.route("/room/<houseid>/<roomid>w.mtl")
def wall_mtl(houseid, roomid):
    return flask.send_file(os.path.join("dataset", ROOMDIR, houseid, roomid + "w.mtl"))

@app.route("/room/<houseid>/<roomid>c.mtl")
def ceil_mtl(houseid, roomid):
    return flask.send_file(os.path.join("dataset", ROOMDIR, houseid, roomid + "c.mtl"))

@app.route("/set_scene_configuration", methods=['POST', 'GET'])
def set_scene_configuration():
    if request.method == 'POST':
        with open('./temp.json', 'w') as f:
            json.dump(request.json, f)
        return "POST scene configuration. "
    if request.method == 'GET':
        return "Do not support using GET to configurate scene. "

@app.route("/sketch", methods=['POST', 'GET'])
def sketch():
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        if '&' in keyword:
            k = int(keyword.split('&')[1])
            keyword = keyword.split('&')[0]
        else:
            k = 20
        if keyword == 'unknown' or keyword == '' or keyword not in ChineseMapping:
            keyword = None
        else:
            keyword = ChineseMapping[keyword]
        image_data = bytes(request.form.get('imgBase64'), encoding="ascii")
        imgdata = base64.b64decode(image_data)
        filename = './qs.png'
        with open(filename, 'wb') as f:
            f.write(imgdata)
        if keyword is None:
            results = sketch_search('./qs.png', k=k)
        else:
            results = sketch_search_non_suncg('./qs.png', k=k, classname=keyword)
        ret = [{"name":modelId, "semantic": sk.getobjCat(modelId), "thumbnail":f"/thumbnail/{modelId}"} for modelId in results]
        return json.dumps(ret)
    return "Post image! "

# Audio Module. 
'''
from layoutmethods import parse
from layoutmethods import speechRec as spr
L = parse.LanguageAnalysis()
@app.route("/voice", methods=['POST'])
def voice():
    uuid4 = uuid.uuid4()
    filename = f"./layoutmethods/audio/{uuid4}.wav"
    pcmfilename = filename.replace('.wav', '.pcm')
    request.files['record'].save(filename)
    c = f'ffmpeg -y -i {filename} -acodec pcm_s16le -f s16le -ac 1 -ar 16000 {pcmfilename}'
    check_output(c, shell=True)
    res = {}
    start_time = time.time()
    print(spr.audiofile_rec(pcmfilename))
    res['rawText'] = " ".join(spr.audiofile_rec(pcmfilename)['result'])
    print(time.time() - start_time)
    res['parsed'] = L.parserText(res['rawText'])
    try:
        adding = res['parsed'][0][0][0]
    except:
        adding = 'unknown'
    if adding in ChineseMapping:
        res['cat'] = ChineseMapping[adding]
    else:
        res['cat'] = 'unknown'
    return json.dumps(res)
'''

@app.route("/sklayout", methods=['POST', 'GET'])
def sklayout():
    if request.method == 'POST':
        return json.dumps(sceneSynthesis(request.json))
    if request.method == 'GET':
        return "Do not support using GET to using recommendation. "

# @app.route("/layout1", methods=['POST', 'GET'])
# def layout1():
#     if request.method == 'POST':
#         return json.dumps(fa_layout_pro(request.json))

@app.route("/planit", methods=['POST'])
def planit():
    res = roomSynthesisPlanIT(request.json)
    roomId = request.json['roomId']
    if res is None:
        res = request.json
    else:
        res['roomId'] = roomId
        for o in res['objList']:
            o['roomId'] = roomId
    return json.dumps(res)

@app.route("/reshuffle", methods=['POST', 'GET'])
def reshuffle():
    if request.method == 'POST':
        return json.dumps(request.json)
    if request.method == 'GET':
        return "Do not support using GET to using recommendation. "

@app.route("/semantic/<obj_id>")
def semantic(obj_id):
    return obj_semantic[obj_id]

# https://icon-icons.com/icon/audience-theater-scene-curtains/54210
@app.route('/favicon.ico') 
def favicon(): 
    return flask.send_from_directory('static', 'iconfinder-stagingsite-4263528_117848.ico', mimetype='image/vnd.microsoft.icon')

onlineScenes = {}

import atexit
# defining function to run on shutdown
def save_online_scenes():
    for groupName in onlineScenes:
        with open(f'./examples/onlineScenes/{groupName}.json', 'w') as f:
            json.dump(onlineScenes[groupName], f)
# Register the function to be called on exit
atexit.register(save_online_scenes)

@app.route("/applyuuid")
def applyuuid():
    return str(uuid.uuid4())

@app.route("/getSceneJsonByID/<origin>")
def getSceneJsonByID(origin):
    if os.path.exists(f'./dataset/Levels2021/{origin}.json'):
        return flask.send_file(f'./dataset/Levels2021/{origin}.json')
    else:
        return ""

def generateObjectsUUIDs(sceneJson):
    # generate wall height: 
    for room in sceneJson['rooms']:
        try:
            sceneJson['coarseWallHeight'] = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
            break
        except:
            continue
    # standardize roomids & generate uuid for each object: 
    for room,roomId in zip(sceneJson['rooms'], range(len(sceneJson['rooms']))):
        room['roomId'] = roomId
        for obj in room['objList']:
            if obj is None:
                continue
            obj['roomId'] = roomId
            obj['key'] = str(uuid.uuid4())
    return sceneJson

def loadOnlineGroup(groupName):
    if groupName not in onlineScenes:
        # if the server has already saved the cached scenes:  
        if os.path.exists(f'./examples/onlineScenes/{groupName}.json'):
            try:
                with open(f'./examples/onlineScenes/{groupName}.json') as f:
                    onlineScenes[groupName] = json.load(f)
            except:
                with open('./examples/initth.json') as f:
                    onlineScenes[groupName] = json.load(f)
            onlineScenes[groupName] = generateObjectsUUIDs(onlineScenes[groupName]) 
            print('Returned the Cached Scene. ')
        else:
            with open('./examples/initth.json') as f:
                onlineScenes[groupName] = json.load(f)
            onlineScenes[groupName] = generateObjectsUUIDs(onlineScenes[groupName])

@app.route("/groupPreview/<groupName>", methods=['GET'])
def groupPreview(groupName):
    loadOnlineGroup(groupName)
    origin = onlineScenes[groupName]['origin']
    mapDir = f'./sceneviewer/results/{origin}/showPcamInset2.png'
    if os.path.exists(mapDir):
        return flask.send_file(mapDir)
    else:
        return flask.send_file(f'./dataset/alilevel_door2021_orth/{origin}.png')

@app.route("/online/<groupName>", methods=['GET', 'POST'])
def onlineMain(groupName):
    if request.method == 'POST':
        loadOnlineGroup(groupName)
        return json.dumps(onlineScenes[groupName])
    now = datetime.datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H-%M-%S")
    if 'userID' in session:
        serverGivenUserID = session['userID']
    else:
        serverGivenUserID = str(uuid.uuid4())
        session['userID'] = serverGivenUserID
    print(request.remote_addr, dt_string, groupName)
    print('UserID: ', session['userID'])
    return flask.render_template("index.html", onlineGroup=groupName, serverGivenUserID=serverGivenUserID)

@socketio.on('join')
def on_join(groupName):
    join_room(groupName)
    session['groupName'] = groupName
    if 'userID' in session:
        emit('join', ('A person has entered the room. ', session['userID']), room=groupName)
    else:
        emit('join', ('A person has entered the room. ', 'An unknown User'), room=groupName)

@socketio.on('message')
def message(data):
    print('Received a sent message: ', data)
@socketio.on('connect')
def connect():
    print('Connected with ', request.remote_addr, datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")) # , 'UserID: ', session['userID']
    emit('connect', ('Welcome to the Server of Shao-Kui. ', datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")), to=request.sid)
@socketio.on('disconnect')
def disconnect():
    print('Disconnected with ', request.remote_addr)

@socketio.on('sktest')
def sktest(data):
    print('sktest from: ', request.remote_addr, '- goes: ', data)

@socketio.on('onlineSceneUpdate')
def onlineSceneUpdate(sceneJson, groupName): 
    if groupName not in onlineScenes:
        emit('onlineSceneUpdate', {'error': "No Valid Group Is Found. "}, room=groupName) 
        return
    onlineScenes[groupName] = sceneJson

@socketio.on('onlineSceneUpdateUnity')
def onlineSceneUpdateUnity(_json):
    sceneJson = json.loads(_json['sceneJson'])
    groupName = _json['groupName']
    if groupName not in onlineScenes:
        emit('onlineSceneUpdate', {'error': "No Valid Group Is Found. "}, room=groupName) 
        return
    onlineScenes[groupName] = sceneJson

@socketio.on('sceneRefresh')
def sceneRefresh(sceneJson, groupName):
    if 'origin' not in sceneJson or 'rooms' not in sceneJson:
        print('Invalid scene-refresh .json file. ')
        return
    onlineScenes[groupName] = generateObjectsUUIDs(sceneJson)
    emit('sceneRefresh', onlineScenes[groupName], room=groupName, include_self=True)

@socketio.on('functionCallUnity')
def functionCallUnity(theJson): 
    fname = theJson['fname']
    arguments = json.loads(theJson['arguments'])
    groupName = theJson['groupName']
    # if fname != 'animateObject3DOnly':
    #     print(theJson['arguments'])
    #     print(fname, arguments, groupName)
    if groupName not in onlineScenes:
        emit('functionCall', {'error': "No Valid Scene Is Found. "}, room=groupName) 
        return
    emit('functionCall', (fname, arguments), room=groupName, include_self=False) 

@socketio.on('functionCall')
def functionCall(fname, arguments, groupName): 
# def functionCall(fname, arguments): 
    # currently, we only allow a user exists in a single room; 
    # if fname != 'animateObject3DOnly':
    #     print(fname, arguments, groupName)
    if groupName not in onlineScenes:
        emit('functionCall', {'error': "No Valid Scene Is Found. "}, room=groupName) 
        return
    emit('functionCall', (fname, arguments), room=groupName, include_self=False) 
    if fname == 'addObjectByUUID':
        emit('functionCallUnity', ({
            'fname': 'addObjectByUUID',
            'uuid': arguments[0],
            'modelId': arguments[1],
            'roomID': arguments[2],
            'transform': arguments[3]
        }), room=groupName, include_self=False)
    if fname == 'removeObjectByUUID':
        emit('functionCallUnity', ({
            'fname': 'removeObjectByUUID',
            'uuid': arguments[0]
        }), room=groupName, include_self=False)
    if fname == 'transformObjectByUUID':
        emit('functionCallUnity', ({
            'fname': 'transformObjectByUUID',
            'uuid': arguments[0],
            'transform': arguments[1],
            'roomID': arguments[2]
        }), room=groupName, include_self=False)
    if fname == 'animateObject3DOnly':
        emit('functionCallUnity', ({
            'fname': 'animateObject3DOnly',
            'transformations': arguments[0]
        }), room=groupName, include_self=False)
    if fname == 'refreshRoomByID':
        emit('functionCallUnity', ({
            'fname': 'refreshRoomByID',
            'roomId': arguments[0],
            'objList': arguments[1]
        }), room=groupName, include_self=False)

object3DControlledByList = {}
@socketio.on('claimControlObject3D')
def claimControlObject3D(userID, objKey, isRelease, groupName):
    # print(userID, objKey, isRelease, groupName)
    if not isRelease:
        if objKey in object3DControlledByList:
            return
        object3DControlledByList[objKey] = userID
        emit('claimControlObject3D', (objKey, isRelease, userID), room=groupName, include_self=True)
    else:
        if objKey in object3DControlledByList:
            del object3DControlledByList[objKey]
        emit('claimControlObject3D', (objKey, isRelease, None), room=groupName, include_self=True)

@socketio.on('autoView')
def autoViewBySocket(scenejson, groupName):
    print(f'received autoview request from {request.sid}')
    autoViewAsync(scenejson, request.sid)

def autoViewAsync(scenejson, to):
    origin = scenejson['origin']
    if os.path.exists(f'./latentspace/autoview/{origin}'):
        socketio.emit('autoView', autoViewsRes(origin), to=to)
        return
    else:
        thread = sk.BaseThread(
            name='autoView',
            target=autoViewRooms,
            method_args=(scenejson,False),
            callback=autoViewAsync,
            callback_args=(scenejson, to)
        )
        thread.start()

if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=11425, threads=8)
    socketio.run(app, host="0.0.0.0", port=11425)

    # app.run(host="0.0.0.0", port=11425, debug=True, threaded=True)
    # from gevent import pywsgi
    # server = pywsgi.WSGIServer(('0.0.0.0', 11425), app)
    # server.serve_forever()
