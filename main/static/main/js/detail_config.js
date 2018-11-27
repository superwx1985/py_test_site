// 处理驱动类型关联项
function show_ui_selenium_client_related($select) {
	if ($select.val() == 1) {
		$('#ui_config').find('select:not(#id_ui_selenium_client),input').removeAttr('readonly');
		$('#id_ui_remote_ip').attr('readonly', true);
		$('#id_ui_remote_port').attr('readonly', true);
		show_ui_window_size_related($('#id_ui_window_size'));
	} else if ($select.val() == 2) {
		$('#ui_config').find('select:not(#id_ui_selenium_client),input').removeAttr('readonly');
		$('#id_ui_remote_ip').removeAttr('readonly');
		$('#id_ui_remote_port').removeAttr('readonly');
		show_ui_window_size_related($('#id_ui_window_size'));
	} else {
		$('#ui_config').find('select:not(#id_ui_selenium_client),input').attr('readonly', true);
	}
}

// 处理窗口关联项
function show_ui_window_size_related($select) {
	if ($select.val() == 1) {
		$('#id_ui_window_width').attr('disabled', true);
		$('#id_ui_window_height').attr('disabled', true);
		$('#id_ui_window_position_x').attr('disabled', true);
		$('#id_ui_window_position_y').attr('disabled', true);
	} else {
		$('#id_ui_window_width').removeAttr('disabled');
		$('#id_ui_window_height').removeAttr('disabled');
		$('#id_ui_window_position_x').removeAttr('disabled');
		$('#id_ui_window_position_y').removeAttr('disabled');
	}
}