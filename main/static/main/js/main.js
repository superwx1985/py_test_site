$.extend({
    //  获取对象的长度，需要指定上下文 this
    Object: {
        count: function (p) {
            p = p || false;

            return $.map(this, function (o) {
                if (!p) return o;

                return true;
            }).length;
        }
    }
});


// 生成随机字符串
function S4() {
    return (((1+ Math.random())*0x10000)|0).toString(16).substring(1);
}

// 生成GUID
function guid() {
    return (S4() + S4() + "-" + S4() + "-" + S4() + "-" + S4() + S4() + S4())
}


// 设置cookie
function set_cookie(name, value, seconds, path) {
    var exp_str = '';
    var path_str = '';
    var exp = new Date();
	if (seconds && seconds > 0) {exp_str = exp.setTime(exp.getTime() + seconds*1000).toUTCString();}
	if (path) {path_str = path}
	document.cookie = name + "=" + encodeURI(value) + ";expires=" + exp_str + ";path=" + path_str;
}

// 获取cookie
function get_cookie(name) {
	var arr,reg = new RegExp("(^|)" + name + "=([^;]*)(;|$)");
	if (arr=document.cookie.match(reg)) {
		return decodeURI(arr[2]);
	} else {
		return null;
	}
}

// 输出返回消息（废弃，使用toastr代替）
/*
function show_info(msg, class_list, time) {
	// 首先停止上次的setTimeout任务
	if ("undefined"!==typeof(_show_info_timeout_id)) {
		clearTimeout(_show_info_timeout_id);
	}
	var show_info = $(".show_info");
	show_info.empty()
	var show_info_wrap = $('<div></div>');
	var show_info_inner = $('<div></div>');
	show_info_wrap.append(show_info_inner);
	show_info.append(show_info_wrap);
	show_info_inner.text(msg);
	show_info_inner.addClass(class_list);
	show_info.show();
	window._show_info_timeout_id = setTimeout(function(){show_info.fadeOut(500)}, time);// 停留{time}毫秒之后淡出
}*/

// 获取结果集
function getList(url, csrf_token, callback_func, condition_json) {
	$.ajax({
        url: url,
        type: "POST",
        data: {
            csrfmiddlewaretoken: csrf_token,
            condition: condition_json
        },
        dataType: "json",
        success: function (data, textStatus) {
            // console.log('success');
            // console.log("data['new_value']: " + data['new_value']);
            // console.log("textStatus: " + textStatus);
            callback_func(true, data)
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            // console.log('error');
            // console.log("XMLHttpRequest: " + XMLHttpRequest);
            // console.log("XMLHttpRequest.status: " + XMLHttpRequest.status);
            // console.log("XMLHttpRequest.statusText: " + XMLHttpRequest.statusText);
            // console.log("XMLHttpRequest.responseText: " + XMLHttpRequest.responseText);
            // console.log("XMLHttpRequest.responseXML: "+XMLHttpRequest.responseXML);
            // console.log("textStatus: " + textStatus);
            // console.log("errorThrown: " + errorThrown);
            callback_func(false, XMLHttpRequest.responseText)
        }
    })
}

// 获取元素整体高度, 包含margin
function get_element_full_height($e) {
    var height = parseInt($e.css('margin-top')) + parseInt($e.css('margin-bottom')) + $e.outerHeight();
    return isNaN(height) ? 0 : height
}

// 获取元素外部margin, border, padding高度
function get_element_outside_height($e) {
    var height = get_element_full_height($e) - $e.height();
    return isNaN(height) ? 0 : height
}

// 复制对象弹框
function copy_obj(copy_url) {
    var now = new Date().Format("yyyy-MM-dd HH:mm:ss");
    var body = $('<div>').addClass('modal-body');
    var div = $('<div>准备复制对象。请输入复制后的名称前缀：</div>');
    body.append(div);
    body.append($('<br>'));
    var input = $('<input class="form-control" autocomplete="off" type="text" id="copy_obj_name">').attr('value', '【' + now + ' 复制】');
    body.append(input);
    if (window.has_sub_object) {
        var buttons = {
            cancel: {
                label: '<i class="icon-undo">&nbsp;</i>取消',
                className: 'btn btn-secondary'
            },
            copy: {
                label: '<i class="icon-copy">&nbsp;</i>复制',
                className: 'btn btn-warning',
                callback: function () { callback_copy_obj(copy_url, $('#copy_obj_name').val()) }
            },
            copy_sub_item: {
                label: '<i class="icon-copy">&nbsp;</i>同时复制子对象',
                className: 'btn btn-warning-dark',
                callback: function () { callback_copy_obj_sub_item(copy_url, $('#copy_obj_name').val()) }
            }
        }
    } else {
        var buttons = {
            cancel: {
                label: '<i class="icon-undo">&nbsp;</i>取消',
                className: 'btn btn-secondary'
            },
            copy: {
                label: '<i class="icon-copy">&nbsp;</i>复制',
                className: 'btn btn-warning',
                callback: function () { callback_copy_obj(copy_url, $('#copy_obj_name').val()) }
            }
        }
    }

    bootbox.dialog({
        size: 'large',
        title: '<i class="icon-exclamation-sign">&nbsp;</i>请确认',
        message: body.html(),
        onEscape: true,
		backdrop: true,
        buttons: buttons
    });
}

// 弹出框
function show_my_modal(modal_name, modal_class, modal_style, modal_body_style, modal_title, $modal_body_div, modal_option, callback) {
    var html_ =
        '<div class="modal fade" name="'+ modal_name +'">\n' +
        '    <div class="modal-dialog '+ modal_class +'" style="' + modal_style + '">\n' +
        '        <div class="modal-content">\n' +
        '            <div class="modal-header">\n' +
        '                <span class="modal-title lead">' + modal_title + '</span>\n' +
        '                <button type="button" class="close" data-dismiss="modal">&times;</button>\n' +
        '            </div>\n' +
        '            <div class="modal-body" style="' + modal_body_style + '"></div>\n' +
        '        </div>\n' +
        '    </div>\n' +
        '</div>';
	var my_modal = $(html_);
	$('body').append(my_modal);
	// 如果未提供title，不显示header
	if (!modal_title) { my_modal.find('.modal-header').remove() }
	var my_modal_body = my_modal.find('.modal-body');
    my_modal_body.empty().append($modal_body_div);
    // 如果body未指定高度，则使用当前页面高度来确定
    if (!parseInt(my_modal_body.css('height'))){
        // 必须要先显示出来才能得到正确的高度
        my_modal.off('shown.bs.modal').on('shown.bs.modal', function () {
            var body_height = $(window).height()
                - get_element_outside_height(my_modal.find('.modal-dialog'))
                - get_element_outside_height(my_modal.find('.modal-content'))
                - get_element_full_height(my_modal.find('.modal-header'))
                - get_element_outside_height(my_modal_body);
            my_modal_body.css('height', body_height);
        });
    }
    // 关闭modal后执行回调函数并清除modal代码
	my_modal.off('hide.bs.modal').on('hide.bs.modal', function () {
	    if (callback) { callback() }
	    my_modal.remove();
	});
    if (modal_option) { my_modal.modal(modal_option) } else { my_modal.modal() }
    return my_modal;
}

// 弹出内嵌页面
function modal_with_iframe(modal_name, modal_class, modal_style, modal_body_style, modal_title, url, modal_option, callback) {
    var $modal_body_div = $('<div style="height: 100%;"></div>');
    var iframe = $('<iframe>').attr('name', modal_name + '_iframe').attr('frameborder', 0).css({'height': '100%', 'width': '100%'});
    if (url) {
        iframe.attr('src', url);
    }
    $modal_body_div.append(iframe);
    return show_my_modal(modal_name, modal_class, modal_style, modal_body_style, modal_title, $modal_body_div, modal_option, callback)
}

// 弹出内嵌页面最大化
function modal_with_iframe_max(modal_name, modal_title, url, modal_option, callback) {
    return modal_with_iframe(modal_name, 'modal-max', '', 'min-height: 600px', modal_title, url, modal_option, callback)
}

// 查看被调用弹窗
function show_reference(url, title) {
    if (!title) {
        title = '被调用情况';
    }
	bootbox.dialog({
		title: title,
		message: '<div id="reference_div" class="middle"><i class="icon-spinner icon-spin icon-5x"></i></div>',
		size: 'large',
		onEscape: true,
		backdrop: true,
		init: $.get(url, function (data) {
			$('#reference_div').parent('.bootbox-body').empty().html(data);
		}, 'html')
	})
}

// 搜索时是否回到第一页
function go_to_first_page(not_go_to_first_page, f, $e) {
    if (!not_go_to_first_page) {
        f($e)
    }
}

// 修改页码为1
function set_page_to_one($e) {
    $e.val(1)
}

// 获取格式化时间
Date.prototype.Format = function (fmt) {
    var o = {
        'M+': this.getMonth() + 1,
        'd+': this.getDate(),
        'H+': this.getHours(),
        'm+': this.getMinutes(),
        's+': this.getSeconds(),
        'S': this.getMilliseconds(),
        'q+': Math.floor((this.getMonth()+3)/3)
    };
    if (/(y+)/.test(fmt)) fmt = fmt.replace(RegExp.$1, (this.getFullYear() + '').substr(4 - RegExp.$1.length));
    for (var k in o)
        if (new RegExp('(' + k + ')').test(fmt)) fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]): (('00' + o[k]).substr(('' + o[k]).length)));
    return fmt;
};

// 更新下拉项
function update_dropdown(data, $base_div, readonly) {
	$base_div.empty();
	var name = $base_div.attr('name');
	var div_dropdown = $('<div j_dropdown style="width: 100%"><select style="display: none;" placeholder="请选择" name="' + name + '"></select></div>');
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