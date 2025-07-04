function help_items_popup($e) {
	$e.off('click').on('click', function() {
		let url = $(this).attr('url') + "?inside=1";
		let name = $(this).text();
		modal_with_iframe_max('inside_detail_modal', name, url);
	});
}

// 一些公用说明
function show_expression_introduce($introduce) {
	$introduce.append($('<div>计算表达式时，首先会替换表达式中<span class="mark">${}$</span>标识的变量，然后替换<span class="mark">$[]$</span>标识的变量，最后把替换的结果尝试作为python代码执行。由于安全原因，大部分python关键字将会被屏蔽，只支持数学运算符，逻辑运算符和类型转换符。</div>'));
	$introduce.append($('<div>如果想在表达式中使用字符串，请添加<span class="text-danger">英文双引号</span>。例：<span class="mark">"123"</span>不会转换为整型<span class="text-info">123</span>，而是被保存为字符串<span class="text-info">123</span>。</div>'));
	$introduce.append($('<div>如果想在表达式中调用变量，请使用<span class="mark">$[变量名]$</span>格式。例：假设已有变量x=3（字符串），那么<span class="mark">int($[x]$)+1</span>结果为<span class="text-info">4</span>；<span class="mark">$[x]$==3</span>结果为布尔变量<span class="text-info">False</span>。</div>'));
	$introduce.append($('<div>如果想在表达式中使用特殊变量，请使用<span class="mark">${特殊变量表达式}$</span>格式。注意：特殊变量返回值会被认为是表达式的一部分，所以应该添加双引号把它转为文本再进行保存，否则会被认为是无效的表达式。例如想把当前时间保存为变量，<span class="text-success">正确示例：</span><span class="mark">"${t|now}$"</span>结果为字符串<span class="text-info">2025-02-05 12:55:58</span>；<span class="mark">"现在时间: "+"${t|now}$"</span>结果为字符串<span class="text-info">现在时间: 2025-02-05 12:55:58</span>。<span class="text-danger">错误示例：</span><span class="mark">${t|now}$</span>。</div>'));
	$introduce.append($('<div>复杂用法的示例。验证字符串的最后一位是数字4：<span class="mark">${int|${slice|abcd1234,-1}$}$==4</span>结果为布尔变量<span class="text-info">True</span>。请使用<a name="help_items" url=' + window.variable_test_url + ' href="javascript:">变量表达式测试</a>页面自行测试。</div>'));
	help_items_popup($('[name=help_items]'));
}

// 展示Action相关内容
function show_action_field($actionSelect, init) {
    reset_action_field(init);
	window.select_value = window.action_map[$actionSelect.val()];
	let introduce = $('#introduce');
	if (select_value === 'UI_ALERT_HANDLE') {
		introduce.children('div').text('处理浏览器弹窗（非页面元素弹窗），如：alert，confirm，prompt');
		$('div[name=ui_alert_handle],div[name=ui_alert_handle_text],div[name=timeout],div[name=ui_step_interval]').show();
	} else if (select_value === 'UI_GO_TO_URL') {
		introduce.children('div').text('打开一个页面，请填入页面URL');
		$('div[name=ui_data] .col-1').text('URL');
		$('div[name=ui_data],div[name=timeout],div[name=ui_step_interval]').show();
	} else if (select_value === 'UI_REFRESH') {
		introduce.children('div').text('触发浏览器刷新页面操作');
		$('div[name=timeout],div[name=ui_step_interval]').show();
	} else if (select_value === 'UI_FORWARD') {
		introduce.children('div').text('触发浏览器前进操作');
		$('div[name=timeout],div[name=ui_step_interval]').show();
	} else if (select_value === 'UI_BACK') {
		introduce.children('div').text('触发浏览器后退操作');
		$('div[name=timeout],div[name=ui_step_interval]').show();
	} else if (select_value === 'UI_SCREENSHOT') {
		introduce.children('div').text('获取当前页面截图，如果提供了定位信息则只截取定位到的元素');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_data],div[name=ui_special_action]').hide();
	} else if (select_value === 'UI_SWITCH_TO_FRAME') {
		introduce.children('div').text('进入页面内嵌框架（frame或iframe）。如果提供了定位信息，则切换至定位到的元素绑定的框架，否则切换至索引值（当前页面的第一个框架索引为0，第二个框架索引为1，以此类推）对应的框架');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_data],div[name=ui_special_action]').hide();
	} else if (select_value === 'UI_SWITCH_TO_DEFAULT_CONTENT') {
		introduce.children('div').text('回到框架的上一级页面，如进入了多层框架，请使用多次该动作');
		$('div[name=timeout],div[name=ui_step_interval]').show();
	} else if (select_value === 'UI_SWITCH_TO_WINDOW') {
		introduce.children('div').text('切换至浏览器的其他窗口或标签。如果提供了窗口标题，则切换到标题（head中title元素的值）中包含该文字的窗口；如果提供了定位信息，则切换到包含该元素的窗口；否则切换至任意一个非当前窗口');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('窗口标题');
	} else if (select_value === 'UI_CLOSE_WINDOW') {
		introduce.children('div').text('关闭当前浏览器窗口或标签并切换至其他窗口或标签。如果提供了窗口标题，则切换到标题（head中title元素的值）中包含该文字的窗口；如果提供了定位信息，则切换到包含该元素的窗口；否则切换至任意一个非当前窗口');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('窗口标题');
	} else if (select_value === 'UI_RESET_BROWSER') {
		introduce.children('div').text('关闭浏览器，清空所有缓存，再重新打开浏览器');
		$('div[name=timeout],div[name=ui_step_interval]').show();
	} else if (select_value === 'UI_CLICK') {
		introduce.children('div').text('在指定的元素上触发单击，如果找不到元素或元素当前不可见会报错。如果填写了“保存为”，找到的元素将被保存为变量');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_data],div[name=ui_special_action]').hide();
	} else if (select_value === 'UI_ENTER') {
		introduce.children('div').text('在指定的元素里输入文字，如果找不到元素或元素当前不可见会报错。如果填写了“保存为”，找到的元素将被保存为变量');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('文字内容');
	} else if (select_value === 'UI_CLEAR') {
		introduce.children('div').text('清空指定输入框、文本框的值，如果找不到元素或元素当前不可见会报错。如果填写了“保存为”，找到的元素将被保存为变量');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_data],div[name=ui_special_action]').hide();
	} else if (select_value === 'UI_SELECT') {
		introduce.children('div').text('在指定的下拉列表进行选择操作，如果找不到元素或元素当前不可见会报错。此动作只能操作由select，option元素组成的标准下拉列表，其他类型的下拉列表请使用单击或JS进行选择');
		introduce.append($('<div>').text('不提供选项代表在指定的下拉列表取消所有选择'));
		introduce.append($('<div>').text('全选只能在多选下拉列表生效'));
		introduce.append($('<div>').text('如果填写了“保存为”，找到的元素将被保存为变量'));
		$('[ui],div[name=timeout],div[name=ui_data_select],div[name=save_as]').show();
		$('div[name=ui_special_action],div[name=ui_data]').hide();
		init_step_ui_data_select();
		// 注册添加按钮
		$('#ui_data_select_table #new_helper td[col_move]').off('click').on('click', function () {
			add_step_ui_data_select();
		});
		// 注册new helper的删除按钮事件
		$('#ui_data_select_table #new_helper [col_del]').off('click').on('click', function () {
			$('#ui_data_select_table #new_helper [col_select_by] select').val('value');
			$('#ui_data_select_table #new_helper [col_select_value] input').val('').removeClass('is-invalid').siblings('div.invalid-feedback').remove();
		});
		// 注册全选复选框事件
		$('[name=ui_data_select_all]').off('click').on('click', function () { check_step_ui_data_select_all_checkbox() });
	} else if (select_value === 'UI_SPECIAL_ACTION') {
		introduce.children('div').text('执行一些特殊的互动操作。如果填写了“保存为”，找到的元素将被保存为变量。请选择具体的特殊动作...');
		$('div[name=ui_special_action],div[name=timeout],div[name=save_as],div[name=ui_step_interval]').show();
		show_special_action_field($('#id_ui_special_action'));
	} else if (select_value === 'UI_SCROLL_INTO_VIEW') {
		introduce.children('div').text('移到浏览器窗口的可视区域到指定的元素的位置，如果找不到元素会报错。如果填写了“保存为”，找到的元素将被保存为变量');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_data],div[name=ui_special_action]').hide();
	} else if (select_value === 'UI_VERIFY_URL') {
		introduce.children('div').text('验证当前页面的URL是否匹配，待验证内容可以为字符串或表达式。如果填写了“保存为”，验证结果将被保存为变量');
		$('div[name=ui_data] .col-1').text('待验证内容');
		$('div[name=ui_data],div[name=timeout],div[name=save_as],div[name=ui_step_interval]').show();
	} else if (select_value === 'UI_VERIFY_TEXT') {
		introduce.children('div').text('验证页面是否包含文字（如果待验证内容是输入框内的值，或者是表达式，请指定元素）。如果指定了元素，则验证该元素是否包含文字。如果填写了“保存为”，验证结果将被保存为变量');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('待验证内容');
	} else if (select_value === 'UI_VERIFY_ELEMENT_SHOW') {
		introduce.children('div').text('验证页面是否包含指定元素，且该元素可见。可以通过数量表达式验证找到的元素数量，如果不提供表达式则表示找到任意数量的元素都可以通过验证。如果填写了“保存为”，验证结果将被保存为变量');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').html('数量表达式&nbsp;<i class="icon-question-sign" data-toggle="tooltip" title="在表达式中以$[x]$代表找到的元素数量。例：$[x]$==3 代表找到的元素数量必须等于3，1 < $[x]$ <= 5 代表找到的元素数量必须大于1且小于等于5"></i>');
	} else if (select_value === 'UI_VERIFY_ELEMENT_HIDE') {
		introduce.children('div').text('验证页面是否包含指定元素，且该元素不可见。如果填写了“保存为”，验证结果将被保存为变量');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_special_action],div[name=ui_data]').hide();
	} else if (select_value === 'UI_EXECUTE_JS') {
		introduce.children('div').html('在当前页面执行JavaScript代码。如果指定了元素，可以在代码中通过<span class="mark">arguments[0][0]</span>调用。例：<span class="mark">arguments[0][0].click()</span>');
		introduce.append($('<div>如果填写了“保存为”，那么将把JavaScript代码执行后的返回值保存为用例变量</div>'));
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('js代码');
	} else if (select_value === 'UI_VERIFY_JS_RETURN') {
		introduce.children('div').html('在当前页面执行JavaScript代码并验证结果是否为真。验证通过的条件是js代码执行后返回True，如果指定了元素，可以在代码中通过<span class="mark">arguments[0][0]</span>调用。例：<span class="mark">arguments[0][0].click()</span>');
		introduce.append($('<div>如果填写了“保存为”，验证结果将被保存为变量</div>'));
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('js代码');
	} else if (select_value === 'UI_SAVE_ELEMENT') {
		introduce.children('div').text('把指定的元素组保存为变量。为统一变量类型，即使定位到唯一元素也会以元素组形式保存');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_special_action],div[name=ui_data]').hide();
	} else if (select_value === 'UI_SAVE_URL') {
		introduce.children('div').html('把URL或URL的一部分保存为变量。可以使用正则表达式指定要匹配的部分。例：<span class="mark">#{re}#id=(\\d+)&</span>将匹配<span class="text-info">http://www.test.com/user/?id=12345&pk=45678</span>中的<span class="text-info">12345</span>');
		$('div[name=timeout],div[name=save_as],div[name=ui_data],div[name=ui_step_interval]').show();
		$('div[name=ui_data] .col-1').text('正则表达式');
	} else if (select_value === 'UI_SAVE_ELEMENT_TEXT') {
		introduce.children('div').html('把元素文本保存为变量');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_special_action],div[name=ui_data]').hide();
	} else if (select_value === 'UI_SAVE_ELEMENT_ATTR') {
		introduce.children('div').html('把元素属性的值保存为变量');
		$('div[name=ui_data] .col-1').text('属性名');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_special_action]').hide();
	} else if (select_value === 'OTHER_SLEEP') {
		introduce.children('div').text('等待若干秒');
		$('div[name=other_data] .col-1').html('等待时间&nbsp;<i class="icon-question-sign" data-toggle="tooltip" title="单位：秒"></i>');
		$('div[name=other_data]').show();
	} else if (select_value === 'OTHER_SAVE_CASE_VARIABLE') {
		introduce.children('div').text('把数值，字符串或表达式的值保存为用例级别的局部变量。在子用例中保存的局部变量可以被调用它的上级用例访问。例：依次运行2个用例，A和B；A调用子用例C，C运行时定义了局部变量bar=1，那么A访问bar得到1；若B也调用C，C运行时定义了局部变量bar=2，那么B访问bar得到2，A访问bar还是1');
		show_expression_introduce(introduce)
		$('div[name=save_as],div[name=other_data]').show();
	} else if (select_value === 'OTHER_SAVE_GLOBAL_VARIABLE') {
		introduce.children('div').text('把数值，字符串或表达式的值保存为全局变量。全局变量定义后可以被本次测试的所有用例访问。例：依次运行2个用例，A和B；A调用子用例C，C运行时定义了局部变量bar=1，那么A访问bar得到1；若B也调用C，C运行时定义了局部变量bar=2，那么B访问bar得到2，A访问bar得到2');
		show_expression_introduce(introduce)
		introduce.append($('<div><span class="text-danger">如果运行时选择了多线程模式，由于执行顺序不可预期，要考虑全局变量在多个用例中被多次更改的情况</span></div>'));
		$('div[name=save_as],div[name=other_data]').show();
	} else if (select_value === 'OTHER_CHANGE_VARIABLE_TYPE') {
		introduce.children('div').text('转换变量的类型。把变量的值转换为指定的类型');
		var type = $('div[name=other_data] textarea').val();
		$('div[name=other_data] textarea').attr('name', '').hide();
		var type_select = $('<select>');
		type_select.addClass('form-control').attr('required', true).attr('name', 'other_data').attr('temp', true);
		type_select.append($('<option value="str">字符串</option>'));
		type_select.append($('<option value="int">整型</option>'));
		type_select.append($('<option value="float">浮点型</option>'));
		type_select.append($('<option value="bool">布尔型</option>'));
		type_select.append($('<option value="datetime">日期</option>'));
		type_select.val(type);
        $('div[name=other_data] [form_data]').append(type_select);
        $('div[name=other_data] .col-1').text('类型');
        $('div[name=save_as] .col-1').html('变量名&nbsp;<i class="icon-question-sign" data-toggle="tooltip" title="需要转换的变量名称"></i>');;
		$('div[name=save_as],div[name=other_data]').show();
	} else if (select_value === 'OTHER_TEXT_PROCESSING') {
		introduce.children('div').html('通过文本验证操作符处理文本并保存为变量，使用方法请参考帮助文档<a name="help_items" url=' + window.text_validation_operators_help_url + ' href="javascript:">《文本验证操作符说明》</a>和<a name="help_items" url=' + window.text_validation_connector_help_url + ' href="javascript:">《文本验证连接符说明》</a>。请使用<a name="help_items" url=' + window.text_verification_test_url + ' href="javascript:">文本验证测试</a>页面自行测试。');
		introduce.append($('<div>例：如果待处理的文本为<span class="mark">cid=123&tid=456</span>，文本验证操作符为<span class="mark">#{re}#tid=(.*)&|tid=(.*)$</span>，将返回<span class="text-info">"456"</span></div>'));
		introduce.append($('<div>例：如果待处理的文本为<span class="mark">{"a": {"a1": "123", "a2": "456"}, "b": "9"}</span>，文本验证操作符为<span class="mark">#{json}#{"a": {"a2": "#{re|,0}#(\\d*)"}}</span>，将返回<span class="text-info">"123"</span></div>'));
        help_items_popup($('[name=help_items]'));
		$('div[name=other_data] .col-1').text('文本验证操作符');
		$('div[name=save_as],div[name=other_data],div[name=other_input]').show();
	} else if (select_value === 'OTHER_VERIFY_EXPRESSION') {
		introduce.children('div').html('验证表达式，条件为真（表达式的计算结果为<span class="text-info">True</span>）时验证通过，否则验证失败');
		show_expression_introduce(introduce)
		introduce.append($('<div>如果填写了“保存为”，验证结果将被保存为变量</div>'));
		$('div[name=save_as],div[name=other_data]').show();
	} else if (select_value === 'OTHER_CALL_SUB_CASE') {
		introduce.children('div').text('调用一个子用例。子用例会继承母用例的变量和配置项。如果出现递归调用，系统将会中断执行');
		$('div[name=other_sub_case],div[name=save_as]').show();
		// 快照页面无需增加底边距容纳下拉列表
		if (!("is_snapshot" in window)) {
			$('[name=detail_content]').css('padding-bottom', '350px');
		}
	} else if (select_value === 'OTHER_IF') {
		introduce.children('div').html('开始一个条件判断分支。如果条件为真（表达式的计算结果为<span class="text-info">True</span>），将执行后续的步骤');
		show_expression_introduce(introduce)
		$('div[name=other_data]').show();
	} else if (select_value === 'OTHER_ELSE_IF') {
		introduce.children('div').html('在条件分支中判断额外条件。如果条件为真（表达式的计算结果为<span class="text-info">True</span>），将执行后续的步骤');
		show_expression_introduce(introduce)
		$('div[name=other_data]').show();
	} else if (select_value === 'OTHER_ELSE') {
		introduce.children('div').text('条件判断分支的否则分支。如果条件为假，将执行后续的步骤');
	} else if (select_value === 'OTHER_END_IF') {
		introduce.children('div').text('条件判断分支的结束标志');
	} else if (select_value === 'OTHER_START_LOOP') {
		introduce.children('div').text('循环开始标志');
	} else if (select_value === 'OTHER_END_LOOP') {
		introduce.children('div').html('根据条件判断是否返回循环开始。如果条件为真（表达式的计算结果为<span class="text-info">True</span>），将返回对应的循环开始标志');
		show_expression_introduce(introduce)
		$('div[name=other_data]').show();
	} else if (select_value === 'DB_EXECUTE_SQL') {
		introduce.children('div').text('执行SQL。如果是select操作且填写了“保存为”，结果集将被保存为变量');
		introduce.append($('<div>结果集会被保存为一个列表，其中的每一条记录被保存为一个字典，字段名作为字段的键，字段值为字典中的值</div>'));
		introduce.append($('<div>例：如果把结果集保存为变量db_result，那么在后续步骤中可以通过表达式$[db_result]$[0]["ID"]调用结果集中第一条结果的ID字段的值</div>'));
		$('div[db],div[name=save_as]').show();
		$('div[name="db_data"]').hide();
	} else if (select_value === 'DB_VERIFY_SQL_RESULT') {
		introduce.children('div').text('执行SQL，并对查询操作的结果集(转换为json格式)进行验证。如果填写了“保存为”，验证结果将被保存为变量');
		$('div[db],div[name=save_as]').show();
	} else if (select_value === 'API_SEND_HTTP_REQUEST') {
		introduce.children('div').text('发送HTTP请求。如果提供了待验证内容，将对执行结果进行验证。如果填写了“保存响应内容”，将把匹配的内容保存为变量。如果填写了“保存为”，验证结果将被保存为变量');
		$('div[api],div[name=save_as]').show();
		init_step_api_save_as();
		// 注册添加按钮
		$('#api_save_as_table #new_helper td[col_move]').off('click').on('click', function () {
			add_step_api_save_as();
		});
		// 注册new helper的删除按钮事件
		$('#api_save_as_table #new_helper [col_del]').off('click').on('click', function () {
			$('#api_save_as_table #new_helper [col_name] input').val('').removeClass('is-invalid').siblings('div.invalid-feedback').remove();
			$('#api_save_as_table #new_helper [col_part] select').val('header');
			$('#api_save_as_table #new_helper [col_expression] input').val('');
		});
		// 启用排序功能
		sortable_api_save_as();
	} else if (select_value === 'API_CREATE_HTTP_SESSION') {
		introduce.children('div').text('创建HTTP请求的SESSION，后续所有的HTTP都会使用同一个SESSION（用于保存Cookies）。如果重复调用这个步骤，可以重置为新SESSION。');
	} else if (select_value === 'API_CREATE_HTTP_SESSION') {
		introduce.children('div').text('删除HTTP请求的SESSION，后续所有的HTTP都使用独立的临时SESSION。');
	} else if ($.inArray(select_value, ["test"]) >= 0) {
		console.error('未知的动作【' +select_value + '】')
	}
	// 注册提示框
	$('[data-toggle=tooltip]').tooltip();
}

// 还原Action相关内容
function reset_action_field(init) {
    $('[temp]').remove();
	$('#introduce').empty().append($('<div>').text('请选择动作'));
	$('div[name=ui_data] .col-1').html('数据');
	$('[common],[ui],[ui_hidden],[api],[db],[other]').hide();
	// $('[common]').hide();
	// $('[ui]').hide();
	// $('[ui_hidden]').hide();
	// $('[api]').hide();
	// $('[db]').hide();
	// $('[other]').hide();
	// 初始化时无需设置底边距，否则快照页面底部会出现多余的空白
	if (!init) {
		$('[name=detail_content]').css('padding-bottom', '100px');
	}
	$('div[name=other_data] .col-1').html('表达式');
	$('div[name=other_data] textarea').attr('name', 'other_data').show();
	$('div[name=save_as] .col-1').html('保存为&nbsp;<i class="icon-question-sign" data-toggle="tooltip" title="填入要保存为的变量名称，不能包含 ${  }$"></i>');
}

// 展示SpecialAction相关内容
function show_special_action_field($actionSelect) {
	reset_special_action_field();
	var select_value = $actionSelect.find('option:selected').val();
	var introduce = $('#introduce');
	if (select_value === '1') {
		introduce.empty().append($('<div>').text('在指定的元素上触发单击，不指定元素则在当前鼠标位置触发'));
		$('[ui]').show();
		$('div[name=ui_data]').hide();
	} else if (select_value === '2') {
		introduce.empty().append($('<div>').text('在指定的元素上触发双击，不指定元素则在当前鼠标位置触发'));
		$('[ui]').show();
		$('div[name=ui_data]').hide();
	} else if (select_value === '3') {
		introduce.empty().append($('<div>').text('在指定的元素上触发右键单击，不指定元素则在当前鼠标位置触发'));
		$('[ui]').show();
		$('div[name=ui_data]').hide();
	} else if (select_value === '4') {
		introduce.empty().append($('<div>').text('在指定的元素上左键点击后不释放，不指定元素则在当前鼠标位置触发'));
		$('[ui]').show();
		$('div[name=ui_data]').hide();
	} else if (select_value === '5') {
		introduce.empty().append($('<div>').text('释放左键点按'));
	} else if (select_value === '6') {
		introduce.empty().append($('<div>').text('鼠标从当前位置偏移一定距离。偏移量x,y为一对半角逗号分隔的数字（单位：像素，水平方向为x轴，左负右正，垂直方向为y轴，上负下正）。例：300,200'));
		$('div[name=ui_data]').show();
		$('div[name=ui_data] .col-1').text('偏移量');
	} else if (select_value === '7') {
		introduce.empty().append($('<div>').text('鼠标从当前位置移动到一个元素（通过定位信息指定）的中间'));
		$('[ui]').show();
		$('div[name=ui_data]').hide();
	} else if (select_value === '8') {
		introduce.empty().append($('<div>').text('鼠标从当前位置移动到一个元素（通过定位信息指定）的左上角，然后偏移一定距离。偏移量x,y为一对半角逗号分隔的数字（单位：像素，水平方向为x轴，左负右正，垂直方向为y轴，上负下正）。例：300,200'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').text('偏移量');
	} else if (select_value === '9') {
		introduce.empty().append($('<div>').text('把一个元素（通过定位信息指定）拖动到目标元素（一个已预先保存为变量的元素）中间'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').html('目标元素&nbsp;<i class="icon-question-sign" data-toggle="tooltip" title="需在之前的步骤预先保存，使用${变量名}$调用"></i>');
	} else if (select_value === '10') {
		introduce.empty().append($('<div>').text('把一个元素（通过定位信息指定）拖动偏移一定距离。偏移量x,y为一对半角逗号分隔的数字（单位：像素，水平方向为x轴，左负右正，垂直方向为y轴，上负下正）。例：300,200'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').text('偏移量');
	} else if (select_value === '11') {
		introduce.empty().append($('<div>').text('按偏移量从当前位置滚动页面。偏移量x,y为一对半角逗号分隔的数字（单位：像素，水平方向为x轴，左负右正，垂直方向为y轴，上负下正）。例：300,200'));
		$('div[name=ui_data]').show();
		$('div[name=ui_data] .col-1').text('偏移量');
	} else if (select_value === '12') {
		introduce.empty().append($('<div>').text('如果某元素（通过定位信息指定）位于页面显示范围之外，则将页面底部滚动到该元素的底部'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').text('偏移量');
	} else if (select_value === '13') {
		introduce.empty().append($('<div>').text('在指定的元素里按下某个键盘按键不释放，不指定元素则在当前焦点所在元素触发。该方法应该只用于发送修饰键（$SHIFT，$CONTROL，$ALT），否则会导致不确定输出结果'));
		introduce.append($('<div>').html('<span class="text-danger">经测试：发送装饰键到指定元素在Chrome浏览器有问题，建议只通过预先设置焦点的方式触发修饰键</span>'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').html('按键&nbsp;<i class="icon-question-sign" data-toggle="tooltip" title="特殊按键以$开头"></i>');
	} else if (select_value === '14') {
		introduce.empty().append($('<div>').text('在指定的元素里释放某个键盘按键，不指定元素则在当前焦点所在元素触发。该方法应该只用于发送修饰键（$SHIFT，$CONTROL，$ALT）'));
		introduce.append($('<div>').html('<span class="text-danger">经测试：发送装饰键到指定元素在Chrome浏览器有问题，建议只通过预先设置焦点的方式触发修饰键</span>'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').html('按键&nbsp;<i class="icon-question-sign" data-toggle="tooltip" title="特殊按键以$开头"></i>');
	} else if (select_value === '15') {
		introduce.empty().append($('<div>').text('向指定的元素发送按键（组）。不指定元素则在当前焦点所在元素触发'));
		introduce.append($('<div>').html('<span class="text-danger">经测试：发送装饰键到指定元素在Chrome浏览器有问题，建议只通过预先设置焦点的方式触发修饰键</span>'));
		introduce.append($('<div>').html('常用的特殊键：<span class="mark">$SHIFT $CONTROL $ALT $ENTER $ESCAPE $SPACE $BACKSPACE $TAB $PAGE_UP $PAGE_DOWN $END $HOME $LEFT $UP $RIGHT $DOWN $INSERT $DELETE $F1~$F12</span>'));
		introduce.append($('<div>').html('其中修饰键是：<span class="mark">$SHIFT $CONTROL $ALT</span>，修饰键发送一次后一直有效，直到出现相同的修饰键。此外，步骤结束后，所有未释放的修饰键会被自动释放。如果需要跨步骤使用修饰键，请使用“键盘 - 按住某键”'));
		introduce.append($('<div>').html('特殊键和普通键之间，以及特殊键和特殊键之间，用+号分隔，连续的普通按键可以不分隔。例如要实现全选删除原有字符后输入Abc，可以使用：<span class="mark">$CONTROL+a+$CONTROL+$BACKSPACE+Abc</span>'));
		introduce.append($('<div>').html('如需输入真正的+号和$号，请添加转义符。例如：<span class="mark">\$CONTROL\+a</span>将被当作字符串<span class="text-info">$CONTROL+a</span>'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').html('按键（组）&nbsp;<i class="icon-question-sign" data-toggle="tooltip" title="特殊按键以$开头，多个特殊按键以+分隔，连续的普通按键可以不分隔，如需输入正常的$和+请用\\转义，如\\$，\\+"></i>');
	}
	// 注册提示框
	$('[data-toggle=tooltip]').tooltip();
}

// 还原special_action相关内容
function reset_special_action_field() {
	$('#introduce').empty().append($('<div>').text('执行一些特殊的互动操作。请选择具体的特殊动作'));
	$('div[name=ui_data] .col-1').html('数据');
	$('[ui]').hide();
	$('div[name=ui_special_action]').show();
}

// 生成带错误提示的输入框
function get_invalid_input($input, check_result){
	$input.removeClass('is-invalid');
	$input.siblings('div.invalid-feedback').remove();
	var errorDiv = $('<div class="invalid-feedback">' + check_result + '</div>');
	$input.addClass('is-invalid');
	$input.after(errorDiv);
}

// 检查是否有未保存的变量
function check_unsaved() {
	var unsaved = false;
	if (window.select_value === 'UI_SELECT') {
		unsaved = check_unsaved_step_ui_data_select();
	} else if (select_value === 'API_SEND_HTTP_REQUEST') {
		unsaved = check_unsaved_step_api_save_as();
	}

	if (unsaved) {
		var msg = '检查到有未保存的内容，是否需要一并提交？';
		bootbox.confirm({
			title: '<i class="icon-exclamation-sign">&nbsp;</i>请确认',
			message: msg,
			size: 'large',
			backdrop: true,
			buttons: {
				confirm: {
					label: '<i class="icon-ok">&nbsp;</i>一并提交',
					className: 'btn-success'
				},
				cancel: {
					label: '<i class="icon-undo">&nbsp;</i>返回修改',
					className: 'btn-secondary'
				}
			},
			callback: function (result) {
				if (result === true) {
					var save = false;
					if (window.select_value === 'UI_SELECT') {
						save = add_step_ui_data_select();
					} else if (select_value === 'API_SEND_HTTP_REQUEST') {
						save = add_step_api_save_as();
					} else {
						save = true;
					}
					if (save) {
						$('#object_form').removeAttr('onsubmit').submit();
					}
				}
			}
		});
	} else {
		var save = false;
		if (window.select_value === 'UI_SELECT') {
			save = update_step_ui_data_select();
		} else if (select_value === 'API_SEND_HTTP_REQUEST') {
			save = update_step_api_save_as();
		} else {
			save = true;
		}
		if (save) {
			$('#object_form').removeAttr('onsubmit').submit();
		}
	}
	return false;
}

// 清空未显示的字段
function clear_hidden_field() {

}