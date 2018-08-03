// 展示Action相关内容
function show_action_field($actionSelect) {
	reset_action_field();
	var select_value = $actionSelect.find('option:selected').val();
	var introduce = $('#introduce')
	if (select_value === '1') {
		introduce.children('span').text('打开一个页面，请填入页面URL');
		$('div[name=ui_data] .col-1').text('URL');
		$('div[name=ui_alert_handle],div[name=ui_data],div[name=timeout]').show();
	} else if (select_value === '2') {
		introduce.children('span').text('触发浏览器刷新页面操作');
		$('div[name=ui_alert_handle],div[name=timeout]').show();
	} else if (select_value === '3') {
		introduce.children('span').text('触发浏览器前进操作');
		$('div[name=ui_alert_handle],div[name=timeout]').show();
	} else if (select_value === '4') {
		introduce.children('span').text('触发浏览器后退操作');
		$('div[name=ui_alert_handle],div[name=timeout]').show();
	} else if (select_value === '6') {
		introduce.children('span').text('获取当前页面截图，如果提供了定位信息则只截取定位到的元素');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_data],div[name=ui_special_action]').hide();
	} else if (select_value === '7') {
		introduce.children('span').text('切换至页面内嵌的frame或iframe。如果提供了定位信息，则切换至定位到的元素绑定的frame，否则切换至索引值对应的frame');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_data],div[name=ui_special_action]').hide();
	} else if (select_value === '8') {
		introduce.children('span').text('回到frame的上一级页面，如进入了多层frame，请使用多次该动作');
		$('div[name=ui_alert_handle],div[name=timeout]').show();
	} else if (select_value === '9') {
		introduce.children('span').text('切换至浏览器的其他窗口或标签。如果提供了定位信息，则切换到包含该元素的窗口，如果提供了窗口标题，则切换到标题中包含该文字的窗口，否则切换至任意一个非当前窗口');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('窗口标题');
	} else if (select_value === '10') {
		introduce.children('span').text('关闭当前浏览器窗口或标签。如果关闭后需要继续测试，请使用切换窗口动作切换至正确的窗口再进行后续操作');
		$('div[name=ui_alert_handle],div[name=timeout]').show();
	} else if (select_value === '11') {
		introduce.children('span').text('关闭浏览器，清空所有缓存，再重新打开浏览器');
		$('div[name=ui_alert_handle],div[name=timeout]').show();
	} else if (select_value === '12') {
		introduce.children('span').text('在指定的元素上触发单击，如果找不到元素或元素当前不可用会报错');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_data],div[name=ui_special_action]').hide();
	} else if (select_value === '13') {
		introduce.children('span').text('在指定的元素上触发双击，如果找不到元素或元素当前不可用会报错');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_data],div[name=ui_special_action]').hide();
	} else if (select_value === '14') {
		introduce.children('span').text('在指定的元素里输入文字，如果找不到元素或元素当前不可用会报错');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('文字内容');
	} else if (select_value === '15') {
		introduce.children('span').text('执行一些特殊的互动操作。请选择具体的特殊动作');
		$('div[name=ui_special_action],div[name=timeout]').show();
		show_special_action_field($('#id_ui_special_action'));
	} else if (select_value === '16') {
		introduce.children('span').text('验证当前页面的URL是否匹配，待验证内容可以为字符串或表达式');
		$('div[name=ui_data] .col-1').text('待验证内容');
		$('div[name=ui_alert_handle],div[name=ui_data],div[name=timeout]').show();
	} else if (select_value === '17') {
		introduce.children('span').text('验证页面是否包含文字（如果待验证内容是输入框内的值，或者是表达式，请指定元素）。如果指定了元素，则验证该元素是否包含文字');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('待验证内容');
	} else if (select_value === '18') {
		introduce.children('span').text('验证页面是否包含指定元素，且该元素可见。可以通过数量表达式验证找到的元素数量，如果不提供表达式则表示找到任意数量的元素都可以通过验证');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').html('<i class="icon-question-sign" data-toggle="tooltip" title="在表达式中以$[x]$代表找到的元素数量。例：1 < $[x]$ <= 5 代表找到的元素数量必须大于1且小于等于5"></i>&nbsp;数量表达式');
	} else if (select_value === '19') {
		introduce.children('span').text('验证页面是否包含指定元素，且该元素不可见');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_special_action],div[name=ui_data]').hide();
	} else if (select_value === '20') {
		introduce.children('span').text('在当前页面执行JavaScript代码。如果指定了元素，可以在代码中通过 arguments[0][0] 调用。例：arguments[0][0].click()');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('js代码');
	} else if (select_value === '21') {
		introduce.children('span').text('在当前页面执行JavaScript代码并验证结果是否为真。验证通过的条件是js代码执行后返回True，如果指定了元素，可以在代码中通过 arguments[0][0] 调用。例：arguments[0][0].click()');
		$('[ui],div[name=timeout]').show();
		$('div[name=ui_special_action]').hide();
		$('div[name=ui_data] .col-1').text('js代码');
	} else if (select_value === '27') {
		introduce.children('span').text('把指定的元素组保存为变量。为统一变量类型，即使定位到唯一元素也会以元素组形式保存');
		$('[ui],div[name=timeout],div[name=save_as]').show();
		$('div[name=ui_special_action],div[name=ui_data]').hide();
	} else if (select_value === '5') {
		introduce.children('span').text('等待若干秒');
		$('div[name=timeout]').show();
	} else if (select_value === '22') {
		introduce.children('span').text('把数值，字符串或表达式的值保存为用例级别的局部变量。在子用例中保存的局部变量可以被调用它的上级用例访问。例：依次运行2个用例，A和B；A调用子用例C，C运行时定义了局部变量bar=1，那么A访问bar得到1；若B也调用C，C运行时定义了局部变量bar=2，那么B访问bar得到2，A访问bar还是1');
		introduce.append($('<br>')).append($('<span>').addClass('mark').text('如果想在表达式中使用字符串，请添加双引号。例："123"不会转换为整型123，而是被保存为字符串"123"'));
		introduce.append($('<br>')).append($('<span>').addClass('mark').text('如果想在表达式中调用变量，请使用$[变量名]$格式。例：假设已有变量x=3，那么 $[x]$+1 返回4；$[x]$==3 返回 True'));
		$('div[name=save_as],div[name=other_data]').show();
	} else if (select_value === '23') {
		introduce.children('span').text('把数值，字符串或表达式的值保存为全局变量。全局变量定义后可以被本次测试的所有用例访问。例：依次运行2个用例，A和B；A调用子用例C，C运行时定义了局部变量bar=1，那么A访问bar得到1；若B也调用C，C运行时定义了局部变量bar=2，那么B访问bar得到2，A访问bar得到2');
		introduce.append($('<br>')).append($('<span>').addClass('mark').text('如果想在表达式中使用字符串，请添加双引号。例："123"不会转换为整型123，而是被保存为字符串"123"'));
		introduce.append($('<br>')).append($('<span>').addClass('mark').text('如果想在表达式中调用变量，请使用$[变量名]$格式。例：假设已有变量x=3，那么 $[x]$+1 返回4；$[x]$==3 返回 True'));
		introduce.append($('<br>')).append($('<span>').addClass('mark').text('如果运行时选择了多线程模式，由于动态定义全局变量的时间不可预期，要考虑全局变量在被调用时还没被定义的情况'));
		$('div[name=save_as],div[name=other_data]').show();
	} else if (select_value === '25') {
		introduce.children('span').text('验证表达式的计算结果是否为真，验证通过的条件是表达式返回True。例：假设已有变量x=3，那么 $[x]$>=3 验证通过；$[x]$>3 验证不通过');
		introduce.append($('<br>')).append($('<span>').addClass('mark').text('如果想在表达式中使用字符串，请添加双引号。例："123"不会转换为整型123，而是被保存为字符串"123"'));
		introduce.append($('<br>')).append($('<span>').addClass('mark').text('如果想在表达式中调用变量，请使用$[变量名]$格式。例：假设已有变量x=3，那么 $[x]$+1 返回4；$[x]$==3 返回 True'));
		$('div[name=other_data]').show();
	} else if (select_value === '26') {
		introduce.children('span').text('调用一个子用例。子用例会继承母用例的变量和配置项。如果出现递归调用，系统将会中断执行');
		$('div[name=other_sub_case]').show();
		$('[name=detail_content]').css('padding-bottom', '350px');
	} else if ($.inArray(select_value, ["test"]) >= 0) {
	}
	// 注册提示框
	$('[data-toggle=tooltip]').tooltip();
}
// 还原Action相关内容
function reset_action_field() {
	$('#introduce').empty().append($('<span>').addClass('mark').text('请选择动作'));
	$('div[name=ui_data] .col-1').html('数据');
	$('[common]').hide();
	$('[ui]').hide();
	$('[api]').hide();
	$('[db]').hide();
	$('[other]').hide();
	$('[name=detail_content]').css('padding-bottom', '100px');
}
// 展示SpecialAction相关内容
function show_special_action_field($actionSelect) {
	reset_special_action_field();
	var select_value = $actionSelect.find('option:selected').val();
	var introduce = $('#introduce');
	if (select_value === '1') {
		introduce.empty().append($('<span>').addClass('mark').text('在指定的元素上触发单击，不指定元素则在当前鼠标位置触发'));
		$('[ui]').show();
		$('div[name=ui_data]').hide();
	} else if (select_value === '2') {
		introduce.empty().append($('<span>').addClass('mark').text('在指定的元素上点击后不释放，不指定元素则在当前鼠标位置触发'));
		$('[ui]').show();
		$('div[name=ui_data]').hide();
	} else if (select_value === '3') {
		introduce.empty().append($('<span>').addClass('mark').text('在指定的元素上触发右键单击，不指定元素则在当前鼠标位置触发'));
		$('[ui]').show();
		$('div[name=ui_data]').hide();
	} else if (select_value === '4') {
		introduce.empty().append($('<span>').addClass('mark').text('在指定的元素上触发双击，不指定元素则在当前鼠标位置触发'));
		$('[ui]').show();
		$('div[name=ui_data]').hide();
	} else if (select_value === '5') {
		introduce.empty().append($('<span>').addClass('mark').text('释放鼠标按键'));
		$('div[name=ui_alert_handle]').show();
	} else if (select_value === '6') {
		introduce.empty().append($('<span>').addClass('mark').text('鼠标从当前位置偏移一定距离。偏移量x,y为一对半角逗号分隔的数字（单位：像素，水平方向为x轴，左负右正，垂直方向为y轴，上正下负）。例：300,200'));
		$('div[name=ui_alert_handle],div[name=ui_data]').show();
		$('div[name=ui_data] .col-1').text('偏移量');
	} else if (select_value === '7') {
		introduce.empty().append($('<span>').addClass('mark').text('鼠标从当前位置移动到一个元素（通过定位信息指定）的中间'));
		$('[ui]').show();
		$('div[name=ui_data]').hide();
	} else if (select_value === '8') {
		introduce.empty().append($('<span>').addClass('mark').text('鼠标从当前位置移动到一个元素（通过定位信息指定）的左上角，然后偏移一定距离。偏移量x,y为一对半角逗号分隔的数字（单位：像素，水平方向为x轴，左负右正，垂直方向为y轴，上正下负）。例：300,200'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').text('偏移量');
	} else if (select_value === '9') {
		introduce.empty().append($('<span>').addClass('mark').text('把一个元素（通过定位信息指定）拖动到目标元素（一个已预先保存为变量的元素）中间'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').html('<i class="icon-question-sign" data-toggle="tooltip" title="需在之前的步骤预先保存，使用${变量名}$调用"></i>&nbsp;目标元素');
	} else if (select_value === '10') {
		introduce.empty().append($('<span>').addClass('mark').text('把一个元素（通过定位信息指定）拖动偏移一定距离。偏移量x,y为一对半角逗号分隔的数字（单位：像素，水平方向为x轴，左负右正，垂直方向为y轴，上正下负）。例：300,200'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').text('偏移量');
	} else if (select_value === '11') {
		introduce.empty().append($('<span>').addClass('mark').text('在指定的元素里按下某个键盘按键不释放，该方法应该只被用于发送修饰键（$SHIFT，$CONTROL，$ALT），否则会导致输入的字符长度不可预期。不指定元素则在当前焦点所在元素触发'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').html('<i class="icon-question-sign" data-toggle="tooltip" title="特殊按键以$开头"></i>&nbsp;按键');
	} else if (select_value === '12') {
		introduce.empty().append($('<span>').addClass('mark').text('在指定的元素里释放某个键盘按键。不指定元素则在当前焦点所在元素触发'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').html('<i class="icon-question-sign" data-toggle="tooltip" title="特殊按键以$开头"></i>&nbsp;按键');
	} else if (select_value === '13') {
		introduce.empty().append($('<span>').addClass('mark').text('向当前焦点所在元素里发送按键（组），修饰键发送一次后一直有效，直到出现相同的修饰键'));
		introduce.append($('<br>')).append($('<span>').addClass('mark').text('常用的特殊键：$SHIFT $CONTROL $ALT $ENTER $ESCAPE $SPACE $BACKSPACE $TAB $PAGE_UP $PAGE_DOWN $END $HOME $LEFT $UP $RIGHT $DOWN $INSERT $DELETE'));
		$('div[name=ui_alert_handle],div[name=ui_data]').show();
		$('div[name=ui_data] .col-1').html('<i class="icon-question-sign" data-toggle="tooltip" title="特殊按键以$开头，多个特殊按键以+分隔，连续的普通按键可以不分隔，如需输入正常的$和+请用\\转义，如\\$，\\+"></i>&nbsp;按键（组）');
	} else if (select_value === '14') {
		introduce.empty().append($('<span>').addClass('mark').text('向指定的元素发送按键（组），修饰键发送一次后一直有效，直到出现相同的修饰键'));
		introduce.append($('<br>')).append($('<span>').addClass('mark').text('常用的特殊键：$SHIFT $CONTROL $ALT $ENTER $ESCAPE $SPACE $BACKSPACE $TAB $PAGE_UP $PAGE_DOWN $END $HOME $LEFT $UP $RIGHT $DOWN $INSERT $DELETE'));
		$('[ui]').show();
		$('div[name=ui_data] .col-1').html('<i class="icon-question-sign" data-toggle="tooltip" title="特殊按键以$开头，多个特殊按键以+分隔，连续的普通按键可以不分隔，如需输入正常的$和+请用\\转义，如\\$，\\+"></i>&nbsp;按键（组）');
	}
	// 注册提示框
	$('[data-toggle=tooltip]').tooltip();
}
// 还原special_action相关内容
function reset_special_action_field() {
	$('#introduce').empty().append($('<span>').addClass('mark').text('执行一些特殊的互动操作。请选择具体的特殊动作'));
	$('div[name=ui_data] .col-1').html('数据');
	$('[ui]').hide();
	$('div[name=ui_special_action]').show();
}