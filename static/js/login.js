function onReady(callback){
    if (document.readyState!='loading') {
        callback();
    } else {
        document.addEventListener('DOMContentLoaded', callback);
    }
}

onReady(function(){
    
});
