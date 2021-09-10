var reco = null;

navigator.getUserMedia = (navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia);

navigator.getUserMedia({audio: true}, create_stream, function (err) {
    console.log(err)
});

function create_stream(user_media) {
    var audio_context = new AudioContext();
    var stream_input = audio_context.createMediaStreamSource(user_media);
    reco = new Recorder(stream_input);
    // reco = new Recorder({
    //     sampleRate: 16000, //采样频率，默认为44100Hz(标准MP3采样率)
    //     bitRate: 128, //比特率，默认为128kbps(标准MP3质量)
    //     success: function(){ //成功回调函数
    //     },
    //     error: function(msg){ //失败回调函数
    //     },
    //     fix: function(msg){ //不支持H5录音回调函数
    //     }
    // });
}

function start_reco() {
    console.log('start recording')
    $("#audio_error").hide()
    $("#audio_ok").hide()
    $("#audio_processing").hide()
    $("#start_record_button").hide();
    $("#stop_record_button").show();
    reco.record();
}

function stop_reco() {
    reco.stop();
    $("#start_record_button").show();

    $("#stop_record_button").hide();
    console.log('stop recording')
}

const requestAudioObject = function(data){
    console.log(`time requires: ${moment.duration(new moment().diff(startTime)).asSeconds()}s`)
    console.log(data)
    if(data.rawText.includes('删')){
        removeIntersectObject();
        toggles();
    }
    if(data.parsed[0][0] !== undefined){
    if(data.parsed[0][0].length >= 2){
        if(currentRoomId === undefined) return; 
        let englishCategory = ""; 
        switch(data.parsed[0][0][0]){
            case '床':
                englishCategory = "King-size Bed";
                break;
            case '双人床':
                englishCategory = "King-size Bed";
                break;
            case '床头柜':
                englishCategory = "Nightstand";
                break;
            case '桌子':
                englishCategory = "Dining Table"; 
                break;
            case '餐桌':
                englishCategory = "Dining Table"; 
                break;
            case '茶几':
                englishCategory = "Coffee Table"; 
                break;
            case '梳妆台':
                englishCategory = "Dressing Table"; 
                break;
            case '软凳':
                englishCategory = "Footstool&nbsp;&frasl;&nbsp;Sofastool&nbsp;&frasl;&nbsp;Bed&nbsp;End&nbsp;Stool&nbsp;&frasl;&nbsp;Stool"; 
                break;
            case '床凳':
                englishCategory = "Footstool&nbsp;&frasl;&nbsp;Sofastool&nbsp;&frasl;&nbsp;Bed&nbsp;End&nbsp;Stool&nbsp;&frasl;&nbsp;Stool"; 
                break;
            case '书桌':
                englishCategory = "Desk"; 
                break;
            case '椅子':
                englishCategory = "Dining Chair"; 
                break;
            default:
                englishCategory = "Desk"; 
                break;
        }
        $.getJSON(`/audio_categoryObj/${englishCategory}`, async data => {
            await loadObjectToCache(data.modelId);
            await auxiliaryRoom(); 
            var timeout = setInterval(function() {
                console.log('checking... ... ...')
                if(data.modelId in objectCache && 'auxiliaryDomObj' in manager.renderManager.scene_json.rooms[currentRoomId]) {
                    let rm = tf.tensor(manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj.room_meta); 
                    let xz = rm.mean(axis=0).arraySync(); 
                    addObjectFromCache(
                        modelId=data.modelId,
                        transform={
                            'translate': [xz[0], 0, xz[1]], 
                            'rotate': [0, 0, 0],
                            'scale': [1, 1, 1]
                        }
                    );
                    clearInterval(timeout); 
                }
            }, 100);
        });
    }}
    reco.clear();
}
let startTime;
const audioToText = function(){
    startTime = new moment();
    reco.exportWAV(wav_file => {
        let formdata = new FormData();
        formdata.append("record", wav_file);
        console.log(wav_file);
        reco.clear();
        $.ajax({
            url: "/voice",
            type: "post",
            processData: false,
            contentType: false,
            data: formdata,
            dataType: 'json',
            success: requestAudioObject
        })
    });

};

function get_audio() {
    console.log('submitting audio')
    $("#audio_processing").show()
    reco.exportWAV(function (wav_file) {
        // wav_file = Blob对象 file对象
        // ws.send(wav_file);
        var formdata = new FormData();
        formdata.append("record", wav_file);

        // formdata.append("sender", toy_id);
        // formdata.append("to_user", document.getElementById("from_user").innerText);
        $.ajax({
            url: "/toy_uploader",  // ⚠️
            type: 'post',
            processData: false,
            contentType: false,
            data: formdata,
            dataType: 'json',
            success: function (data) {
                console.log(data);
                $("#audio_processing").hide()
                if (data.err_msg!="success."){
                    $("#audio_error").text(data.err_msg)
                    $("#audio_error").show()
                    $("#audio_ok").hide()

                }else {
                    $("#searchinput").val(data.result[0])
                    $("#audio_error").hide()
                    $("#audio_ok").show()
                    while(catalogItems.firstChild){
                        catalogItems.firstChild.remove();
                    }
                    var dataURL = drawingCanvas.toDataURL();
                    dataURL = dataURL.split(',')[1]
                    $.ajax({
                        type: "POST",
                        url: "/sketchNaudio",
                        data: {
                            imgBase64: dataURL
                        }
                    }).done(function(o) {
                        searchResults = JSON.parse(o);
                        searchResults.forEach(function(item){
                        var iDiv = document.createElement('div');
                            iDiv.className = "catalogItem";
                            iDiv.style.backgroundImage = "url(" + item.thumbnail + ")";
                            iDiv.setAttribute('objectID', item.id);
                            iDiv.setAttribute('objectName', item.name);
                            iDiv.setAttribute('semantic', item.semantic);
                            iDiv.addEventListener('click', clickCatalogItem)
                            catalogItems.appendChild(iDiv);
                        })
                    });
                }
            }
        })
    })
    reco.clear();
}