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
            var textarea = $("<textarea class='input-area'></textarea>");
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

// 全选
function bind_select_all_button() {
    $('th[index]').off('click').click(function () {
        if (window.muliple_selected_id.length > 0) {
        $('tr[pk]').data('selected', false);
        $('td[col_name=index]').css('background-color', '');
        window.muliple_selected_id = [];
    } else {
        $('tr[pk]').data('selected', true);
        $('td[col_name=index]').css('background-color', 'lightblue');
        $('tr[pk]').each(function (i, e) {
            window.muliple_selected_id.push($(e).attr('pk'))
        });
    }
    multiple_operate_button_state();
    });
}

// 多选
function multiple_select($td) {
    var tr = $td.parent('tr');
    var selected_id = tr.attr('pk');

    if (!tr.data('selected')) {
        tr.data('selected', true);
        $td.css('background-color', 'lightblue');
        window.muliple_selected_id.push(selected_id)
    } else {
        tr.data('selected', false);
        $td.css('background-color', '');
        window.muliple_selected_id.splice($.inArray(selected_id, window.muliple_selected_id), 1)
    }
    multiple_operate_button_state();
}

// 批量操作按钮状态
function multiple_operate_button_state() {
    if (muliple_selected_id.length > 0) {
        $('#multiple_copy_button').removeAttr('disabled');
        $('#multiple_delete_button').removeAttr('disabled');
    } else {
        $('#multiple_copy_button').attr('disabled', true);
        $('#multiple_delete_button').attr('disabled', true);
    }
}

// 批量删除按钮
function bind_multiple_delete_button() {
    $('#multiple_delete_button').off('click').click(function () {
        var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
        var url = window.multiple_delete_url;
        var json_str = JSON.stringify(window.muliple_selected_id);
        var msg = '要删除<span class="mark">' + window.muliple_selected_id.length + '</span>个对象吗？<span class="text-danger">（系统将自动跳过无删除权限的对象）</span>';
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
                        $.post(url, {'csrfmiddlewaretoken': csrf_token, 'pk_list': json_str}, function(data) {
                            if (data.state === 1) {
                                $('#objects_form').submit();
                            } else {
                                bootbox.alert('<span class="text-danger">'+data.message+'</span>');
                            }
                        });
                    }
                }
            });
    });
}

// 批量复制按钮
function bind_multiple_copy_button() {
    $('#multiple_copy_button').off('click').click(function () {
        var body = $('<div>').addClass('modal-body');
        var now = new Date().Format("yyyy-MM-dd HH:mm:ss");
        var div = $('<div>准备复制<span class="mark">' + window.muliple_selected_id.length + '</span>个对象。请输入复制后的名称前缀：</div>');
        body.append(div);
        body.append($('<br>'));
        var input = $('<input class="form-control" autocomplete="off" type="text" id="copy_obj_name">').attr('value', '【' + now + ' 复制】');
        body.append(input);
        var url = window.multiple_copy_url;
        if (window.has_sub_object) {
            var buttons = {
                cancel: {
                    label: '<i class="icon-undo">&nbsp;</i>取消',
                    className: 'btn btn-secondary'
                },
                copy: {
                    label: '<i class="icon-copy">&nbsp;</i>复制',
                    className: 'btn btn-warning',
                    callback: function () { callback_multiple_copy_obj(url, $('#copy_obj_name').val()) }
                },
                copy_sub_item: {
                    label: '<i class="icon-copy">&nbsp;</i>同时复制子对象',
                    className: 'btn btn-warning-dark',
                    callback: function () { callback_multiple_copy_obj_sub_item(url, $('#copy_obj_name').val()) }
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
                    callback: function () { callback_multiple_copy_obj(url, $('#copy_obj_name').val()) }
                }
            }
        }

        bootbox.dialog({
            size: 'large',
            title: '<i class="icon-exclamation-sign">&nbsp;</i>请确认',
            message: body.html(),
            onEscape: true,
            backdrop: true,
            buttons: buttons
        });
    });
}

// 详情按钮
// function bind_edit_button() {
//     $('button[name=edit_button]').on('click', function() {
//         var url = $(this).parents('tr').attr('edit_url') + '?next=' + window.next_;
//         window.open(url, '_self');
//     });
// }

// 添加详情链接
function add_edit_link() {
    $('td[col_name=name]').each(function () {
        var url = $(this).parents('tr').attr('edit_url') + '?next=' + window.next_;
        var a = $('<a>');
        a.attr('href', url).text($(this).text());
        $(this).empty().append(a);
    });
}

// 删除按钮
function bind_delete_button() {
    $('button[name="delete_button"]').off('click').click(function () {
        var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
        var url = $(this).parents('tr').attr('del_url');
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
                        if (data.state === 1) {
                                $('#objects_form').submit();
                            } else {
                                bootbox.alert('<span class="text-danger">'+data.message+'</span>');
                            }
                    });
                    // 如使用delete方式，需要在ajax头文件中设置X-CSRFToken
                    // $.ajaxSetup({
                    //     beforeSend: function (xhr, settings) {
                    //         xhr.setRequestHeader('X-CSRFToken', csrf_token);
                    //     }
                    // });
                    // $.ajax({
                    //     url: url,
                    //     type: 'DELETE',
                    //     success: function () {
                    //        $("#objects_form").submit()
                    //     }
                    // });
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
            if (data.state === 1) {
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

// 复制对象的回调函数
function callback_copy_obj(copy_url, name_prefix) {
    copy_obj_post(copy_url, name_prefix)
}

// 复制对象及子对象的的回调函数
function callback_copy_obj_sub_item(copy_url, name_prefix) {
    copy_obj_post(copy_url, name_prefix, 1)
}

// 复制对象
function copy_obj_post(copy_url, name_prefix, copy_sub_item) {
    $('#mask').show();
    $.post(copy_url, {'csrfmiddlewaretoken': $csrf_input.val(), 'name_prefix': name_prefix, 'copy_sub_item': copy_sub_item}, function(data) {
        $('#mask').hide();
        if (data.state === 1) {
            $('#objects_form').submit();
        } else {
            bootbox.alert('<span class="text-danger">'+data.message+'</span>');
        }
    });
}

// 批量复制对象的回调函数
function callback_multiple_copy_obj(url, name_prefix) {
    multiple_copy_obj_post(url, name_prefix)
}

// 复制对象及子对象的的回调函数
function callback_multiple_copy_obj_sub_item(url, name_prefix) {
    multiple_copy_obj_post(url, name_prefix, 1)
}

// 批量复制对象
function multiple_copy_obj_post(url, name_prefix, copy_sub_item) {
    var json_str = JSON.stringify(window.muliple_selected_id);
    $('#mask').show();
    $.post(url, {'csrfmiddlewaretoken': $csrf_input.val(), 'name_prefix': name_prefix, 'copy_sub_item': copy_sub_item, 'pk_list': json_str}, function(data) {
        $('#mask').hide();
        if (data.state === 1) {
            $('#objects_form').submit();
        } else {
            bootbox.alert('<span class="text-danger">'+data.message+'</span>');
        }
    });
}

// 更新排序标志
function update_sort_icon() {
    $('#result_table th[order_by_text]').find('i').remove();
    var sort_col = $('#result_table th[order_by_text=' + $('input[name=order_by]').val() + ']');
    if ($('input[name=order_by_reverse]').val() === 'True') {
        sort_col.prepend('<i class="icon-circle-arrow-down">&nbsp;</i>');
    } else {
        sort_col.prepend('<i class="icon-circle-arrow-up">&nbsp;</i>');
    }
}

