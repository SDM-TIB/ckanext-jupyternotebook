var full_loaded = false;
setTimeout(function(){ show_jupyter_notebooks_iframe(""); }, 4000);

function show_jupyter_notebooks_iframe(msg) {
    // alert("show iframe now: "+msg);
    $('#jupyternotebook_loading').hide();
    // $('#view_title').show();
    $('#jupyternotebook_iframe').show();
    full_loaded = true;
}

/* The following functions receive a message from jupyternotebook iframe
   when the content is loaded. Then the loading bar is hidden and the iframe is shown.
*/
if (window.addEventListener) {
    window.addEventListener ("message", receive, false);
} else if (window.attachEvent) {
    window.attachEvent("onmessage", receive, false);
}

function receive(event){
    var data = event.data;
    if (typeof(window[data.func]) == "function") {
        window[data.func].call(null, data.params[0]);
    }
}
