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
function quick_update(tds, func, callback_func) {
    // 注册鼠标双击事件
    tds.off('dblclick').dblclick(function () {
        //找到当前鼠标双击的td
        var td = $(this);
        var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
        var col_name = td.attr('col_name');
        var url = td.parent('tr').attr('updateUrl');
        var pk = td.parent('tr').attr('pk');
        // 判断是否已在编辑
        if (td.attr('editing')) {
            // 获取原值
            var old_value = td.data('oldText');
            var textarea = td.children('textarea');
            var new_value = textarea.val();
            //当修改前后的值不同时才进行数据库提交操作
            if (old_value != new_value) {
                func(url, csrf_token, pk, new_value, old_value, col_name, callback_func);
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
                        if (old_value !== new_value) {
                            func(url, csrf_token, pk, new_value, old_value, col_name, callback_func);
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
function bind_delete_button() {
    $('button[name="delete_button"]').off('click').click(function () {
        var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
        var url = $(this).parents('tr').attr('delUrl');
        var pk = $(this).parents('tr').attr('pk');
        // var name = $(this).parent().siblings('td[col_name="name"]').text();
        var name = $(this).parents('tr').find('td[col_name="name"]').text();
        var msg = '确定要删除<span class="mark">' + name + '</span>吗？';
        bootbox.confirm({
            title: '<i class="icon-spinner icon-spin icon-2x pull-left"></i>',
            message: msg,
            buttons: {
                confirm: {
                    label: '<i class="icon-trash">&nbsp;</i>确定',
                    className: 'btn-danger'
                },
                cancel: {
                    label: '<i class="icon-undo">&nbsp;</i>取消',
                    className: 'btn-secondary'
                }
            },
            callback: function (result) {
                if (result === true) {
                    console.log('delete');
                    $.post(url, {'csrfmiddlewaretoken': csrf_token, 'pk': pk}, function(data) {
                        $("#objects_form").submit()
                    });
                }
            },
            size: 'large'
        })
    })
}


// 刷新字段显示
function refresh_single_column(is_success, pk, new_value, old_value, col_name, msg) {
    var td = $('tr[pk="'+pk+'"]>td[col_name="'+col_name+'"]');
    td.text(new_value);
    if (is_success) {
        console.log(1111)
        toastr.success('更新成功');
        td.css('background-color', 'lightgreen');// 变为浅绿
        td.animate({opacity: 'toggle'}, 300);// 闪烁动画
        td.animate({opacity: 'toggle'}, 300);
        // 1秒后颜色恢复
        setTimeout(function () {
            td.css('background-color', '');
        }, 1000);
    } else {
        toastr.error(msg);
        td.css('background-color', 'red');// 变为红色
        td.animate({opacity: 'toggle'}, 300);// 闪烁动画
        td.animate({opacity: 'toggle'}, 300);
        setTimeout(function () {
            td.css('background-color', '');
            td.text(old_value);
        }, 1000);
    }
}


// 更新单个字段
function update_single_column(url, csrf_token, pk, new_value, old_value, col_name, callback_func) {
    $.ajax({
        url: url,
        type: "POST",
        data: {
            csrfmiddlewaretoken: csrf_token,
            pk: pk,
            new_value: new_value,
            col_name: col_name
        },
        dataType: "json",
        success: function (data, textStatus) {
            // console.log('success');
            // console.log("data['new_value']: " + data['new_value']);
            // console.log("textStatus: " + textStatus);
            callback_func(true, pk, new_value, old_value, col_name)
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
            callback_func(false, pk, new_value, old_value, col_name, XMLHttpRequest.responseText)
        }
    })
}

// 设置cookie
function set_cookie(name, value, seconds) {
	var exp = new Date();
	exp.setTime(exp.getTime() + seconds*1000)
	document.cookie = name + "=" + encodeURI(value) + ";expires=" + exp.toUTCString();
}

// 获取cookie
function get_cookie(name) {
	var arr,reg = new RegExp("(^|)" + name + "=([^;]*)(;|$)");
	if (arr=document.cookie.match(reg)) {
		return unescape(arr[2]);
	} else {
		return null;
	}
}

// 输出返回消息（废弃，使用toastr代替）
/*
function show_info(msg, class_list, time) {
	// 首先停止上次的setTimeout任务
	if ("undefined"!==typeof(_show_info_timeout_id)) {
		clearTimeout(_show_info_timeout_id);
	}
	var show_info = $(".show_info");
	show_info.empty()
	var show_info_wrap = $('<div></div>');
	var show_info_inner = $('<div></div>');
	show_info_wrap.append(show_info_inner);
	show_info.append(show_info_wrap);
	show_info_inner.text(msg);
	show_info_inner.addClass(class_list);
	show_info.show();
	window._show_info_timeout_id = setTimeout(function(){show_info.fadeOut(500)}, time);// 停留{time}毫秒之后淡出
}*/

// 获取结果集
function getListAll(url, csrf_token, callback_func, condition) {
	$.ajax({
        url: url,
        type: "GET",
        data: {
            csrfmiddlewaretoken: csrf_token,
            condition: condition,
        },
        dataType: "json",
        success: function (data, textStatus) {
            // console.log('success');
            // console.log("data['new_value']: " + data['new_value']);
            // console.log("textStatus: " + textStatus);
            callback_func(true, data)
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
            callback_func(false, XMLHttpRequest.responseText)
        }
    })
}