// 启用排序功能
function sortable_element() {
	if (!window.editable) { return }
	$('#element_table tbody').sortable({
		items: "tr:not(#new_helper)",
		distance: 15,
		handle: "[moveable]",
		placeholder: 'ui-state-highlight',
		stop: function( event, ui ) {
			function update_function() { update_element_index_and_field() }
			// 如果选中了多条
			if (window.sub_muliple_selected_id.length > 1) {
				order_consecutive_line(window.sub_muliple_selected_id, ui.item, 'element_table', update_function)
			}
			update_function();
		}
	});
}

// 生成选项
function generate_select(select_list) {
	var $select = $('<select class="form-control">');
	$.each(select_list,function(i, v) {
		if (!v[0]) { return }
		var o = $('<option>');
		o.val(v[0]);
		o.text(v[1]);
		$select.append(o);
	});
	return $select
}

// 更新列表
function init_element(success, data, multiple_select) {
	if (success) {
		if (data.data.length > 0) {
			$('#element_table tbody tr:not(#new_helper)').remove();
			$.each(data.data, function (i, v) {
				var tr = $('<tr></tr>');
				$('<td class="middle" col_move moveable><i class="icon-sort icon-2x"></i></td>').appendTo(tr);
				$('<td class="middle" col_del><i class="icon-trash icon-2x" data-toggle="tooltip" title="删除"></i></td>').off('click').on(
					'click', function() { del_element(tr) }).appendTo(tr);
				var span = $('<span></span>').text(i + 1);
				$('<td class="middle" col_index></td>').append(span).appendTo(tr);
				var input = $('<input placeholder="请输入元素名" class="form-control" maxlength="100">').val(v.name).off('change').on('change', function () { update_element_index_and_field() });
				$('<td col_name></td>').append(input).appendTo(tr);
				var select = generate_select(window.by_list);
				select.val(v.by);
				$('<td col_by></td>').append(select).appendTo(tr);
				var input = $('<input placeholder="请输入定位值" class="form-control">').val(v.locator);
				$('<td col_locator></td>').append(input).appendTo(tr);
				var input = $('<input placeholder="" class="form-control">').val(v.description);
				$('<td col_description></td>').append(input).appendTo(tr);
				tr.insertBefore($('#new_helper'));
			});
		}
		update_element_index_and_field(multiple_select);
		// 注册提示框
		$('[data-toggle=tooltip]').tooltip();
	}
	if (!window.editable) {
		// 禁用所有互动
		disable_interaction();
    }
}

// 新对象验证重名
function check_new_element() {
	var name_input = $('#new_helper td[col_name] input');
	name_input.removeClass('is-invalid');
	name_input.siblings('div.invalid-feedback').remove();
	var check_result = check_element_name(name_input.val(), get_element_name_list_());
	if (check_result !== true) {
		get_invalid_input(name_input, check_result);
		return false;
	}
}

// 添加
function add_element() {
	var new_helper = $('#new_helper');
	var name_input = $('#new_helper td[col_name] input');
	name_input.removeClass('is-invalid');
	name_input.siblings('div.invalid-feedback').remove();
	var check_result = check_element_name(name_input.val(), get_element_name_list_());
	if (check_result === true) {
		var _new = new_helper.clone();
		// 去掉new_helper id 和 背景色
		_new.removeAttr('id').removeClass('bg-light');
		// 改变新增按钮为排序按钮
		_new.children('td[col_move]').attr('moveable', '').empty().append('<i class="icon-sort icon-2x"></i>');
		// 重新注册删除按钮事件
		_new.children('td[col_del]').off('click').on('click', function() { del_element(_new) });
		_new.find('td[col_name] input').off('change').on('change', function () { update_element_index_and_field() });
		// 选项值无法复制，需要强制更新
        _new.find('td[col_by] select').val(new_helper.find('td[col_by] select').val());
		// 插入并淡入
		_new.insertBefore(new_helper).hide();
		_new.fadeIn("slow");
		$('#new_helper td[col_name] input').val('').focus();
		$('#new_helper td[col_locator] input').val('');
		$('#new_helper td[col_description] input').val('');
		update_element_index_and_field();
		// 注册提示框
		$('[data-toggle=tooltip]').tooltip();
		return true;
	} else {
		get_invalid_input(name_input, check_result);
		return false;
	}
}

// 删除
function del_element($tr) {
	var name = $tr.find('td[col_name] input').val();
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
				$tr.fadeOut("slow", function() {
					$(this).remove();
					update_element_index_and_field();
				});
			}
		}
	});
}

// 获取名称列表
function get_element_name_list_() {
	var trs = $('#element_table tbody tr:not(#new_helper)');
	var name_list = [];
	trs.each(function() {
		name_list.push($(this).find('td[col_name] input').val());
	});
	return name_list;
}

// 验证名称
function check_element_name(name, name_list_) {
	if (!name || ''===name.trim()) {
		return '名称不能为空'
	}
	var index = $.inArray(name, name_list_);
	if (index >= 0) {
		return '与第[' + (index + 1) + ']行重名'
	}
	return true;
}

// 生成带错误提示的输入框
function get_invalid_input($input, check_result){
	$input.removeClass('is-invalid');
	$input.siblings('div.invalid-feedback').remove();
	var errorDiv = $('<div class="invalid-feedback">' + check_result + '</div>');
	$input.addClass('is-invalid');
	$input.after(errorDiv);
}

// 更新列表序号，更新表单内容
function update_element_index_and_field(multiple_select) {
	var trs = $('#element_table tbody tr:not(#new_helper)');
	var _list = [];
	var name_list = [];
	window.temp_sub_list = [];
	trs.each(function(i) {
		$(this).attr('order', i+1);
		$(this).find('td[col_index] span').text(i+1);
		var name_input = $(this).find('td[col_name] input');
		var name = name_input.val();
		var check_result = check_element_name(name, name_list);
		name_input.removeClass('is-invalid');
		name_input.siblings('div.invalid-feedback').remove();
		var by = $(this).find('td[col_by] select').val();
		var locator = $(this).find('td[col_locator] input').val();
		var description = $(this).find('td[col_description] input').val();
		var element = {};
		element.name = name;
		element.by = by;
		element.locator = locator;
		element.description = description;
		window.temp_sub_list.push(element);
		if (check_result === true) {
			_list.push(element);
			name_list.push(name);
		} else {
			get_invalid_input(name_input, check_result);
		}
	});
	window.$sub_input.val(JSON.stringify(_list));
	if (window.editable) {
		bind_sub_multiple_select();
	}
	update_sub_muliple_selected(multiple_select);
	// 关闭遮罩
	$('#mask').hide();
}

// 检查是否有未保存的对象
function check_unsaved() {
	var name = $('#new_helper td[col_name] input').val();
	if ($('#element_table tbody div.invalid-feedback').length > 0) {
		var msg = '检查到错误，请返回修改';
		bootbox.alert({
			title: '<i class="icon-exclamation-sign">&nbsp;</i>请确认',
			message: msg,
			size: 'large',
			backdrop: true,
			buttons: {
				ok: {
					label: '<i class="icon-undo">&nbsp;</i>返回修改',
					className: 'btn-secondary'
				}
			}
		});
	}
    else if (name !== '') {
		var msg = '检查到有未保存的变量<span class="mark">' + name + '</span>，是否需要一并提交？';
		bootbox.confirm({
			title: '<i class="icon-exclamation-sign">&nbsp;</i>请确认',
			message: msg,
			size: 'large',
			backdrop: true,
			buttons: {
				confirm: {
					label: '<i class="icon-ok">&nbsp;</i>一并提交',
					className: 'btn-success'
				},
				cancel: {
					label: '<i class="icon-undo">&nbsp;</i>返回修改',
					className: 'btn-secondary'
				}
			},
			callback: function (result) {
				if (result === true) {
					if (add_element()) {
						$('#object_form').removeAttr('onsubmit').submit();
					}
				}
			}
		});
	} else {
		update_element_index_and_field();
		$('#object_form').removeAttr('onsubmit').submit();
	}
	return false;
}

// 批量操作按钮状态
function sub_multiple_operate_button_state() {
    if (window.sub_muliple_selected_id.length > 0) {
        $('#sub_multiple_delete_button').removeAttr('disabled');
        $('#sub_multiple_copy_obj_button').removeAttr('disabled');
    } else {
        $('#sub_multiple_delete_button').attr('disabled', true);
        $('#sub_multiple_copy_obj_button').attr('disabled', true);
    }
}

// 多选列表刷新
function update_sub_muliple_selected(multiple_select) {
	if (multiple_select) {  // 通过sub_muliple_selected_id更新列表
		$('#element_table tbody tr:not(#new_helper)').data('selected', false).css('background-color', '');
		$.each(window.sub_muliple_selected_id, function(i, v) {
			$('#element_table tbody tr[order='+ v.order +']').data('selected', true).css('background-color', 'lightblue');
		});
	} else {  // 通过列表更新sub_muliple_selected_id
        window.sub_muliple_selected_id = [];
        $('#element_table tbody tr:not(#new_helper)').each(function (i, e) {
            if ($(e).data('selected')) {
                var obj = {order: $(e).attr('order'), name: $(e).find('[col_name] input').val(), by: $(e).find('[col_by] select').val(), locator: $(e).find('[col_locator] input').val(), description: $(e).find('[col_description] input').val()};
                window.sub_muliple_selected_id.push(obj);
                $(e).css('background-color', 'lightblue');
            } else {
                $(e).css('background-color', '');
            }
        });
    }
	sub_multiple_operate_button_state()
}

// 全选
function bind_sub_multiple_select_all_button() {
    $('#element_table th[select_all]').off('click').click(function () {
        if (window.sub_muliple_selected_id.length > 0) {
            if (window.sub_muliple_selected_reverse) {
                $('#element_table tbody tr:not(#new_helper)').each(function (i, e) {
                    if ($(e).data('selected')) {
                        $(e).data('selected', false);
                    } else {
                        $(e).data('selected', true);
                    }
                });
                window.sub_muliple_selected_reverse = false;
            } else {
                $('#element_table tbody tr:not(#new_helper)').data('selected', false);
            }
		} else {
			$('#element_table tbody tr:not(#new_helper)').data('selected', true);
		}
	update_sub_muliple_selected();
    });
}

// 多选
function sub_multiple_select($td) {
    var tr = $td.parent('tr');
    window.sub_muliple_selected_reverse = true;

    if (!tr.data('selected')) {
        tr.data('selected', true);
    } else {
        tr.data('selected', false);
    }
    update_sub_muliple_selected();
}

// 注册多选功能
function bind_sub_multiple_select() {
	$('#element_table td[moveable]').off('click').on('click', function() { sub_multiple_select($(this)) });
}


// 批量删除对象
function sub_multiple_delete() {
	$.each(window.sub_muliple_selected_id, function(i, v) {
	    $('#element_table tbody tr[order='+ v.order +']').attr('deleting', true)
	});

	$('#element_table tbody tr[deleting]').fadeOut("slow", function() {
        $(this).remove();
        update_element_index_and_field();
    });

}

// 批量删除按钮
function bind_sub_multiple_delete_button() {
    $('#sub_multiple_delete_button').off('click').click(function () {
        var msg = '要删除<span class="mark">' + window.sub_muliple_selected_id.length + '</span>个对象吗？';
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
					sub_multiple_delete();
				}
			}
		});
    });
}

// 批量复制对象
function sub_multiple_copy_obj(text) {
    var msg = '当前选择了<span class="mark">' + window.sub_muliple_selected_id.length + '</span>个对象，请复制下列对象文本';
    var textarea = $('<textarea class="form-control" rows="10">').val(text);
	var copy_button = $('<button class="btn btn-warning"><i class="icon-copy">&nbsp;</i>复制文本</button>');
	copy_button.off('click').on('click', function () {
		textarea.select();
		var success = document.execCommand('copy');
		if (success) {
			toastr.success('复制成功');
		} else {
			toastr.error('浏览器不兼容，请手动复制文本');
		}
    });
    var _div = $('<div>').append(textarea).append('<br>').append(copy_button);
    var buttons = {
		canal: {
			label: '<i class="icon-remove">&nbsp;</i>关闭',
			className: 'btn btn-secondary'
		}
	};
    bootbox.dialog({
		size: 'large',
		title: '<i class="icon-exclamation-sign">&nbsp;</i>'+msg,
		message: _div,
		onEscape: true,
		backdrop: true,
		buttons: buttons
	});
}

// 注册批量复制对象按钮
function bind_sub_multiple_copy_obj_button() {
    $('#sub_multiple_copy_obj_button').off('click').click(function () {
        sub_multiple_copy_obj(JSON.stringify(window.sub_muliple_selected_id));
    });
}

// 添加批量对象到列表
function sub_multiple_paste_obj_link_to_list(data) {
	if (!data) {
	    toastr.error('没有填写对象文本');
		return false;
	}
	try {
		var objs = $.parseJSON(data);
	}
	catch (e) {
		toastr.error('无法识别的对象文本');
		return false;
    }
	var sub_objs = window.temp_sub_list;
    var last_select = sub_objs.length;
    if (window.sub_muliple_selected_id.length > 0) {
		last_select = parseInt(sub_muliple_selected_id[sub_muliple_selected_id.length-1].order);
	}
	$.each(objs, function (i, v) {
		sub_objs.splice(last_select, 0, {name: v.name, by: v.by, locator: v.locator, description: v.description});
		last_select++;
    });
	init_element(true, {data: sub_objs}, true);
}

// 批量粘贴对象
function sub_multiple_paste_obj() {
    var msg = '请粘贴对象文本然后点击生成，对象将被添加到当前选中的最后一行下面';
    var textarea = $('<textarea class="form-control" rows="10">');
    var buttons = {
		accept: {
			label: '<i class="icon-plus">&nbsp;</i>生成',
			className: 'btn btn-info',
			callback: function () { sub_multiple_paste_obj_link_to_list(textarea.val()) }
		}
	};
    bootbox.dialog({
		size: 'large',
		title: '<i class="icon-exclamation-sign">&nbsp;</i>'+msg,
		message: textarea,
		onEscape: true,
		backdrop: true,
		buttons: buttons
	});
}

// 注册批量粘贴对象按钮
function bind_sub_multiple_paste_obj_button() {
    $('#sub_multiple_paste_obj_button').off('click').click(function () {
        sub_multiple_paste_obj(JSON.stringify(window.sub_muliple_selected_id));
    });
}