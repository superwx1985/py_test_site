// 初始化
function init_step_ui_data_select(success, data) {
	if (success) {
		if (data.data.length > 0) {
			$.each(data.data, function (i, v) {
				if (v.all) {
					$('[name=ui_data_select_all]').prop("checked", true);
					return false;
				} else {
					var tr = $('<tr index=' + i + '></tr>');
					$('<td class="middle" col_move moveable></td>').appendTo(tr);
					$('<td class="middle" col_del><i class="icon-trash icon-2x" data-toggle="tooltip" title="删除"></i></td>').off('click').on(
						'click', function() { del_step_ui_data_select(tr) }).appendTo(tr);
					var span = $('<span></span>').text(i + 1);
					$('<td class="middle" col_index></td>').append(span).appendTo(tr);
					var select = $('<select class="form-control">');
					select.append('<option value="value">选项值</option>');
					select.append('<option value="text">选项文字</option>');
					select.append('<option value="index">选项索引</option>');
					select.val(v.select_by).off('change').on('change', function() { check_step_ui_data_select_select_by_select(tr) });
					$('<td col_select_by></td>').append(select).appendTo(tr);
					var input = $('<input placeholder="" class="form-control">').val(v.select_value).off('change').on('change', function () { update_step_ui_data_select() });
					$('<td col_select_value></td>').append(input).appendTo(tr);
					// 根据选项类型确定选项值输入框的限制
					check_step_ui_data_select_select_by_select(tr);
					tr.insertBefore($('#ui_data_select_table #new_helper'));
				}
			});
		}
		check_step_ui_data_select_all_checkbox();
		// 注册提示框
		$('[data-toggle=tooltip]').tooltip();
	}
}
// 添加
function add_step_ui_data_select() {
	var new_helper = $('#ui_data_select_table #new_helper');
	var name_input = $('#ui_data_select_table #new_helper td[col_select_value] input');
	name_input.removeClass('is-invalid');
	name_input.siblings('div.invalid-feedback').remove();
	var check_result = check_step_ui_data_select(new_helper);
	if (check_result === true) {
		var new_variable = new_helper.clone();
		// 去掉new_helper id 和 背景色
		new_variable.removeAttr('id').removeClass('bg-light');
		// 去掉新增按钮
		new_variable.children('td[col_move]').attr('moveable', '').empty();
		// 重新注册删除按钮事件
		new_variable.children('td[col_del]').off('click').on('click', function() { del_step_ui_data_select(new_variable) });
		// 重新注册标识类型选择事件
		new_variable.find('td[col_select_by] select').off('change').on('change', function() { check_step_ui_data_select_select_by_select(new_variable) });
        // 选项值无法复制，需要强制更新
        new_variable.find('td[col_select_by] select').val(new_helper.find('td[col_select_by] select').val());
        new_variable.find('td[col_select_value] input').off('change').on('change', function () { update_step_ui_data_select() });
		// 插入并淡入
		new_variable.insertBefore(new_helper).hide();
		new_variable.fadeIn("slow");
		name_input.val('').focus();
		update_step_ui_data_select();
		// 注册提示框
		$('[data-toggle=tooltip]').tooltip();
		return true;
    } else {
		get_invalid_input(name_input, check_result);
		return false;
	}

}
// 删除
function del_step_ui_data_select($tr) {
	var name = $tr.find('td[col_index] span').text();
	var msg = '要删除第<span class="mark">' + name + '</span>个选项吗？';
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
					update_step_ui_data_select();
				});
			}
		}
	});
}

// 验证
function check_step_ui_data_select($tr) {
	var value = $tr.find('td[col_select_value] input').val();
	var r = /^\d+$/;
	if ($tr.find('td[col_select_by] select').val() === 'index' && !r.test(value)) {
		return '请输入大于等于0的整数'
	}
	if (!value || ''===value.trim()) {
		return '不能为空'
	}
	return true;
}

// 更新变量列表序号，更新表单内容
function update_step_ui_data_select() {
	var trs = $('#ui_data_select_table tbody tr:not(#new_helper)');
	var variable_list = [];
	var _success = true;
	if ($('[name=ui_data_select_all]').prop("checked")) {
		variable_list.push({'all': true})
	} else {
		trs.each(function(i) {
			$(this).find('td[col_index] span').text(i+1);
			var name_input = $(this).find('td[col_select_value] input');
			var select_value = name_input.val();
			var check_result = check_step_ui_data_select($(this));
			name_input.removeClass('is-invalid');
			name_input.siblings('div.invalid-feedback').remove();
			if (check_result === true) {
				var select_by = $(this).find('td[col_select_by] select').val();
				var variable = {};
				variable.select_by = select_by;
				variable.select_value = select_value;
				variable_list.push(variable);
			} else {
				get_invalid_input(name_input, check_result);
				_success = false
			}
		});
	}
	var json_str = JSON.stringify(variable_list);
	$('textarea[name=ui_data]').val(json_str);
	return _success
}

// 检查是否有未保存的内容
function check_unsaved_step_ui_data_select() {
	var name = $('#ui_data_select_table #new_helper td[col_select_value] input').val();
	if (name !== '') {
		return name;
	} else {
		return false;
	}
}
// 检查全选复选框
function check_step_ui_data_select_all_checkbox() {
	if ($('[name=ui_data_select_all]').prop("checked")) {
		$('#ui_data_select_table').hide();
		$('#ui_data_select_table #new_helper td[col_select_value] input').val('');
	} else {
		$('#ui_data_select_table').show();
	}
}
// 检查select_by状态
function check_step_ui_data_select_select_by_select($tr) {
	if ($tr.find('td[col_select_by] select').val() === 'index') {
		$tr.find('td[col_select_value] input').attr('type', 'number').attr('min', '0');
	} else {
		$tr.find('td[col_select_value] input').removeAttr('type').removeAttr('min');
	}
}