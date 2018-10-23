// 更新下拉项
function update_dropdown(data, $base_div, readonly) {
	$base_div.empty();
	var name = $base_div.attr('name');
	var div_dropdown = $('<div j_dropdown><select style="display: none" placeholder="请选择" name="' + name + '"></select></div>');
	$base_div.append(div_dropdown);
	div_dropdown.j_dropdown({
		data: data.data,
		//multipleMode: 'label',
		//limitCount: 1,
		input: '<input type="text" maxLength="20" placeholder="筛选">',
		choice: function() {
			// console.log(this.selectId);
			// window._selectId = JSON.stringify(this.selectId);
		}
	});
	if (readonly) {
		div_dropdown.data('dropdown').changeStatus('readonly')
	}
}

// 更新变量组下拉项
function update_variable_groups_dropdown(success, data) {
	if (success) {
		if (window.editable) {
			update_dropdown(data, $("#variable_group_dropdown"));
		} else {
			update_dropdown(data, $("#variable_group_dropdown"), true);
		}
    } else {
		console.log(data);
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
    } else {
		console.log(data);
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

    } else {
		console.log(data);
	}
}

function m2m_detail_popup(title, url) {
	modal_with_iframe_max('m2m_detail_modal', title, url, '', update_m2m_objects)
}

// 更新已选m2m的序号，更新m2m field内容
function update_m2m_selected_index_and_field($input, title) {
	var m2m = $('#m2m_selected tbody tr:not([placeholder])');
	var m2m_list = [];

	m2m.each(function(i) {
		$(this).children('[index]').text(i+1);
		var href = "javascript:m2m_detail_popup('" + title + "','" + $(this).attr('url') + "?inside=1&order=" + (i+1) + "')";
		$(this).find('[name]>a').attr('href', href);
		m2m_list.push($(this).attr('pk'));
	});
	var json_str = JSON.stringify(m2m_list);
	$input.val(json_str);
}

// 处理m2m拖动及排序
function m2m_handle($input, col, title) {
	if (!window.editable) { return }
	$('#m2m_selected tbody').sortable({
		items: "tr:not([placeholder])",
		distance: 15,
		handle: "[moveable]",
		placeholder: 'ui-state-highlight',
		stop: function( event, ui ) {
			update_m2m_selected_index_and_field($input, title);
		}
	});
	$('#m2m_selected tbody').droppable({
		activeClass: 'ui-state-default',
		hoverClass: 'ui-state-hover',
		accept: 'tr',
		scope: "m2m_all",
		drop: function (event, ui) {
			$(this).children('[placeholder]').remove();
		}
	});
	$('#m2m_all tbody').droppable({
		hoverClass: 'ui-state-hover',
		accept: '#m2m_selected tr:not([placeholder])',
		drop: function (event, ui) {
			ui.draggable.remove();
			if ($('#m2m_selected tbody tr').length <= 1) {
				$('#m2m_selected tbody').append($('<tr placeholder><td colspan=' + col + ' class="text-center bg-secondary"><span class="text-white">无数据</span></td></tr>'));
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
	$('#m2m_all th[order_by_text]').find('i').remove();
	var sort_col = $('#m2m_all th[order_by_text=' + $('input[name=order_by]').val() + ']');
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
	console.log($input, pk);
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
	$('input,textarea,select').attr('disabled', true);
	$('tr#new_helper').hide();
	$('td[col_del]').empty().off('click');
	$('td[col_move]').empty().off('click');
	$('[j_dropdown]').each(function(){$(this).data('dropdown').changeStatus('readonly')});
	$('#m2m_add_button').off('click');
	//$('#m2m_all tbody tr').draggable('option', 'disabled');
	//$('#m2m_selected tbody').sortable('option', 'disabled');
	//$('#m2m_selected tbody').droppable('option', 'disabled');
}
