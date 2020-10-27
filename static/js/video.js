function onReady(callback){
    if (document.readyState!='loading') {
        callback();
    } else {
        document.addEventListener('DOMContentLoaded', callback);
    }
}


function gen_handle_rewind(video, diff) {
    return function(event) {
        video.currentTime += diff;
    };
}


function gen_handle_speed(video, indicator, diff) {
    return function(event) {
        video.playbackRate = Math.max(video.playbackRate + diff, 0);
        indicator.innerText = video.playbackRate.toFixed(1) + "x";
    };
}


onReady(function(){
    var video = document.getElementById('video');
    var video_url = document.getElementById('video-url').innerText;

    var back_60 = document.getElementById('video-back-60');
    var back_10 = document.getElementById('video-back-10');
    var fwd_10 = document.getElementById('video-fwd-10');
    var fwd_60 = document.getElementById('video-fwd-60');

    var slower = document.getElementById('video-speed-down');
    var faster = document.getElementById('video-speed-up');
    var speed_indicator = document.getElementById('video-speed');

    if(Hls.isSupported()) {
        var hls = new Hls();
        hls.loadSource(video_url);
        hls.attachMedia(video);
    }


    back_60.addEventListener('click', gen_handle_rewind(video, -60));
    back_10.addEventListener('click', gen_handle_rewind(video, -10));
    fwd_10.addEventListener('click', gen_handle_rewind(video, +10));
    fwd_60.addEventListener('click', gen_handle_rewind(video, +60));

    slower.addEventListener('click', gen_handle_speed(video, speed_indicator, -0.1));
    faster.addEventListener('click', gen_handle_speed(video, speed_indicator, +0.1));

    document.addEventListener("keyup", function(event) {
        if (event.key == "+") {
            document.getElementById("video-speed-up").click();
        }
        if (event.key == "-") {
            document.getElementById("video-speed-down").click();
        }
    });
});
