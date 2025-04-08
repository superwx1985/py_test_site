// 快速修改
function quick_update(tds, func, callback_func) {
    // 注册鼠标双击事件
    tds.off('dblclick').on('dblclick', function () {
        const $td = $(this);
        const csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
        const col_name = $td.attr('col_name');
        const url = $td.parent('tr').attr('quick_update_url');
        const pk = $td.parent('tr').attr('pk');
        // 判断是否已在编辑
        if ($td[0].hasAttribute('editing')) {
            // 获取原值
            const old_value = $td.data('oldText');
            const textarea = $td.children('textarea');
            const new_value = textarea.val();
            console.log('old_value: ', old_value, '; new_value: ', new_value)
            restore_td($td, new_value)
            //当修改前后的值不同时才进行数据库提交操作
            if (old_value !== new_value) {
                func(url, csrf_token, pk, new_value, old_value, col_name, callback_func, $td);
            }
        } else {
            // 添加编辑标志
            $td.attr('editing', '');
            // 保存链接
            $td.data('$a', $td.find('a'));
            // $td.data('link', $td.find('a').attr('href') || '');
            //保存原来的文本
            const old_value = $td.text();
            $td.data('oldText', old_value);
            // 插入输入框
            const $textarea = $("<textarea class='input-area'></textarea>");
            $textarea.css({'height': '100%', 'background-color': 'lightyellow'});
            $textarea.text(old_value);
            $td.text('');
            $td.append($textarea);
            // 获取原生 DOM 元素
            const nativeTextarea = $textarea[0];
            // 设置光标到文本末尾
            nativeTextarea.selectionStart = nativeTextarea.value.length;
            nativeTextarea.selectionEnd = nativeTextarea.value.length;
            // 触发焦点
            nativeTextarea.focus(); // 优先用原生 focus() 而非 jQuery 的 trigger("focus")
            // 处理键盘输入
            $textarea.off('keydown').on('keydown', (event) => {
                const key_code = event.keyCode;
                switch (key_code) {
                    // 按下回车，保存修改
                    case 13:
                        const new_value = $textarea.val();
                        restore_td($td, new_value)
                        // 当修改前后的值不同时才进行数据库提交操作
                        if (old_value !== new_value) {
                            func(url, csrf_token, pk, new_value, old_value, col_name, callback_func, $td);
                        }
                        break;
                    // 按下Esc，取消修改，恢复原来的文本
                    case 27:
                        restore_td($td, old_value)
                        break;
                }
            });
        }
    });
}

// 批量操作按钮状态
function multiple_operate_button_state() {
    if (window.muliple_selected_id.length > 0) {
        $('#multiple_delete_button').removeAttr('disabled');
        $('#multiple_copy_button').removeAttr('disabled');
    } else {
        $('#multiple_delete_button').attr('disabled', true);
        $('#multiple_copy_button').attr('disabled', true);
    }
}

// 多选列表刷新
function update_muliple_selected() {
	window.muliple_selected_id = [];
	$('#result_table tbody tr').each(function (i, e) {
		if ($(e).data('selected')) {
			window.muliple_selected_id.push($(e).attr('pk'));
			$(e).css('background-color', 'lightblue');
		} else {
			$(e).css('background-color', '');
		}
	});
	multiple_operate_button_state()
}

// 全选
function bind_select_all_button() {
    $('#result_table th[select_all]').off('click').click(function () {
        if (window.muliple_selected_id.length > 0) {
            if (window.muliple_selected_reverse) {
                $('#result_table tbody tr').each(function (i, e) {
                    if ($(e).data('selected')) {
                        $(e).data('selected', false);
                    } else {
                        $(e).data('selected', true);
                    }
                });
                window.muliple_selected_reverse = false;
            } else {
                $('#result_table tbody tr').data('selected', false);
            }
		} else {
			$('#result_table tbody tr').data('selected', true);
		}
	update_muliple_selected();
    });
}

// 多选
function multiple_select($td) {
    let tr = $td.parent('tr');
    window.muliple_selected_reverse = true;

    if (!tr.data('selected')) {
        tr.data('selected', true);
    } else {
        tr.data('selected', false);
    }
    update_muliple_selected();
}

// 注册多选功能
function bind_multiple_select() {
	$('#result_table tbody tr td[col_name=index]').off('click').on('click', function() { multiple_select($(this)) });
}

// 批量删除按钮
function bind_multiple_delete_button() {
    $('#multiple_delete_button').off('click').click(function () {
        const csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
        const url = window.multiple_delete_url;
        const json_str = JSON.stringify(window.muliple_selected_id);
        const msg = '要删除<span class="mark">' + window.muliple_selected_id.length + '</span>个对象吗？<span class="text-danger">（系统将自动跳过无删除权限的对象）</span>';
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
        const body = $('<div>').addClass('modal-body');
        const now = new Date().Format("yyyy-MM-dd HH:mm:ss");
        const div = $('<div>准备复制<span class="mark">' + window.muliple_selected_id.length + '</span>个对象。请输入复制后对象的名称前缀</div>');
        body.append(div);
        const input = $('<input class="form-control" autocomplete="off" type="text" id="copy_obj_name">').attr('value', '【' + now + ' 复制】');
        body.append(input);
        const url = window.multiple_copy_url;
        let buttons;
        if (window.has_sub_object) {
            buttons = {
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
                    label: '<span><i class="icon-copy">&nbsp;</i>复制子对象</span>',
                    className: 'btn btn-warning-dark',
                    // callback: function () { callback_multiple_copy_obj_sub_item(url, $('#copy_obj_name').val()) },
                    disabled: true,
                    // 添加 Tooltip
                    attributes: {
                        "title": "为防止误操作，批量复制功能禁止复制子对象",
                        "data-bs-toggle": "tooltip",
                        "data-bs-placement": "top"
                    }
                }
            }
        } else {
            buttons = {
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
            buttons: buttons,
            onShown: () => {
                // 初始化 Tooltip（对话框渲染后生效）
                $('[data-bs-toggle="tooltip"]').tooltip();
            }
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
function refresh_single_column(is_success, $td, new_value, old_value, msg) {
    restore_td($td, new_value)
    if (is_success) {
        toastr.success('更新成功');
        $td.css('background-color', 'lightgreen');// 变为浅绿
        $td.animate({opacity: 'toggle'}, 300);// 闪烁动画
        $td.animate({opacity: 'toggle'}, 300);
        // 1秒后颜色恢复
        setTimeout(function () {
            $td.css('background-color', '');
        }, 1000);
    } else {
        toastr.error(msg);
        $td.css('background-color', 'red');// 变为红色
        $td.animate({opacity: 'toggle'}, 300);// 闪烁动画
        $td.animate({opacity: 'toggle'}, 300);
        setTimeout(function () {
            $td.css('background-color', '');
            restore_td($td, old_value)
        }, 1000);
    }
}

// 复原td
function restore_td($td, value) {
    const $a = $td.data('$a');
    $td.removeAttr('editing');
    $td.children().remove();
    if ($a.length) {
        $a.text(value);
        $td.append($a);
    } else {
        $td.text(value);
    }
}

// 更新单个字段
function update_single_column(url, csrf_token, pk, new_value, old_value, col_name, callback_func, $td) {
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
                callback_func(true, $td, new_value, old_value, 'msg');
            } else {
                callback_func(false, $td, new_value, old_value, data.message);
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
            callback_func(false, $td, new_value, old_value, XMLHttpRequest.responseText);
        }
    })
}

// 复制对象的回调函数
function callback_copy_obj(copy_url, new_name) {
    copy_obj_post(copy_url, new_name)
}

// 复制对象及子对象的的回调函数
function callback_copy_obj_sub_item(copy_url, parent_name) {
    let sub_object_prefix = "【复制《" + parent_name.trim() + "》时生成】";
    const body = $('<div>').addClass('modal-body');
    const div = $('<div>复制对象包含的所有子对象，将生成大量数据，可能耗费较长时间。请确认您了解此操作的含义。<br>请输入复制后对象的名称前缀：</div>');
    body.append(div);
    const input = $('<input class="form-control" autocomplete="off" type="text" id="sub_object_prefix">').attr('value', sub_object_prefix);
    body.append(input);
    bootbox.dialog({
		size: 'large',
		title: '<i class="icon-exclamation-sign">&nbsp;</i>请再次确认',
		message: body.html(),
		buttons: {
			cancel: {
				label: '<i class="icon-undo">&nbsp;</i>取消',
				className: 'btn btn-secondary'
			},
			confirm: {
				label: '<i class="icon-ok">&nbsp;</i>确认',
				className: 'btn btn-primary',
				callback: function() { copy_obj_post(copy_url, parent_name, $('#sub_object_prefix').val(), 1) }
			}
		}
	})
}

// 复制对象
function copy_obj_post(copy_url, new_name, name_prefix, copy_sub_item) {
    $('#mask').show();
    $.post(copy_url, {'csrfmiddlewaretoken': $csrf_input.val(), 'new_name': new_name, 'name_prefix': name_prefix, 'copy_sub_item': copy_sub_item}, function(data) {
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

// 批量复制对象及子对象的的回调函数
// function callback_multiple_copy_obj_sub_item(copy_url, name_prefix) {
//     bootbox.dialog({
// 		size: 'large',
// 		title: '<i class="icon-exclamation-sign">&nbsp;</i>请再次确认',
// 		message: '复制对象包含的所有子对象，将生成大量数据，可能耗费较长时间。请确认您了解此操作的含义。',
// 		buttons: {
// 		    cancel: {
// 				label: '<i class="icon-undo">&nbsp;</i>取消',
// 				className: 'btn btn-secondary'
// 			},
// 			confirm: {
// 				label: '<i class="icon-ok">&nbsp;</i>确认',
// 				className: 'btn btn-primary',
// 				callback: function() { multiple_copy_obj_post(copy_url, name_prefix, 1) }
// 			}
// 		}
// 	})
// }

// 批量复制对象
function multiple_copy_obj_post(copy_url, name_prefix, copy_sub_item) {
    var json_str = JSON.stringify(window.muliple_selected_id);
    $('#mask').show();
    $.post(copy_url, {'csrfmiddlewaretoken': $csrf_input.val(), 'name_prefix': name_prefix, 'copy_sub_item': copy_sub_item, 'pk_list': json_str}, function(data) {
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

