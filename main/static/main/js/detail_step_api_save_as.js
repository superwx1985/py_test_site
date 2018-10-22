// 启用排序功能
function sortable_api_save_as() {
	$('#api_save_as_table tbody').sortable({
		items: "#api_save_as_table tr:not(#new_helper)",
		distance: 15,
		handle: "[moveable]",
		placeholder: 'ui-state-highlight',
		stop: function( event, ui ) {
			update_step_api_save_as();
		}
	});
}
// 更新变量列表
function init_step_api_save_as(success, data) {
	if (success) {
		if (data.data.length > 0) {
			$.each(data.data, function (i, v) {
				var tr = $('<tr></tr>');
				$('<td class="middle" col_move moveable><i class="icon-sort icon-2x"></i></td>').appendTo(tr);
				$('<td class="middle" col_del><i class="icon-trash icon-2x" data-toggle="tooltip" title="删除"></i></td>').off('click').on(
					'click', function() { del_step_api_save_as(tr) }).appendTo(tr);
				var span = $('<span></span>').text(i + 1);
				$('<td class="middle" col_index></td>').append(span).appendTo(tr);
				var input = $('<input placeholder="请输入变量名" class="form-control">').val(v.name).off('change').on('change', function () { update_step_api_save_as() });
				$('<td col_name></td>').append(input).appendTo(tr);
				var select = $('<select class="form-control">');
				select.append('<option value="header">Header</option>');
				select.append('<option value="body">Body</option>');
				select.val(v.part);
				$('<td col_part></td>').append(select).appendTo(tr);
				var input = $('<input placeholder="" class="form-control">').val(v.expression);
				$('<td col_expression></td>').append(input).appendTo(tr);
				tr.insertBefore($('#api_save_as_table #new_helper'));
			});
		}
		update_step_api_save_as();
		// 注册提示框
		$('[data-toggle=tooltip]').tooltip();
	}
}
// 添加变量
function add_step_api_save_as() {
	var new_helper = $('#api_save_as_table #new_helper');
	var name_input = $('#api_save_as_table #new_helper td[col_name] input');
	name_input.removeClass('is-invalid');
	name_input.siblings('div.invalid-feedback').remove();
	var check_result = check_api_save_as_name(name_input.val(), get_api_save_as_name_list());
	if (check_result === true) {
		var new_variable = new_helper.clone();
		// 去掉new_helper id 和 背景色
		new_variable.removeAttr('id').removeClass('bg-light');
		// 改变新增按钮为排序按钮
		new_variable.children('td[col_move]').attr('moveable', '').empty().append('<i class="icon-sort icon-2x"></i>');
		// 重新注册删除按钮事件
		new_variable.children('td[col_del]').off('click').on('click', function() { del_step_api_save_as(new_variable) });
		new_variable.find('td[col_name] input').off('change').on('change', function () { update_step_api_save_as() });
		// 选项值无法复制，需要强制更新
		new_variable.find('td[col_part] select').val(new_helper.find('td[col_part] select').val());
		// 插入并淡入
		new_variable.insertBefore(new_helper).hide();
		new_variable.fadeIn("slow");
		name_input.val('').focus();
		$('#api_save_as_table #new_helper td[col_expression] input').val('');
		update_step_api_save_as();
		// 注册提示框
		$('[data-toggle=tooltip]').tooltip();
		return true;
	} else {
		get_invalid_input(name_input, check_result);
		return false;
	}
}
// 删除变量
function del_step_api_save_as($tr) {
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
					update_step_api_save_as();
				});
			}
		}
	});
}
// 获取当前变量名列表
function get_api_save_as_name_list() {
	var trs = $('#api_save_as_table tbody tr:not(#new_helper)');
	var variable_name_list = [];
	trs.each(function(i) {
		variable_name_list.push($(this).find('td[col_name] input').val());
	});
	return variable_name_list;
}
// 验证变量名
function check_api_save_as_name(name, variable_name_list_) {
	if (!name || ''===name.trim()) {
		return '变量名不能为空'
	}
	var index = $.inArray(name, variable_name_list_);
	if (index >= 0) {
		return '与第[' + (index + 1) + ']个变量重名'
	}
	return true;
}

// 更新变量列表序号，更新表单内容
function update_step_api_save_as() {
	var trs = $('#api_save_as_table tbody tr:not(#new_helper)');
	var variable_list = [];
	var variable_name_list = [];
	var _success = true;
	trs.each(function(i) {
		$(this).find('td[col_index] span').text(i+1);
		var name_input = $(this).find('td[col_name] input');
		var name = name_input.val();
		var check_result = check_api_save_as_name(name, variable_name_list);
		name_input.removeClass('is-invalid');
		name_input.siblings('div.invalid-feedback').remove();
		if (check_result === true) {
			var part = $(this).find('td[col_part] select').val();
			var expression = $(this).find('td[col_expression] input').val();
			var variable = {};
			variable.name = name;
			variable.part = part;
			variable.expression = expression;
			variable_list.push(variable);
			variable_name_list.push(name);
		} else {
			get_invalid_input(name_input, check_result);
			_success = false
		}
	});
	var json_str = JSON.stringify(variable_list);
	$('input[name=api_save]').val(json_str);
	return _success;
}
// 检查是否有未保存的变量
function check_unsaved_step_api_save_as() {
	var name = $('#api_save_as_table #new_helper td[col_name] input').val();
	if (name !== '') {
		return name;
	} else {
		return false;
	}
}