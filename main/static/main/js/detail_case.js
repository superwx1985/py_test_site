// 注册m2m导入按钮
function bind_m2m_multiple_import_button() {
    $('#m2m_multiple_import_button').off('click').click(function () {
        m2m_multiple_import_obj();
    });
}

// m2m导入对象
function m2m_multiple_import_obj() {
	var url = window.m2m_multiple_import_url;

    var title = '<i class="icon-exclamation-sign">&nbsp;</i>' + '导入seleniumIDE生成的XML格式用例';
    var body = $('<div>').addClass('modal-body');
    var now = new Date().Format("yyyy-MM-dd HH:mm:ss");
    var case_name = $('#id_name').val();
    var div = $('<div>请输入导入后对象的名称前缀</div>');
    body.append(div);
    var input = $('<input class="form-control" autocomplete="off" type="text" id="copy_obj_name">').attr('value', '【' + now + ' 导入】' + case_name);
    body.append(input);

    div = $('<div>请选择导入后对象所属的项目</div>');
    body.append(div);
    var select = $('#id_project');
    var new_select = select.clone();
    new_select.val(select.val());
	body.append(new_select);

    body.append($('<br>'));
    div = $('<div>请粘贴seleniumIDE生成的XML格式用例，对象将被添加到当前选中的最后一行下面</div>');
    body.append(div);
    var textarea = $('<textarea class="form-control" rows="10" wrap="off">');
    body.append(textarea);

    var buttons = {
		import: {
			label: '<span title="导入步骤"><i class="icon-primary">&nbsp;</i>导入</span>',
			className: 'btn btn-primary',
			callback: function () { callback_m2m_multiple_import_obj(url, $('#copy_obj_name').val(), new_select.val(), textarea.val()) }
		}
	};

    bootbox.dialog({
		size: 'large',
		title: title,
		message: body,
		onEscape: true,
		backdrop: true,
		buttons: buttons
	});
}

// 复制m2m对象及子对象的的回调函数
function callback_m2m_multiple_import_obj(url, name_prefix, project, data_text) {
	bootbox.dialog({
		size: 'large',
		title: '<i class="icon-exclamation-sign">&nbsp;</i>请再次确认',
		message: '导入操作将自动生成若干步骤，可能耗费较长时间。请确认您了解此操作的含义。',
		buttons: {
			cancel: {
				label: '<i class="icon-undo">&nbsp;</i>取消',
				className: 'btn btn-secondary'
			},
			confirm: {
				label: '<i class="icon-ok">&nbsp;</i>确认',
				className: 'btn btn-primary',
				callback: function() { m2m_multiple_import_obj_post(url, name_prefix, project, data_text) }
			}
		}
	})
}

function m2m_multiple_import_obj_post(url, name_prefix, project, data_text) {
    $('#mask').show();
    $.post(url, {'csrfmiddlewaretoken': $csrf_input.val(), 'name_prefix': name_prefix, 'project': project, 'data_text': data_text}, function(data) {
        $('#mask').hide();
        if (data.state === 1) {
        	var new_pk_list = data.data;
        	var new_obj_list = [];
			$.each(new_pk_list, function (i, v) {
				var obj = {"pk": v.toString()};
				new_obj_list.push(obj);
			});
			new_obj_list = JSON.stringify(new_obj_list);
            m2m_multiple_paste_obj_link_to_list(new_obj_list);
        } else {
            bootbox.alert('<span class="text-danger">'+data.message+'</span>');
        }
    });
}