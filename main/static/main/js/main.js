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


// 快速修改
function quick_update(url, tds, func, callback_func) {
    // 注册鼠标双击事件
    tds.off('dblclick').dblclick(function () {
        //找到当前鼠标双击的td
        var td = $(this);
        var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
        var col_name = td.attr('col_name');
        var object_id = td.parent('tr').attr('object_id');
        // 判断是否已在编辑
        if (td.attr('editing')) {
            // 获取原值
            var old_value = td.data('oldText');
            var textarea = td.children('textarea');
            var new_value = textarea.val();
            //当修改前后的值不同时才进行数据库提交操作
            if (old_value != new_value) {
                func(url, csrf_token, object_id, new_value, old_value, col_name, callback_func);
            }
            // 去掉编辑标志
            td.removeAttr('editing');
            td.text(td.children().val());
            td.children().remove();
        } else {
            // 添加可编辑属性
            td.attr('');
            // 添加编辑标志
            td.attr('editing', true);
            //保存原来的文本
            td.data('oldText', td.text());
            var old_value = td.text();
            // 插入输入框
            var textarea = $("<textarea class='input_area'></textarea>");
            textarea.css({'height': '100%', 'background-color': 'lightyellow'});
            textarea.text(old_value);
            td.text('');
            td.append(textarea);
            // 切换焦点
            textarea.trigger("focus");
            // 全选
            // textarea.trigger("focus").trigger("select");
            // 处理键盘输入
            textarea.off('keydown').keydown(function () {
                var key_code = event.keyCode;
                switch (key_code) {
                    // 按下回车，保存修改
                    case 13:
                        var new_value = textarea.val();
                        // 当修改前后的值不同时才进行数据库提交操作
                        if (old_value != new_value) {
                            func(url, csrf_token, object_id, new_value, old_value, col_name, callback_func);
                        }
                        // 去掉编辑标志
                        td.removeAttr('editing');
                        td.text(td.children().val());
                        td.children().remove();
                        break;
                    // 按下Esc，取消修改，恢复原来的文本
                    case 27:
                        td.text(old_value);
                        // 去掉编辑标志
                        td.removeAttr('editing');
                        td.text(td.children().val());
                        td.children().remove();
                        break;
                }
            });
            /*
            //文本框失去焦点的时候变为文本
            inputObj.blur(function () {
                var newText = $(this).val();
                tdObj.html(newText);
            });
            */
        }
    });
}

// 删除
function bind_delete_button(url) {
    $('button[name="delete_button"]').off('click').click(function () {
        var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
        var object_id = $(this).parents('tr').attr('object_id');
        var name = $(this).parent().siblings('td[col_name="name"]').text();
        var msg = '确定要删除【' + name + '】吗？';
        var dialog_div = $('<div id="dialog-confirm" title="请确认"><p><span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>'+msg+'</p></div>');
        dialog_div.dialog({
            resizable: false,
            modal: true,
            buttons: {
                "确定": function () {
                    $(this).dialog("close");
                    $.post(url, {csrfmiddlewaretoken: csrf_token, object_id: object_id}, function(data){$("#objects_form").submit()});
                },
                "取消": function () {
                    $(this).dialog("close");
                }
            }
        });
    })
}


// 刷新字段显示
function refresh_single_column(is_success, object_id, value, col_name) {
    var td = $('tr[object_id="'+object_id+'"]>td[col_name="'+col_name+'"]');
    td.text(value);
    if (is_success) {
        td.css('background-color', 'lightgreen');// 变为浅绿
        td.animate({opacity: 'toggle'}, 300);// 闪烁动画
        td.animate({opacity: 'toggle'}, 300);
        // 1秒后颜色恢复
        setTimeout(function () {
            td.css('background-color', '');
        }, 1000);
    } else {
        td.css('background-color', 'red');// 变为红色
        td.animate({opacity: 'toggle'}, 300);// 闪烁动画
        td.animate({opacity: 'toggle'}, 300);
        setTimeout(function () {
            td.css('background-color', '');
        }, 1000);
    }
}


// 更新单个字段
function update_single_column(url, csrf_token, object_id, new_value, old_value, col_name, callback_func) {
    $.ajax({
        url: url,
        type: "POST",
        data: {
            csrfmiddlewaretoken: csrf_token,
            object_id: object_id,
            new_value: new_value,
            col_name: col_name
        },
        dataType: "json",
        success: function (data, textStatus) {
            // console.log('success');
            // console.log("data['new_value']: " + data['new_value']);
            // console.log("textStatus: " + textStatus);
            callback_func(true, object_id, new_value, col_name)
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
            callback_func(false, object_id, new_value, col_name)
        }
    })
}

