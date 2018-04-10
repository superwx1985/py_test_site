$.extend({
    //  获取对象的长度，需要指定上下文 this
    Object: {
        count: function (p) {
            p = p || false;

            return $.map(this, function (o) {
                if (!p) return o;

                return true;
            }).length;
        }
    }
});


function refluch_single_column(is_success, value, col_name, data_id) {
    var td = $('tr[data_id="'+data_id+'"]>td[col_name="'+col_name+'"]');
    td.text(value);
    if (is_success) {
        td.css('background-color', 'lightgreen');// 变为浅绿
        td.animate({opacity: 'toggle'}, 250);// 闪烁动画
        td.animate({opacity: 'toggle'}, 250);
        // 1.5秒后颜色恢复
        setTimeout(function () {
            td.css('background-color', '');
        }, 1000);
    } else {
        td.css('background-color', 'red');// 变为红色
        td.animate({opacity: 'toggle'}, 250);// 闪烁动画
        td.animate({opacity: 'toggle'}, 250);
        setTimeout(function () {
            td.css('background-color', '');
        }, 1000);
    }
}


function update_single_column(url, csrf_token, new_value, old_value, col_name, data_id, callback_func) {
    $.ajax({
        url: url,
        type: "POST",
        data: {
            csrfmiddlewaretoken: csrf_token,
            col_name: col_name,
            data_id: data_id,
            new_value: new_value
        },
        dataType: "json",
        success: function (data, textStatus) {
            // console.log('success');
            // console.log("data['new_value']: " + data['new_value']);
            // console.log("textStatus: " + textStatus);
            callback_func(true, new_value, col_name, data_id)
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            // console.log('error');
            // console.log("XMLHttpRequest: " + XMLHttpRequest);
            // console.log("XMLHttpRequest.status: " + XMLHttpRequest.status);
            // console.log("XMLHttpRequest.statusText: " + XMLHttpRequest.statusText);
            // console.log("XMLHttpRequest.responseText: " + XMLHttpRequest.responseText);
            // console.log("XMLHttpRequest.responseXML: "+XMLHttpRequest.responseXML);
            // console.log("textStatus: " + textStatus);
            // console.log("errorThrown: " + errorThrown);
            callback_func(false, new_value, col_name, data_id)
        }
    })
}

