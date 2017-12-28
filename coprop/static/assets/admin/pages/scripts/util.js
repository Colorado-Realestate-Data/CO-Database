var Server = function(){};
Server.prototype = {

    call: function(url, data, callback, err_callback, method, asyncronous) {
        asyncronous = (asyncronous != false);
        $.ajax({
            type: method,
            url: url,
            data: data == undefined || method == 'GET' ? data: JSON.stringify(data),
            dataType: 'json',
            contentType: 'application/json;charset=UTF-8',
            success: callback || this.default_callback,
            error: err_callback || this.default_error_callback,
            async: asyncronous
        });
    },
    default_error_callback: function(response, showReason, delay, extra_message) {
        var msg;
        delay = delay != undefined? delay: 5000;
        if (response.status === 0) {
            msg = "Server Connection Error";
        } else {
            msg = response.status + ": " + response.statusText;
            if (showReason && response.responseJSON && response.responseJSON.reason) {
                msg += ' ('+ JSON.stringify(response.responseJSON.reason) + ')';
            }
            if (extra_message) {
                msg += extra_message;
            }
        }
        showModalAlert('ERROR', msg, 'danger', delay);

    },
    default_callback: function(res) {
        showModalAlert('SUCCESS', 'Operation done successfully', 'success');
    },
    get: function(url, callback, err_callback, asyncronous) {
        this.call(url, undefined, callback, err_callback, 'GET', asyncronous)
    },
    post: function(url, data, callback, err_callback, asyncronous) {
        this.call(url, data, callback, err_callback, 'POST', asyncronous)
    },
    put: function(url, data, callback, err_callback, asyncronous) {
        this.call(url, data, callback, err_callback, 'PUT', asyncronous)
    },
    delete: function(url, callback, err_callback, asyncronous) {
        this.call(url, undefined, callback, err_callback, 'DELETE', asyncronous)
    }
};
var server = new Server();

function showAlert(message, alerttype, delay, place_holder) {
    place_holder = place_holder || 'alert_placeholder';
    delay = delay != undefined? delay: 5000;
    $('#' + place_holder).append('<div id="alertdiv" class="alert ' +  alerttype + '"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>');
    if (delay != 0) {
        setTimeout(function() { // this will automatically close the alert and remove this if the users doesnt close it in 5 secs
            $("#alertdiv").remove();
        }, delay);
    }
}

function showModalAlert(title, content, type, delay, place_holder) {
    place_holder = place_holder == undefined? '#notify_modal': '#'+place_holder;
    delay = delay != undefined? delay: 5000;
    type = type != undefined? type: 'success';
    title = '<span class="text-' + type + '"><strong>' + title + '</strong></span>'
    $(place_holder + ' ' + place_holder + '_title').html(title);
    $(place_holder + ' ' + place_holder + '_content').html(content);
    $(place_holder).modal('show').css("z-index", "999999999");
    if (delay != 0) {
        var tid = setTimeout(function() { // this will automatically close the alert and remove this if the users doesnt close it in 5 secs
            $(place_holder).modal('hide');
        }, delay);
        $(place_holder).on('hide.bs.modal', function(event) {
            clearTimeout(tid);
        });
    }
}

