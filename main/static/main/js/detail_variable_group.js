// 启用排序功能
function sortable_variable() {
	$('#variable_table tbody').sortable({
		items: "tr:not(#new_helper)",
		distance: 15,
		handle: "[moveable]",
		placeholder: 'ui-state-highlight',
		stop: function( event, ui ) {
			update_variable_index_and_field();
		}
	});
}
// 更新变量列表
function variable_update(success, data) {
	if (success) {
		if (data.data.length > 0) {
			$.each(data.data, function (i, v) {
				var tr = $('<tr></tr>');
				$('<td class="middle" col_move moveable><i class="icon-sort icon-2x"></i></td>').appendTo(tr);
				$('<td class="middle" col_del><i class="icon-trash icon-2x" data-toggle="tooltip" title="删除"></i></td>').off('click').on(
					'click', function() { del_variable(tr) }).appendTo(tr);
				var span = $('<span></span>').text(i + 1);
				$('<td index class="middle" col_index></td>').append(span).appendTo(tr);
				var input = $('<input placeholder="请输入变量名" class="form-control">').val(v.name).off('change').on('change', function () { update_variable_index_and_field() });
				$('<td col_name></td>').append(input).appendTo(tr);
				var input = $('<input placeholder="请输入变量值" class="form-control">').val(v.value);
				$('<td col_value></td>').append(input).appendTo(tr);
				var input = $('<input placeholder="" class="form-control">').val(v.description);
				$('<td col_description></td>').append(input).appendTo(tr);
				tr.insertBefore($('#new_helper'));
			});
		}
		update_variable_index_and_field();
		// 注册提示框
		$('[data-toggle=tooltip]').tooltip();
	}
}
// 添加变量
function addVariable() {
	var new_helper = $('#new_helper');
	var name_input = $('#new_helper td[col_name] input');
	name_input.removeClass('is-invalid');
	name_input.siblings('div.invalid-feedback').remove();
	var check_result = check_variable_name(name_input.val(), get_variable_name_list_());
	if (check_result === true) {
		var new_variable = new_helper.clone();
		// 去掉new_helper id 和 背景色
		new_variable.removeAttr('id').removeClass('bg-light');
		// 改变新增按钮为排序按钮
		new_variable.children('td[col_move]').attr('moveable', '').empty().append('<i class="icon-sort icon-2x"></i>');
		// 重新注册删除按钮事件
		new_variable.children('td[col_del]').off('click').on('click', function() { del_variable(new_variable) });
		new_variable.find('td[col_name] input').off('change').on('change', function () { update_variable_index_and_field() });
		// 插入并淡入
		new_variable.insertBefore(new_helper).hide();
		new_variable.fadeIn("slow");
		$('#new_helper td[col_name] input').val('').focus();
		$('#new_helper td[col_value] input').val('');
		$('#new_helper td[col_description] input').val('');
		update_variable_index_and_field();
		// 注册提示框
		$('[data-toggle=tooltip]').tooltip();
		return true;
	} else {
		get_invalid_input(name_input, check_result);
		return false;
	}
}
// 删除变量
function del_variable($tr) {
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
					update_variable_index_and_field();
				});
			}
		}
	});
}
// 获取当前变量名列表
function get_variable_name_list_() {
	var trs = $('#variable_table tbody tr:not(#new_helper)');
	var variable_name_list = [];
	trs.each(function(i) {
		variable_name_list.push($(this).find('td[col_name] input').val());
	});
	return variable_name_list;
}
// 验证变量名
function check_variable_name(name, variable_name_list_) {
	if (!name || ''===name.trim()) {
		return '变量名不能为空'
	}
	var index = $.inArray(name, variable_name_list_);
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
// 更新变量列表序号，更新variable field内容
function update_variable_index_and_field() {
	var trs = $('#variable_table tbody tr:not(#new_helper)');
	var variable_list = [];
	var variable_name_list = [];
	trs.each(function(i) {
		$(this).find('td[col_index] span').text(i+1);
		var name_input = $(this).find('td[col_name] input');
		var name = name_input.val();
		var check_result = check_variable_name(name, variable_name_list);
		name_input.removeClass('is-invalid');
		name_input.siblings('div.invalid-feedback').remove();
		if (check_result === true) {
			var value = $(this).find('td[col_value] input').val();
			var description = $(this).find('td[col_description] input').val();
			var variable = {};
			variable.name = name;
			variable.value = value;
			variable.description = description;
			variable_list.push(variable);
			variable_name_list.push(name);
		} else {
			get_invalid_input(name_input, check_result);
		}
	});
	var json_str = JSON.stringify(variable_list);
	$('input[name=variable]').val(json_str);
	// 关闭遮罩
	$('#mask').hide();
}
// 检查是否有未保存的变量
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
					if (addVariable()) {
						$('#object_form').removeAttr('onsubmit').submit();
					}
				}
			}
		});
	} else {
		update_variable_index_and_field();
		$('#object_form').removeAttr('onsubmit').submit();
	}
	return false;
}