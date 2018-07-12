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