// 获取详情
function get_detail() {
	$.ajax({
		url: window._request_url,
		type: "POST",
		data: {"operate": "get_detail", "id": window._id},
		dataType: "html",
		success: function(data, textStatus) {
			// console.log("textStatus: "+textStatus);
			// console.log("data: "+data);
			// console.log("data's lenth: " + $.Object.count.call(data));
			if ("[]"!==data) {
				window._detail = $.parseJSON(data)[0];
				fill_table();
			} else {
				console.log("返回为空");
				$("body").empty().html("<h2>返回为空</h2>");
			}
		},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
			console.log('error');
			console.log("textStatus: "+textStatus);
			console.log("errorThrown: "+errorThrown);
			console.log("XMLHttpRequest: "+XMLHttpRequest);
			console.log("XMLHttpRequest.status: "+XMLHttpRequest.status);
			console.log("XMLHttpRequest.statusText: "+XMLHttpRequest.statusText);
			console.log("XMLHttpRequest.responseText: "+XMLHttpRequest.responseText);
			// console.log("XMLHttpRequest.responseXML: "+XMLHttpRequest.responseXML);
		}
	})
}
// 获取详情及所有相关内容
function get_detail_all() {
	$.ajax({
		url: window._request_url,
		type: "POST",
		data: {"operate": "get_detail_all", "id": window._id},
		dataType: "html",
		success: function(data, textStatus) {
			// console.log("textStatus: "+textStatus);
			// console.log("data: "+data);
			// console.log("data's lenth: " + $.Object.count.call(data));
			if ("[]"!==data) {
				window._detail_all = $.parseJSON(data);
				fill_table_all();
			} else {
				console.log("返回为空");
				$("body").empty().html("<h2>返回为空</h2>");
			}
		},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
			console.log('error');
			console.log("textStatus: "+textStatus);
			console.log("errorThrown: "+errorThrown);
			console.log("XMLHttpRequest: "+XMLHttpRequest);
			console.log("XMLHttpRequest.status: "+XMLHttpRequest.status);
			console.log("XMLHttpRequest.statusText: "+XMLHttpRequest.statusText);
			console.log("XMLHttpRequest.responseText: "+XMLHttpRequest.responseText);
			// console.log("XMLHttpRequest.responseXML: "+XMLHttpRequest.responseXML);
		}
	})
}

// 更新或插入详情
function update_detail() {
	// 获取含有update内容的元素组
	var elements = $("table#tb1 textarea.input_area[type='detail']")
	var update_object = new Object;
	elements.each(function(i){
		var name = $(this).attr("name");
		var value = $(this).val();
		update_object[name] = value;
	})
	
	if ($.isEmptyObject(update_object)) {
		return;
	}
	// 生成json格式数据
	var update_data = JSON.stringify(update_object);
	
	console.log("update_data: " + update_data);
	
	$.ajax({
		url: window._request_url,
		type: "POST",
		data: {"operate": "update_detail", "id": window._id, "update_data": update_data},
		dataType: "html",
		success: function(data, textStatus) {
			// console.log("textStatus: "+textStatus);
			// console.log("data: "+data);
			// console.log("data's lenth: " + $.Object.count.call(data));
			var obj = $.parseJSON(data);
			if (0==window._id) {
				if (true===obj[0]) {
					show_info("[添加成功] ID为"+obj[1], "green", 3000);
					window._id = obj[1];
					refresh_original_data(elements);
					create_operate_div();
					update_detail_custom();
				} else {
					show_info("[添加失败] "+obj[1], "red", 5000);
				}
			} else {
				if (true===obj[0]) {
					show_info("[更新成功]", "green", 3000);
					refresh_original_data(elements);
					update_detail_custom();
				} else {
					show_info("[更新失败] "+obj[1], "red", 5000);
				}
			}
		},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
			console.log('error');
			console.log("textStatus: "+textStatus);
			console.log("errorThrown: "+errorThrown);
			console.log("XMLHttpRequest: "+XMLHttpRequest);
			console.log("XMLHttpRequest.status: "+XMLHttpRequest.status);
			console.log("XMLHttpRequest.statusText: "+XMLHttpRequest.statusText);
			console.log("XMLHttpRequest.responseText: "+XMLHttpRequest.responseText);
			// console.log("XMLHttpRequest.responseXML: "+XMLHttpRequest.responseXML);
			show_info("[请求失败: ]"+errorThrown, "red", 5000);
		}
	})
}

// 刷新用于还原的原始数据
function refresh_original_data(elements) {
	elements.each(function(i){
		var name = $(this).attr("name");
		var value = $(this).val();
		window._detail[name] = value;
	})
	refresh_original_data_custom(elements);
}

// 还原数据
function reset_data(key) {
	var tr = $("tr#" + key);
	var textarea = tr.find("textarea");
	textarea.val(window._detail[key]);
	reset_data_custom(key);
}

// 根据页面情况生成操作按钮
function create_operate_div() {
	var div = $("<div name='operate_div' style='width:100px; margin:0 auto; text-align: center'></div>");
	var table = $("<table></table>");
	var colgroup = $("<colgroup></colgroup>");
	colgroup.append($("<col style='width:50px;'>"));
	colgroup.append($("<col style='width:50px;'>"));
	table.append(colgroup);
	var tr = $("<tr></tr>");
	
	var td = $('<td style="text-align: center"></td>');
	var button = $("<button></button>");
	if ('null'!=window._id && ''!=window._id && '0'!=window._id) {
		button.text("修改");
		button.attr("onclick", "update_detail();");
	} else {
		button.text("新增");
		button.attr("onclick", "update_detail();");
	}
	td.append(button);
	tr.append(td);
	
	var td = $('<td style="text-align: center"></td>');
	var button = $("<button>返回</button>");
	if ("true"===window._is_new_window) {
		button.attr("onclick", "window.close();");
	} else {
		button.attr("onclick", "javascript:window.location.href=window._referer;");
	}
	td.append(button);
	tr.append(td);
	
	table.append(tr);
	div.append(table);
	var elements = $("div[name=operate_div]");
	elements.each(function(i){
		$(this).replaceWith(div.clone());
	})
}