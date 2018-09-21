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
    tds.off('dblclick').on('dblclick', function () {
        //找到当前鼠标双击的td
        var td = $(this);
        var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
        var col_name = td.attr('col_name');
        var url = td.parent('tr').attr('quick_update_url');
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

// 详情
function bind_edit_button() {
    $('button[name=edit_button]').on('click', function() {
        var url = $(this).parents('tr').attr('edit_url') + '?next=' + window.next_;
        window.open(url, '_self');
    });
}

// 删除
function bind_delete_button() {
    $('button[name="delete_button"]').off('click').click(function () {
        var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
        var url = $(this).parents('tr').attr('del_url');
        // var name = $(this).parent().siblings('td[col_name="name"]').text();
        var name = $(this).parents('tr').find('td[col_name="name"]').text();
        var msg = '要删除<span class="mark">' + name + '</span>吗？';
        bootbox.confirm({
            title: '<i class="icon-exclamation-sign">&nbsp;</i>请确认',
            message: msg,
            size: 'large',
		    backdrop: true,
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
                    $.post(url, {'csrfmiddlewaretoken': csrf_token}, function(data) {
                        $("#objects_form").submit()
                    });
                }
            }
        });
    });
}


// 刷新字段显示
function refresh_single_column(is_success, pk, new_value, old_value, col_name, msg) {
    var td = $('tr[pk="'+pk+'"]>td[col_name="'+col_name+'"]');
    td.text(new_value);
    if (is_success) {
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
            console.log(data)
            if (data.statue === 1) {
                callback_func(true, pk, new_value, old_value, col_name);
            } else {
                callback_func(false, pk, new_value, old_value, col_name, data.message);
            }
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
            callback_func(false, pk, new_value, old_value, col_name, XMLHttpRequest.responseText);
        }
    })
}

// 生成随机字符串
function S4() {
    return (((1+ Math.random())*0x10000)|0).toString(16).substring(1);
}

// 生成GUID
function guid() {
    return (S4() + S4() + "-" + S4() + "-" + S4() + "-" + S4() + S4() + S4())
}


// 设置cookie
function set_cookie(name, value, seconds, path) {
    var exp_str = '';
    var path_str = '';
    var exp = new Date();
	if (seconds && seconds > 0) {exp_str = exp.setTime(exp.getTime() + seconds*1000).toUTCString();}
	if (path) {path_str = path}
	document.cookie = name + "=" + encodeURI(value) + ";expires=" + exp_str + ";path=" + path_str;
}

// 获取cookie
function get_cookie(name) {
	var arr,reg = new RegExp("(^|)" + name + "=([^;]*)(;|$)");
	if (arr=document.cookie.match(reg)) {
		return decodeURI(arr[2]);
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
function getList(url, csrf_token, callback_func, condition_json) {
	$.ajax({
        url: url,
        type: "POST",
        data: {
            csrfmiddlewaretoken: csrf_token,
            condition: condition_json
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

// 获取元素整体高度, 包含margin
function get_element_full_height($e) {
    var height = parseInt($e.css('margin-top')) + parseInt($e.css('margin-bottom')) + $e.outerHeight();
    return isNaN(height) ? 0 : height
}

// 获取元素外部margin, border, padding高度
function get_element_outside_height($e) {
    var height = get_element_full_height($e) - $e.height()
    return isNaN(height) ? 0 : height
}

// 复制对象弹框
function copy_obj(original_name, copy_url, sub_item) {
    var body = $('<div>').addClass('modal-body');
    var input = $('<input class="form-control" autocomplete="off" type="text" id="copy_obj_name">').attr('value', original_name);
    body.append(input);
    if (sub_item) {
        var buttons = {
            cancel: {
                label: '<i class="icon-undo">&nbsp;</i>取消',
                className: 'btn btn-secondary'
            },
            copy: {
                label: '<i class="icon-copy">&nbsp;</i>复制',
                className: 'btn btn-warning',
                callback: function () { callback_copy_obj(copy_url, $('#copy_obj_name').val()) }
            },
            copy_sub_item: {
                label: '<i class="icon-copy">&nbsp;</i>同时复制子对象',
                className: 'btn btn-warning-dark',
                callback: function () { callback_copy_obj_sub_item(copy_url, $('#copy_obj_name').val()) }
            }
        }
    } else {
        var buttons = {
            cancel: {
                label: '<i class="icon-undo">&nbsp;</i>取消',
                className: 'btn btn-secondary'
            },
            copy: {
                label: '<i class="icon-copy">&nbsp;</i>复制',
                className: 'btn btn-warning',
                callback: function () { callback_copy_obj(copy_url, $('#copy_obj_name').val()) }
            }
        }
    }

    bootbox.dialog({
        size: 'large',
        title: '<i class="icon-exclamation-sign">&nbsp;</i>请输入新名称',
        message: body.html(),
        onEscape: true,
		backdrop: true,
        buttons: buttons
    });
}

// 弹出框
function show_my_modal(modal_name, modal_class, modal_style, modal_body_style, modal_title, $modal_body_div, modal_option, callback) {
    var html_ =
        '<div class="modal fade" name="'+ modal_name +'">\n' +
        '    <div class="modal-dialog '+ modal_class +'" style="' + modal_style + '">\n' +
        '        <div class="modal-content">\n' +
        '            <div class="modal-header">\n' +
        '                <span class="modal-title lead">' + modal_title + '</span>\n' +
        '                <button type="button" class="close" data-dismiss="modal">&times;</button>\n' +
        '            </div>\n' +
        '            <div class="modal-body" style="' + modal_body_style + '"></div>\n' +
        '        </div>\n' +
        '    </div>\n' +
        '</div>';
	var my_modal = $(html_);
	$('body').append(my_modal);
	// 如果未提供title，不显示header
	if (!modal_title) { my_modal.find('.modal-header').remove() }
	var my_modal_body = my_modal.find('.modal-body');
    my_modal_body.empty().append($modal_body_div);
    // 如果body未指定高度，则使用当前页面高度来确定
    if (!parseInt(my_modal_body.css('height'))){
        // 必须要先显示出来才能得到正确的高度
        my_modal.off('shown.bs.modal').on('shown.bs.modal', function () {
            var body_height = $(window).height()
                - get_element_outside_height(my_modal.find('.modal-dialog'))
                - get_element_outside_height(my_modal.find('.modal-content'))
                - get_element_full_height(my_modal.find('.modal-header'))
                - get_element_outside_height(my_modal_body);
            my_modal_body.css('height', body_height);
        });
    }
    // 关闭modal后执行回调函数并清除modal代码
	my_modal.off('hide.bs.modal').on('hide.bs.modal', function () {
	    if (callback) { callback() }
	    my_modal.remove();
	});
    if (modal_option) { my_modal.modal(modal_option) } else { my_modal.modal() }
    return my_modal;
}

// 弹出内嵌页面
function modal_with_iframe(modal_name, modal_class, modal_style, modal_body_style, modal_title, url, modal_option, callback) {
    var $modal_body_div = $('<div style="height: 100%;"></div>');
    var iframe = $('<iframe>').attr('name', modal_name + '_iframe').attr('frameborder', 0).css({'height': '100%', 'width': '100%'});
    if (url) {
        iframe.attr('src', url);
    }
    $modal_body_div.append(iframe);
    return show_my_modal(modal_name, modal_class, modal_style, modal_body_style, modal_title, $modal_body_div, modal_option, callback)
}

// 弹出内嵌页面最大化
function modal_with_iframe_max(modal_name, modal_title, url, modal_option, callback) {
    return modal_with_iframe(modal_name, 'modal-max', '', 'min-height: 600px', modal_title, url, modal_option, callback)
}

// 查看被调用弹窗
function show_reference(url, title) {
    if (!title) {
        var title = '被调用情况';
    }
	bootbox.dialog({
		title: title,
		message: '<div id="reference_div" class="middle"><i class="icon-spinner icon-spin icon-5x"></i></div>',
		size: 'large',
		onEscape: true,
		backdrop: true,
		init: $.get(url, function (data) {
			$('#reference_div').parent('.bootbox-body').empty().html(data);
		}, 'html')
	})
}