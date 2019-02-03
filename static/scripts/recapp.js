window.onload = function() {

    //enable the predict button to contact the flask server and execute predictions
    var accuracy = document.getElementById("accuracy"); //update the inner html with the response of a train
    var train = document.getElementById("trainButton");
    train.addEventListener("click", trainFunc);
    //when button pressed, call trainFunc to send ajax,
    function trainFunc(){
        //Send a GET request to train the model, then retrieve a message and model accuracy
        $.ajax({
            url: '/train',
            type: 'GET',
            contentType: false,
            cache: false,
            success: function(data){
                console.log("[client] train success: \n",data.message);
                accuracy.innerHTML = data.model_accuracy;
            },
            error: function(e) {
                console.log("[client] error train: \n", e);
            }
        });

    }

    //webkitURL is deprecated but nevertheless
    URL = window.URL || window.webkitURL;

    var gumStream; 						//stream from getUserMedia()
    var rec; 							//Recorder.js object
    var input; 							//MediaStreamAudioSourceNode we'll be recording

    // shim for AudioContext when it's not avb.
    var AudioContext = window.AudioContext || window.webkitAudioContext;
    var audioContext //audio context to help us record

    var recordButton = document.getElementById("recordButton");
    var stopButton = document.getElementById("stopButton");

    //add events to those 2 buttons
    recordButton.addEventListener("click", startRecording);
    stopButton.addEventListener("click", stopRecording);

    function startRecording() {
        console.log("recordButton clicked");

        /*
            Simple constraints object, for more advanced audio features see
            https://addpipe.com/blog/audio-constraints-getusermedia/
        */

        var constraints = { audio: true, video:false }

        /*
            Disable the record button until we get a success or fail from getUserMedia()
        */

        recordButton.disabled = true;
        stopButton.disabled = false;

        /*
            We're using the standard promise based getUserMedia()
            https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
        */

        navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
            console.log("getUserMedia() success, stream created, initializing Recorder.js ...");

            /*
                create an audio context after getUserMedia is called
                sampleRate might change after getUserMedia is called, like it does on macOS when recording through AirPods
                the sampleRate defaults to the one set in your OS for your playback device

            */
            audioContext = new AudioContext();

            //inform the user about their browser and machine's capabilities
            document.getElementById("capable").innerHTML="Found: 1 channel pcm @ sample rate of "+audioContext.sampleRate/1000+"kHz"

            /*  assign to gumStream for later use  */
            gumStream = stream;

            /* use the stream */
            input = audioContext.createMediaStreamSource(stream);

            /*
                Create the Recorder object and configure to record mono sound (1 channel)
                Recording 2 channels  will double the file size
            */
            rec = new Recorder(input,{numChannels:1})

            //start the recording process
            rec.record()

            console.log("Recording: timer started");

            //Restrict the recording time to about less than 1 second
            setTimeout(function(){console.log("Recording: time up"); stopRecording();}, 1000);

        }).catch(function(err) {
            //enable the record button if getUserMedia() fails
            recordButton.disabled = false;
            stopButton.disabled = true;
        });
    }

    function stopRecording() {
        console.log("stopButton clicked");

        //disable the stop button, enable the record too allow for new recordings
        stopButton.disabled = true;
        recordButton.disabled = false;

        //tell the recorder to stop the recording
        rec.stop();

        //stop microphone access
        gumStream.getAudioTracks()[0].stop();

        //create the wav blob and pass it on to createDownloadLink
        rec.exportWAV(AudioAndUpload);
    }

    function AudioAndUpload(blob) {
        //prepare audio for html by creating a <audio> and <li> element
        var audioUrl = URL.createObjectURL(blob);
        var au = document.createElement('audio');
        var clipContainer = document.createElement('li');

        //add audio and controls to the html <audio> element
        au.controls = true;
        au.src = audioUrl;
        clipContainer.appendChild(au);

        //prepare audio name, delete, predict, & result for html <li>
        var deleteButton = document.createElement('button');
        var name = document.createElement('p');
        var predictButton = document.createElement('button');
        var predictResult = document.createElement('p');

        deleteButton.className = "clips";
        predictButton.className = "clips";

        deleteButton.innerHTML = "Delete";
        var clipName = new Date().toISOString();
        name.innerHTML = ' ' + clipName + '<br>';
        predictButton.innerHTML = "Predict";
        predictResult.innerHTML = '  Label:' + '...' + '   Predicted:' + '...'; //initialize the prediction results



        //add the name and fields to the html <li>
        clipContainer.appendChild(deleteButton);
        clipContainer.appendChild(name);
        //clipContainer.appendChild(document.createTextNode(clipName+".wav ")); //createTextNode is more consistent than innerHTML: https://stackoverflow.com/questions/13122760/is-there-any-major-difference-between-innerhtml-and-using-createtextnode-to-fill
        clipContainer.appendChild(predictButton);
        clipContainer.appendChild(predictResult);

        //add the li element to the ol
        recordingsList.appendChild(clipContainer);

        //ask the person to label their sample
        var smpLabel = prompt("Tell us what label you've recorded: '0' or '1'");


        //upload audio to server automatically
        console.log("[client] automatic jQuery ajax start");
        var file = new File([blob], clipName+'.wav', {type : 'audio/ogg' }); //When made from blob, file holds correct audio content

        if (!file) {
            console.log("[client] no file!")
            return;
        }

        var form = new FormData();
        form.append('file', file);
        //form.append('clipName', 'clipName'); //<---------
        //form.append('smpLabel', 'smpLabel'); //<---------
        $.ajax({
            type: "POST",
            enctype: 'multipart/form-data',
            url: "/upload",
            data: form,
            processData: false,
            contentType: false,
            cache: false,
            success: function (form) {
                //$("#result").text(form);
                console.log("[client] file uploaded: \n",form);
            },
            error: function (e) {
                //$("#result").text(e.responseText);
                console.log("[client] error upload: \n",e);
            }
        });
        console.log("[client] automatic jQuery ajax end");


        //enable the delete button to delete this new HTML
        deleteButton.onclick = function(e) {
            var evtTgt = e.target;
            evtTgt.parentNode.parentNode.removeChild(evtTgt.parentNode);
        }


        //enable the predict button to contact the server and update the "predictResult"
        predictButton.addEventListener("click", predictFunc);
        //when button pressed, call predictFunc to send ajax and update predictResult
        function predictFunc(){
            //send a POST request to train the model on the currently referenced file
            //retrieve a message, label class, prediction
            //https://www.airpair.com/js/jquery-ajax-post-tutorial

            var payload = JSON.stringify({
                "clipName": clipName,
                "smpLabel": smpLabel
            });

            $.ajax({
                url: '/predict',
                type: 'POST',
                dataType: 'json',
                contentType: 'application/json',
                data: payload,
                processData: false,
                cache: false,
                success: function(data){
                    console.log("[client] predict success: \n",data.message);
                    predictResult.innerHTML = 'Label: ' + data.label + '   Predicted: ' + data.predicted;
                },
                error: function(e) {
                    console.log("[client] error predict: \n", e);
                }
            });
        }

    }
};