// 更新下拉项
function update_dropdown(data, $base_div) {
	$base_div.empty();
	var name = $base_div.attr('name');
	var div_dropdown = $('<div><select style="display: none" placeholder="请选择" name="' + name + '"></select></div>');
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
}

// 更新变量组下拉项
function update_variable_groups_dropdown(success, data) {
	if (success) {
		update_dropdown(data, $("#variable_group_dropdown"));
    }
}

// 更新配置下拉项
function update_config_dropdown(success, data) {
	if (success) {
		update_dropdown(data, $("#config_dropdown"));
    }
}

// m2m详情页
function m2m_detail_popup(url) {
	var my_modal = $('[name=my_modal]');
	var my_modal_body = my_modal.find('.modal-body');
	var body_height = $(window).height() - get_element_outside_height(my_modal.find('.modal-dialog')) - get_element_outside_height(my_modal.find('.modal-content')) - get_element_outside_height(my_modal_body);
	var body_min_height = 600;
	var modal_body_div = '<div style="height: 100%;"><iframe name="m2m_iframe" frameborder="0" style="height: 100%; width: 100%;" src="' + url + '"></iframe></div>';
	my_modal.find('.modal-header').remove();
	my_modal_body.empty().css('height', body_height).css('min-height', body_min_height).append(modal_body_div);
	my_modal.find('.modal-footer').remove();
	my_modal.off('hide.bs.modal').on('hide.bs.modal', function () {
		update_m2m_objects();
	});
	my_modal.modal()
}