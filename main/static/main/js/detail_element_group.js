// 启用排序功能
function sortable_element() {
	$('#element_table tbody').sortable({
		items: "tr:not(#new_helper)",
		distance: 15,
		handle: "[moveable]",
		placeholder: 'ui-state-highlight',
		stop: function( event, ui ) {
			update_element_index_and_field();
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
function init_element(success, data) {
	if (success) {
		if (data.data.length > 0) {
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
		update_element_index_and_field();
		// 注册提示框
		$('[data-toggle=tooltip]').tooltip();
	}
	if (!window.editable) {
		// 禁用所有互动
		disable_interaction();
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
	trs.each(function(i) {
		name_list.push($(this).find('td[col_name] input').val());
	});
	return name_list;
}

// 验证名称
function check_element_name(name, name_list_) {
	if (!name || ''===name.trim()) {
		return '变量名不能为空'
	}
	var index = $.inArray(name, name_list_);
	if (index >= 0) {
		return '与第[' + (index + 1) + ']个变量重名'
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
function update_element_index_and_field() {
	var trs = $('#element_table tbody tr:not(#new_helper)');
	var _list = [];
	var name_list = [];
	trs.each(function(i) {
		$(this).find('td[col_index] span').text(i+1);
		var name_input = $(this).find('td[col_name] input');
		var name = name_input.val();
		var check_result = check_element_name(name, name_list);
		name_input.removeClass('is-invalid');
		name_input.siblings('div.invalid-feedback').remove();
		if (check_result === true) {
			var by = $(this).find('td[col_by] select').val();
			var locator = $(this).find('td[col_locator] input').val();
			var description = $(this).find('td[col_description] input').val();
			var element = {};
			element.name = name;
			element.by = by;
			element.locator = locator;
			element.description = description;
			_list.push(element);
			name_list.push(name);
		} else {
			get_invalid_input(name_input, check_result);
		}
	});
	var json_str = JSON.stringify(_list);
	$('input[name=element]').val(json_str);
	// 关闭遮罩
	$('#mask').hide();
}

// 检查是否有未保存的对象
function check_unsaved() {
	var name = $('#new_helper td[col_name] input').val();
	if (name !== '') {
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