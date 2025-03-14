// 注册m2m导入按钮
function bind_m2m_multiple_import_button() {
    $('#m2m_multiple_import_button').off('click').click(function () {
        m2m_multiple_import_obj();
    });
}

// m2m导入对象
function m2m_multiple_import_obj(name_prefix, project, text, no_project) {
	const url = window.m2m_multiple_import_url;
    const title = '<i class="icon-exclamation-sign">&nbsp;</i>' + '导入selenium IDE用例';
    const now = new Date().Format("yyyy-MM-dd HH:mm:ss");
    const case_name = $('#id_name').val();
    let body = $('<div>').addClass('modal-body');
    let div = $('<div>请输入导入后对象的名称前缀</div>');
    body.append(div);
    let input = $('<input class="form-control" autocomplete="off" type="text" id="copy_obj_name">');
    if (name_prefix){
        input.attr('value', name_prefix);
    } else {
        input.attr('value', '【' + now + ' 导入】' + case_name);
    }
    body.append(input);

    div = $('<div>请选择导入后对象所属的项目</div>');
    body.append(div);
    const select = $('#id_project');
    const new_select = select.clone();
    new_select.attr('id', 'new_' + new_select.attr('id'));
    if (typeof(project)==='undefined') {
        new_select.val(select.val());
    } else {
        new_select.val(project);
    }
    body.append(new_select);
    if (no_project) {
        new_select.addClass('is-invalid');
        new_select.after($('<div class="invalid-feedback">这个字段是必填项。</div>'))
    }

    body.append($('<br>'));
    div = $('<div>请使用文本编辑器打开.side文件，复制全部内容后粘贴到下面的文本框。导入的步骤将被添加到当前选中的最后一个步骤下面</div>');
    body.append(div);
    const textarea = $('<textarea class="form-control" rows="10" wrap="off" id="aa111">');
    if (text) { textarea.text(text) }
    body.append(textarea);

    const buttons = {
		import: {
			label: '<span title="导入步骤"><i class="icon-primary">&nbsp;</i>导入</span>',
			className: 'btn btn-primary',
			callback: function () {
			    if (new_select.val()) {
			        callback_m2m_multiple_import_obj(url, input.val(), new_select.val(), textarea.val())
                } else {
			        m2m_multiple_import_obj(input.val(), new_select.val(), textarea.val(), 1)
                }

			}
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