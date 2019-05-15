// 更新变量组下拉项
function update_variable_group_dropdown(success, data) {
	if (success) {
		if (window.editable) {
			update_dropdown(data, $("#variable_group_dropdown"));
		} else {
			update_dropdown(data, $("#variable_group_dropdown"), true);
		}
		update_mask($('#mask'), -1);
    } else {
		console.log(data);
		if (!window.errs) { window.errs = [] }
		window.errs.push(data);
	}
}

// 更新元素组下拉项
function update_element_group_dropdown(success, data) {
	if (success) {
		if (window.editable) {
			update_dropdown(data, $("#element_group_dropdown"));
		} else {
			update_dropdown(data, $("#element_group_dropdown"), true);
		}
		update_mask($('#mask'), -1);
    } else {
		console.log(data);
		if (!window.errs) { window.errs = [] }
		window.errs.push(data);
	}
}

// 更新配置下拉项
function update_config_dropdown(success, data) {
	if (success) {
		if (window.editable) {
			update_dropdown(data, $("#config_dropdown"));
		} else {
			update_dropdown(data, $("#config_dropdown"), true);
		}
		update_mask($('#mask'), -1);
    } else {
		console.log(data);
		if (!window.errs) { window.errs = [] }
		window.errs.push(data);
	}
}

// 更新子用例下拉项
function update_other_sub_case_dropdown(success, data) {
	if (success) {
		if (window.editable) {
			update_dropdown(data, $("#other_sub_case_dropdown"));
		} else {
			update_dropdown(data, $("#other_sub_case_dropdown"), true);
		}
		update_mask($('#mask'), -1);
    } else {
		console.log(data);
		if (!window.errs) { window.errs = [] }
		window.errs.push(data);
	}
}

// 更新动作下拉项
function update_action_dropdown(success, data) {
	if (success) {
		if (window.editable) {
			update_dropdown(data, $("#action_dropdown"));
		} else {
			update_dropdown(data, $("#action_dropdown"), true);
		}
		// 触发展示action相关内容
		show_action_field($('select[name="action"]'));
		// 注册action变更
		$('select[name="action"]').off('change').change(function () {
			show_action_field($(this));
		});
		update_mask($('#mask'), -1);
    } else {
		console.log(data);
		if (!window.errs) { window.errs = [] }
		window.errs.push(data);
	}
}


function m2m_detail_popup(title, url, parent_project) {
	if (parent_project) { url=url+'&parent_project='+parent_project }
	modal_with_iframe_max('inside_detail_modal', title, url, '', update_m2m_objects)
}

// 更新已选m2m的序号，更新m2m field内容
function update_m2m_selected_index_and_field($input, title, multiple_select) {
	var m2m = $('#m2m_selected_table tbody tr:not([placeholder])');
	// var m2m_list = $('#m2m_selected_table tbody').sortable('toArray', {attribute: "pk"});  // 获取可排序对象的pk列表，不能使用该方法，因为只读页面的列表不是可排序对象
    var m2m_list = [];

	m2m.each(function(i) {
		$(this).children('[index]').text(i+1);
		$(this).attr('order', i+1);
		var href = "javascript:m2m_detail_popup('" + title + "','" + $(this).attr('url') + "?inside=1&order=" + (i+1) + "')";
		$(this).find('[name]>a').attr('href', href);
		m2m_list.push($('#m2m_selected_table tbody tr[order="'+(i+1)+'"]').attr('pk'));
	});
	var json_str = JSON.stringify(m2m_list);
	$input.val(json_str);
	if (window.editable) {
		bind_m2m_multiple_select();
	}
	update_m2m_muliple_selected(multiple_select);
}

// 处理m2m拖动及排序
function m2m_handle($input, title) {
	if (!window.editable) { return }
	$('#m2m_selected_table tbody').sortable({
		items: "tr:not([placeholder])",
		distance: 15,
		handle: "[moveable]",
		placeholder: 'ui-state-highlight',
		stop: function( event, ui ) {
			var from_all_table = false;
			if (ui.item.hasClass('from_all_table')) {
				from_all_table = true;
				ui.item.removeClass('from_all_table');
			}
            // 如果拖动的是连续的多选，将进行整体移动
			if (!from_all_table && m2m_muliple_selected_id.length > 1) { //  && m2m_muliple_selected_id.indexOf(ui.item.attr('order')) > -1
				var old_muliple_selected_id = window.m2m_muliple_selected_id;
				var old_start = parseInt(m2m_muliple_selected_id[0].order);
				var old_end = parseInt(m2m_muliple_selected_id[m2m_muliple_selected_id.length-1].order);
				var old_order = parseInt(ui.item.attr('order'));

				if (old_start <= old_order && old_order <= old_end && old_end === old_start+m2m_muliple_selected_id.length-1) {
					var old_selected_element = [];
					$.each(old_muliple_selected_id, function (i, v) {
                       	old_selected_element.push($('#m2m_selected_table tr[order=' + v.order + ']'))
                    });
                    update_m2m_selected_index_and_field($input, title);
                    var new_order = parseInt(ui.item.attr('order'));

                    if (new_order < old_start || new_order > old_end) {
						var target_tr = ui.item;
						do {
							var tr = old_selected_element.pop();
							target_tr.before(tr);
							target_tr = tr;
						} while(old_selected_element.length);
                    }
				}
			}
			update_m2m_selected_index_and_field($input, title);
		}
	});
	$('#m2m_selected_table tbody').droppable({
		activeClass: 'ui-state-default',
		hoverClass: 'ui-state-hover',
		accept: 'tr',
		scope: "m2m_all",
		drop: function (event, ui) {
			$(this).children('[placeholder]').remove();
		}
	});
	$('#m2m_all_table tbody').droppable({
		hoverClass: 'ui-state-hover',
		accept: '#m2m_selected_table tr:not([placeholder])',
		drop: function (event, ui) {
			ui.draggable.remove();
			if ($('#m2m_selected_table tbody tr').length <= 1) {
				$('#m2m_selected_table tbody').append($('<tr placeholder><td colspan=' + $('#m2m_selected_table thead th').length + ' class="text-center bg-secondary"><span class="text-white">无数据</span></td></tr>'));
			}
		}
	})
}

// 更新并注册分页工具
function update_and_bind_paginator(page, max_page, size) {
	var page_input = $('input[name=page]');
	var form = $('#m2m_objects_form');
	page_input.val(page);
	page_input.attr('max', max_page);
	$('span[name=total_text]').text(' / ' + max_page);
	$('input[name=size]').val(size).data('max_page', max_page);

	var button = $("button[name=first_page_button]");
	if (page === 1) {
		button.addClass('disabled')
	} else {
		button.removeClass('disabled').off('click').on('click', function () {
			page_input.val(1);
			form.submit();
		});
	}
	var button = $("button[name=prev_page_button]");
	if (page === 1) {
		button.addClass('disabled')
	} else {
		button.removeClass('disabled').off('click').on('click', function () {
			page_input.val(page - 1);
			form.submit();
		});
	}
	var button = $("button[name=next_page_button]");
	if (page === max_page) {
		button.addClass('disabled')
	} else {
		button.removeClass('disabled').off('click').on('click', function () {
			page_input.val(page +1);
			form.submit();
		});
	}
	var button = $("button[name=last_page_button]");
	if (page === max_page) {
		button.addClass('disabled')
	} else {
		button.removeClass('disabled').off('click').on('click', function () {
			page_input.val(max_page);
			form.submit();
		});
	}
}

// 获取待选m2m
function submit_m2m_all_objects_form(cookie_path, json_url, last_condition_json) {
	$('#m2m_all_mask').show();
	var condition_json = '{}';
	// 如果传入了上次的条件，则使用上次的条件初始化搜索信息
	if (last_condition_json) {
		var last_condition = {};
		try {
			last_condition = $.parseJSON(last_condition_json);
			condition_json = last_condition_json;
		}
		catch (e) {
			console.log(e);
		}
		$('input[name=search_text]').val(last_condition.search_text);
		if (last_condition.search_project === '') {
			$('select[name=search_project]').val('');
		} else {
			$('select[name=search_project]').val(last_condition.search_project);
		}
		if (last_condition.all_ === 'True') {
			$('input[name=all_]').prop('checked', true);
		} else {
			$('input[name=all_]').prop('checked', false);
		}
		if (last_condition.order_by) {
			var order_by = last_condition.order_by;
		} else {
			var order_by = 'modified_date';
		}
		$('input[name=order_by]').val(order_by);
		if (last_condition.order_by_reverse) {
			var order_by_reverse = last_condition.order_by_reverse;
		} else {
			var order_by_reverse = 'True';
		}
		$('input[name=order_by_reverse]').val(order_by_reverse);
	} else {
		var page = $('input[name=page]').val();
		var size = $('input[name=size]').val();
		var max_page = $('input[name=size]').data('max_page');
		var search_text = $('input[name=search_text]').val();
		if ($('input[name=all_]').prop('checked')) {
			var all_ = 'True';
		} else {
			var all_ = 'False';
		}
		var search_project = $('select[name=search_project]').val();
		if ($('input[name=order_by]').val()) {
			var order_by = $('input[name=order_by]').val();
		} else {
			var order_by = 'modified_date';
			$('input[name=order_by]').val(order_by)
		}
		if ($('input[name=order_by_reverse]').val()) {
			var order_by_reverse = $('input[name=order_by_reverse]').val();
		} else {
			var order_by_reverse = 'True';
			$('input[name=order_by_reverse]').val(order_by_reverse)
		}
		var condition = {
			'page': page,
			'size': size,
			'max_page': max_page,
			'search_text': search_text,
			'all_': all_,
			'search_project': search_project,
			'order_by_reverse': order_by_reverse,
			'order_by': order_by
		};
		condition_json = JSON.stringify(condition);
	}
	set_cookie('last_condition_json', condition_json, 0, cookie_path);
	getList(json_url, window.$csrf_input.val(), update_m2m_list_all, condition_json);
	return false;
}

// 更新排序标志
function update_sort_icon() {
	$('#m2m_all_table th[order_by_text]').find('i').remove();
	var sort_col = $('#m2m_all_table th[order_by_text=' + $('input[name=order_by]').val() + ']');
	if ($('input[name=order_by_reverse]').val() === 'True') {
		sort_col.prepend('<i class="icon-circle-arrow-down">&nbsp;</i>');
	} else {
		sort_col.prepend('<i class="icon-circle-arrow-up">&nbsp;</i>');
	}
}

// m2m列表排序
function m2m_sort(order_by_text) {
	var order_by = $('input[name=order_by]');
	var order_by_reverse = $('input[name=order_by_reverse]');
	if (order_by.val() === order_by_text) {
		if (order_by_reverse.val() === 'True') {
			order_by_reverse.val('False');
		} else {
			order_by_reverse.val('True');
		}
	} else {
		order_by_reverse.val('False');
		order_by.val(order_by_text);
	}
	update_sort_icon();
	$('#m2m_objects_form').submit();
}

// 新增m2m主键到m2m字段
function add_m2m($input, pk) {
	var m2m_list = $.parseJSON($input.val());
	m2m_list.push(String(pk));
	$input.val(JSON.stringify(m2m_list))
}

// 替换m2m字段里被复制的主键
function replace_m2m($input, pk, order) {
	var m2m_list = $.parseJSON($input.val());
	m2m_list.splice(order-1, 1, String(pk));
	$input.val(JSON.stringify(m2m_list))
}

// 禁用所有互动
function disable_interaction() {
	$('#object_form input, #object_form textarea, #object_form select').attr('disabled', true);
	$('tr#new_helper').hide();
	$('td[col_del]').empty().off('click');
	$('td[col_move]').empty().off('click');
	$('[j_dropdown]').each(function(){$(this).data('dropdown').changeStatus('readonly')});
    $('#m2m_selected_button_group button').off('click').attr('disabled', true);
	$('#m2m_selected_table th, #m2m_selected_table td').off('click');
    $('#sub_button_group button').off('click').attr('disabled', true);
    $('#variable_table th, #variable_table td, #variable_table input, #variable_table select').off('click').attr('disabled', true);
	$('#element_table th, #element_table td, #element_table input, #element_table select').off('click').attr('disabled', true);
}

// 复制对象的回调函数
function callback_copy_obj(copy_url, name_prefix, order) {
	copy_obj_post(copy_url, name_prefix, null, order)
}

// 复制对象及子对象的的回调函数
function callback_copy_obj_sub_item(copy_url, name_prefix, order) {
	copy_obj_post(copy_url, name_prefix, 1, order)
}

// 复制对象
function copy_obj_post(copy_url, name_prefix, copy_sub_item, order) {
	$('#mask').show();
	$.post(copy_url, {'csrfmiddlewaretoken': $csrf_input.val(), 'name_prefix': name_prefix, 'copy_sub_item': copy_sub_item, 'order': order}, function(data) {
		$('#mask').hide();
		if (data.state === 1) {
            // 如果返回包含有效order，则添加new_pk及order至参数，用于内嵌窗口复制后更新m2m列表
            if (data.data.order > 0) {
				window.open(data.data.new_url + window.location.search + '&new_pk=' + data.data.new_pk + '&order=' + data.data.order, '_self');
			} else {
				window.open(data.data.new_url + window.location.search, '_self');
			}
        } else {
			bootbox.alert('<span class="text-danger">'+data.message+'</span>');
        }
	});
}

// m2m批量操作按钮状态
function m2m_multiple_operate_button_state() {
    if (window.m2m_muliple_selected_id.length > 0) {
        $('#m2m_multiple_delete_button').removeAttr('disabled');
        $('#m2m_multiple_copy_obj_button').removeAttr('disabled');
    } else {
        $('#m2m_multiple_delete_button').attr('disabled', true);
        $('#m2m_multiple_copy_obj_button').attr('disabled', true);
    }
}

// m2m多选列表刷新
function update_m2m_muliple_selected(multiple_select) {
	if (multiple_select) {  // 通过m2m_muliple_selected_id更新列表
		$('#m2m_selected_table tr[pk]').data('selected', false).css('background-color', '');
		$.each(window.m2m_muliple_selected_id, function(i, v) {
			$('#m2m_selected_table tbody tr[order='+ v.order +']').data('selected', true).css('background-color', 'lightblue');
		});
	} else {  // 通过列表更新m2m_muliple_selected_id
		window.m2m_muliple_selected_id = [];
		$('#m2m_selected_table tr[pk]').each(function (i, e) {
			if ($(e).data('selected')) {
				// window.m2m_muliple_selected_id.push($(e).attr('order'));
				var obj = {order: $(e).attr('order'), pk: $(e).attr('pk')};
				window.m2m_muliple_selected_id.push(obj);
				$(e).css('background-color', 'lightblue');
			} else {
				$(e).css('background-color', '');
			}
		});
	}
	m2m_multiple_operate_button_state()
}

// m2m全选
function bind_m2m_select_all_button() {
    $('#m2m_selected_table th[select_all]').off('click').click(function () {
        if (window.m2m_muliple_selected_id.length > 0) {
            if (window.m2m_muliple_selected_reverse) {
                $('#m2m_selected_table tr[pk]').each(function (i, e) {
                    if ($(e).data('selected')) {
                        $(e).data('selected', false);
                    } else {
                        $(e).data('selected', true);
                    }
                });
                window.m2m_muliple_selected_reverse = false;
            } else {
                $('#m2m_selected_table tr[pk]').data('selected', false);
            }
		} else {
			$('#m2m_selected_table tr[pk]').data('selected', true);
		}
	update_m2m_muliple_selected();
    });
}

// m2m多选
function m2m_multiple_select($td) {
    var tr = $td.parent('tr');
    window.m2m_muliple_selected_reverse = true;

    if (!tr.data('selected')) {
        tr.data('selected', true);
    } else {
        tr.data('selected', false);
    }
    update_m2m_muliple_selected();
}

// 注册m2m多择功能
function bind_m2m_multiple_select() {
	$('#m2m_selected_table td[moveable]').off('click').on('click', function() { m2m_multiple_select($(this)) });
}

// 批量删除m2m对象
function m2m_multiple_delete() {
	$.each(window.m2m_muliple_selected_id, function(i, v) {
	    $('#m2m_selected_table tbody tr[order='+ v.order +']').attr('deleting', true)
	});

	$('#m2m_selected_table tbody tr[deleting]').fadeOut("slow", function() {
        $(this).remove();
        update_m2m_selected_index_and_field(window.$m2m_input, '步骤详情');
        if ($('#m2m_selected_table tbody tr').length < 1) {
			$('#m2m_selected_table tbody').append($('<tr placeholder><td colspan=' + $('#m2m_selected_table thead th').length + ' class="text-center bg-secondary"><span class="text-white">无数据</span></td></tr>'));
		}
    });

}

// m2m批量删除按钮
function bind_m2m_multiple_delete_button() {
    $('#m2m_multiple_delete_button').off('click').click(function () {
        var msg = '要删除<span class="mark">' + window.m2m_muliple_selected_id.length + '</span>个对象吗？';
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
                    m2m_multiple_delete();
                }
            }
        });
    });
}

// m2m批量复制对象
function m2m_multiple_copy_obj(text) {
    var msg = '当前选择了<span class="mark">' + window.m2m_muliple_selected_id.length + '</span>个对象，请复制下列对象文本';
    var textarea = $('<textarea class="form-control" rows="5">').val(text);
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

// 注册m2m批量复制对象按钮
function bind_m2m_multiple_copy_obj_button() {
    $('#m2m_multiple_copy_obj_button').off('click').click(function () {
        m2m_multiple_copy_obj(JSON.stringify(window.m2m_muliple_selected_id));
    });
}

// m2m添加批量对象到列表
function add_m2m_multiple_paste_obj_to_list(data) {
	if (!data) {
		return false;
	}
	try {
		var objs = $.parseJSON(data);
	}
	catch (e) {
		toastr.error('无法识别的对象文本');
		return false;
    }
	var m2m_objs = $.parseJSON(window.$m2m_input.val());
    var last_select = m2m_objs.length;
    if (window.m2m_muliple_selected_id.length > 0) {
		last_select = parseInt(m2m_muliple_selected_id[m2m_muliple_selected_id.length-1].order);
	}
	$.each(objs, function (i, v) {
		m2m_objs.splice(last_select, 0, v.pk);
		last_select++;
    });
	window.$m2m_input.val(JSON.stringify(m2m_objs));
	update_m2m_objects();
}

// m2m批量粘贴对象
function m2m_multiple_paste_obj() {
    var msg = '请粘贴对象文本然后点击确认，对象将被添加到当前选中的最后一行下面';
    var textarea = $('<textarea class="form-control" rows="5">');
    var buttons = {
		accept: {
			label: '<i class="icon-ok">&nbsp;</i>确定',
			className: 'btn btn-primary',
			callback: function () { add_m2m_multiple_paste_obj_to_list(textarea.val()) }
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

// 注册m2m批量粘贴对象按钮
function bind_m2m_multiple_paste_obj_button() {
    $('#m2m_multiple_paste_obj_button').off('click').click(function () {
        m2m_multiple_paste_obj(JSON.stringify(window.m2m_muliple_selected_id));
    });
}
