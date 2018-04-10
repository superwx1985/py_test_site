/*注册事件*/
function reg_event() {
	$("button[name=first_page_button]").click(function () {
		first_page();
	})
	$("button[name=last_page_button]").click(function () {
		last_page();
	})
	$("button[name=prev_page_button]").click(function () {
		prev_page();
	})
	$("button[name=next_page_button]").click(function () {
		next_page();
	})
	input_number($("input[name=page_number_input]"), change_page);
	input_number($("input[name=page_size_input]"), change_page_size);
	$("#search_button").click(function () {
		search();
	})
	$("#search_button_clear").click(function () {
		search_clear();
	})
	$("#search_input").keydown(function (e) {
		// console.log(e.keyCode);
		if(e.keyCode === 13) {
			search();
		}
	})
	$("#insert_button").click(function () {
		window.open('detail.jsp?new_window=true');
	})
	recycle_bin_checkbox_change();
}

// 创建翻页导航按钮
function create_page_navigation_div() {
	var div = $("<div name='operate_div' style='width:500px; margin:0 auto; text-align: center'></div>");
	var table = $("<table></table>");
	var colgroup = $("<colgroup></colgroup>");
	colgroup.append($("<col style='width:50px;'>"));
	colgroup.append($("<col style='width:50px;'>"));
	colgroup.append($("<col style='width:150px;'>"));
	colgroup.append($("<col style='width:50px;'>"));
	colgroup.append($("<col style='width:50px;'>"));
	colgroup.append($("<col style='width:200px;'>"));
	table.append(colgroup);
	var tr = $("<tr></tr>");
	
	var td = $('<td style="text-align: center"></td>');
	var button = $("<button></button>");
	button.text("首页");
	button.attr("name", "first_page_button");
	td.append(button);
	tr.append(td)
	
	var td = $('<td style="text-align: center"></td>');
	var button = $("<button></button>");
	button.text("上页");
	button.attr("name", "prev_page_button");
	td.append(button);
	tr.append(td)
	
	var td = $('<td style="text-align: center"></td>');
	var input = $("<input></input>");
	input.attr("name", "page_number_input");
	input.addClass("td_inner_input");
	input.css({"height": "25px", "width": "50px", "border": "1px solid #999999"});
	td.append(input);
	td.append(" / ");
	var span = $("<span></span>");
	span.attr("name", "max_page_number");
	td.append(span);
	tr.append(td)
	
	var td = $('<td style="text-align: center"></td>');
	var button = $("<button></button>");
	button.text("下页");
	button.attr("name", "next_page_button");
	td.append(button);
	tr.append(td)
	
	var td = $('<td style="text-align: center"></td>');
	var button = $("<button></button>");
	button.text("末页");
	button.attr("name", "last_page_button");
	td.append(button);
	tr.append(td);
	
	var td = $('<td style="text-align: center"></td>');
	td.append("每页 ");
	var input = $("<input></input>");
	input.attr("name", "page_size_input");
	input.addClass("td_inner_input");
	input.css({"height": "25px", "width": "50px", "border": "1px solid #999999"});
	td.append(input);
	td.append(" 共 ");
	var span = $("<span></span>");
	span.attr("name", "result_count");
	td.append(span);
	tr.append(td)
	
	table.append(tr);
	div.append(table);
	var elements = $("div[name=page_navigation_div]");
	elements.each(function(i){
		$(this).replaceWith(div.clone());
	})
}

// 重置查询条件
function search_clear() {
	$("#search_input").val("");
	window._condition = get_condition();
	var page_size = parseInt(get_cookie("page_size"));
	goto_page(1, page_size, window._condition);
	get_count(window._condition);
}

// 触发查询
function search() {
	window._condition = get_condition();
	var page_size = parseInt(get_cookie("page_size"));
	goto_page(1, page_size, window._condition);
	get_count(window._condition);
}

// 手动翻页
function change_page(newText) {
	var goto_page_id = parseInt(newText);
	var result_count = parseInt(get_cookie("result_count"));
	var page_size = parseInt(get_cookie("page_size"));
	var last_page_id = Math.ceil(result_count/page_size);
	
	if (goto_page_id>0 && goto_page_id<=last_page_id) {
		goto_page(goto_page_id, page_size, window._condition);
		return true;
	} else {
		alert("超出可选范围");
		return false;
	}
}

// 修改每页显示条数
function change_page_size(newText) {
	var page_size = parseInt(newText);
	if (0>=page_size) {
		alert("超出可选范围");
		return false;
	} else {
		set_cookie("page_size", page_size);
		$("input[name=page_size_input]").val(page_size);
		goto_page(1, page_size, window._condition);
		var result_count = parseInt(get_cookie("result_count"));
		refresh_result_count_and_max_page(result_count);
		return true;
	}
}

// 处理数字输入框
function input_number(inputObjs, func) {
	inputObjs.unbind('focus').focus(function () {
		var inputObj = $(this);
		// 保存原来的文本
		var oldText = inputObj.val();
		// 全选
		inputObj.trigger("select");
		// 按下键盘时
		inputObj.unbind('keydown').keydown(function () {
			var key_code = event.keyCode;
			
			switch (key_code) {
				// 按下回车，跳转
				case 13:
					var newText = inputObj.val();// 修改后的值
					if (oldText != newText) {
						// 调用子函数
						if (!func(newText)) {
							console.log("函数调用失败",func);
							inputObj.val(oldText);
						} else {
							oldText = newText;
						}
					}
					inputObj.blur();
					break;
				// 按下esc，还原
				case 27:
					inputObj.val(oldText);
					inputObj.blur();
					break;
				default:
					// console.log("key_code="+key_code)
					// 限制只能输入退格，大键盘数字，小键盘数字
					if (key_code==8 || (key_code>=48 && key_code<=57) || (key_code>=96 && key_code<=105)) {
						return true;
					} else {
						return false;
					}
			}
		})
		
		// 文本框失去焦点的时
		inputObjs.unbind('blur').blur(function () {
			var inputObj = $(this);
			inputObj.val(oldText);
			inputObj
			return;
		})
	})
}

// 前一页
function prev_page() {
	var goto_page_id = parseInt(get_cookie("page_id")) - 1
	if (goto_page_id < 1) {
		return;
	}
	var page_size = parseInt(get_cookie("page_size"));
	goto_page(goto_page_id, page_size, window._condition)
}

// 下一页
function next_page() {
	var result_count = parseInt(get_cookie("result_count"));
	var page_size = parseInt(get_cookie("page_size"));
	var last_page_id = Math.ceil(result_count/page_size);
	var goto_page_id = parseInt(get_cookie("page_id")) + 1
	if (last_page_id<goto_page_id) {
		return;
	}
	goto_page(goto_page_id, page_size, window._condition)
}

// 第一页
function first_page() {
	var current_page = parseInt(get_cookie("page_id"));
	if (1==current_page) {
		return;
	}
	var page_size = parseInt(get_cookie("page_size"));
	goto_page(1, page_size, window._condition)
}

// 最后一页
function last_page() {
	var current_page = parseInt(get_cookie("page_id"));
	var result_count = parseInt(get_cookie("result_count"));
	var page_size = parseInt(get_cookie("page_size"));
	var last_page_id = Math.ceil(result_count/page_size);
	if (last_page_id==current_page) {
		return;
	}
	goto_page(last_page_id, page_size, window._condition)
}

// 回收站复选框操作
function recycle_bin_checkbox_change() {
	$("#recycle_bin_checkbox").off("change").on("change", function () {
		console.log($(this).prop("checked"));
		search();
	});
}

// 更新当前页码
function refresh_current_page(page_number_input, goto_page_id) {
	page_number_input.val(goto_page_id);
}

// 更新总页数
function refresh_result_count_and_max_page(result_count) {
	set_cookie("result_count", result_count);
	$("span[name=result_count]").text(result_count);
	var page_size = parseInt(get_cookie("page_size"));
	var last_page_id = Math.ceil(result_count/page_size);
	$("span[name=max_page_number]").text(last_page_id);
}

// 生成查询条件
function get_condition() {
	var condition = new Object;
	condition[$("#search_select").val()] = $("#search_input").val();
	if ($("#recycle_bin_checkbox").prop("checked")) {
		condition["is_deleted"] = "1";
	} else {
		condition["is_deleted"] = "0";
	}
	condition = get_condition_custom(condition);
	return condition
}

// 获取新页内容
function goto_page(goto_page_id, page_size, condition) {
	
	var condition_json = JSON.stringify(condition);
	
	console.log("condition_json: " + condition_json);
	$.ajax({
		url: window._request_url,
		type: "POST",
		data: {"operate": "get_list", "goto_page_id": goto_page_id, "page_size": page_size, "condition": condition_json},
		dataType: "html",
		success: function(data, textStatus) {
			// console.log("textStatus: "+textStatus);
			// console.log("data: "+data);
			// console.log("data's lenth: " + $.Object.count.call(data));
			if ("[]"!==data) {
				set_cookie("page_id", goto_page_id);
				set_cookie("page_size", page_size);
				refresh_current_page($("input[name=page_number_input]"), goto_page_id);// 更新当前页码
				window._list_result = $.parseJSON(data)[0];
				fill_table();// 更新列表
			} else {
				console.log("返回为空");
			}
			show_info("[列表已刷新]", "green", 1000);
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

// 获取结果总数
function get_count(condition) {
	
	var condition_json = JSON.stringify(condition);
	
	$.ajax({
		url: window._request_url,
		type: "POST",
		data: {"operate": "result_count", "condition": condition_json},
		dataType: "html",
		success: function(data, textStatus) {
			// console.log("textStatus: "+textStatus);
			// console.log("data: "+data);
			// console.log("data's lenth: " + $.Object.count.call(data));
			refresh_result_count_and_max_page(data);
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

// 删除
function delete_(id) {
	$.ajax({
		url: window._request_url,
		type: "POST",
		data: {"operate": "delete", "id": id},
		dataType: "html",
		success: function(data, textStatus) {
			// console.log("textStatus: "+textStatus);
			// console.log("data: "+data);
			// console.log("data's lenth: " + $.Object.count.call(data));
			tb = $('#tb1');
			tr = tb.find("tr[row_id=" + id + "]");
			tr.remove();
			show_info("[删除成功]", "green", 1000);
			
			var result_count = parseInt(get_cookie("result_count"));
			result_count = result_count - parseInt(data);
			refresh_result_count_and_max_page(result_count);
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

function restore(id) {
	$.ajax({
		url: window._request_url,
		type: "POST",
		data: {"operate": "restore", "id": id},
		dataType: "html",
		success: function(data, textStatus) {
			// console.log("textStatus: "+textStatus);
			// console.log("data: "+data);
			// console.log("data's lenth: " + $.Object.count.call(data));
			tb = $('#tb1');
			tr = tb.find("tr[row_id=" + id + "]");
			tr.remove();
			show_info("[还原成功]", "green", 1000);
			
			var result_count = parseInt(get_cookie("result_count"));
			result_count = result_count - parseInt(data);
			refresh_result_count_and_max_page(result_count);
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

function clear_(id) {
	$.ajax({
		url: window._request_url,
		type: "POST",
		data: {"operate": "clear", "id": id},
		dataType: "html",
		success: function(data, textStatus) {
			// console.log("textStatus: "+textStatus);
			// console.log("data: "+data);
			// console.log("data's lenth: " + $.Object.count.call(data));
			tb = $('#tb1');
			tr = tb.find("tr[row_id=" + id + "]");
			tr.remove();
			show_info("[清除成功]", "green", 1000);
			
			var result_count = parseInt(get_cookie("result_count"));
			result_count = result_count - parseInt(data);
			refresh_result_count_and_max_page(result_count);
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