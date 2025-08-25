// 生成带错误提示的输入框
function get_invalid_input($input, check_result) {
    $input.removeClass('is-invalid');
    $input.siblings('div.invalid-feedback').remove();
    let errorDiv = $('<div class="invalid-feedback">' + check_result + '</div>');
    $input.addClass('is-invalid');
    $input.after(errorDiv);
}

// 获取有data的列名列表
function getColumnsHasData() {
    const currentOrderIndexes = $table.colReorder.order();
    // 过滤掉无 data 属性的列（即固定列）
    return currentOrderIndexes
        .map(index => $table.settings().init().columns[index]) // 获取列配置对象
        .filter(column => column.data) // 仅保留有 data 属性的列
        .map(column => column.data);
}

// 序列化data，获取列序，更新data_set_data input
function update_data_set_input() {
    data_set.data = $table.rows().data().toArray();
    data_set.columns = getColumnsHasData()
    let json_str;
    json_str = JSON.stringify(data_set);
    $('#data_set_data').val(json_str);
}

function check_unsaved() {
    // $('#myTable tbody td:nth-child(n+3) textarea').trigger("change");
    setTimeout(() => {
        update_data_set_input();
        $('#object_form').removeAttr('onsubmit').submit();
    }, 0);
    return false;
}

const COLUMN_WIDTHS = {
  MOVE: 60,
  NUM: 30,
};

const baseColumns = [
    {
        title: 'MOVE',
        type: 'html',
        defaultContent: '<div class="icon-sort icon-2x"></div>',
        width: `${COLUMN_WIDTHS.MOVE}px`,
        className: 'text-center no-lef-right-padding middle',
        orderable: false
    },
    {
        title: '#',
        type: 'string',
        render: function (data, type, row, meta) {
            if (Array.isArray(meta.row)) {
                return meta.row[0] + 1; // 如果是数组，取第一个值 + 1
            } else {
                return meta.row + 1; // 如果不是数组，直接 + 1
            }
        },
        width: `${COLUMN_WIDTHS.NUM}px`,
        className: 'text-center middle'
    },
];

function get_tableSettings(baseColumns, data_set) {
    window._data_set = JSON.parse(JSON.stringify(data_set)) // 深拷贝data_set
    // 单元格渲染函数
    function renderFunction(data, type, row) {
        if (typeof data === 'string') {
            return `<textarea rows="2" cols="30" class="form-control">${data}</textarea>`;
        }
    }
    let dynamicColumns = []
    const has_columns = (_data_set.columns !== undefined && _data_set.columns !== null && _data_set.columns.length > 0);
    const has_data = (_data_set.data !== undefined && _data_set.data !== null && _data_set.data.length > 0 && Object.keys(_data_set.data[0]).length > 0);

    if ((has_data && has_columns && Object.keys(_data_set.data[0]).length > _data_set.columns.length) || (has_data && !has_columns)) { // 如果data的字段数量比columns多，或者有data没columns
        dynamicColumns = Object.keys(_data_set.data[0] || {}).map(col => ({
            title: col,
            data: col,
            type: 'string',
            render: renderFunction,
        }))
    } else if (has_columns) {
        dynamicColumns = _data_set.columns.map(col => ({
            title: col,
            data: col,
            type: 'string',
            render: renderFunction,
        }))
    }

    const columns = baseColumns.concat(dynamicColumns);

    return {
        data: _data_set.data,
        columns: columns,
        order: [[1, 'asc']],
        ordering: false,
        searching: false,
        paging: false,
        info: false,
        autoWidth: false,
        // scrollX: true,
        // scrollY: 400,
        scrollCollapse: true,
        rowReorder: {
            cancelable: true,
            selector: 'td:first-child',
            update: false,
            snapX: 2,
        },

        colReorder: {
            columns: ':gt(1)'
        },
        // fixedHeader: true,
        // fixedColumns: {
        //    left: 2
        //},
        layout: {
            topStart: {
                buttons: ['copy', 'csv', 'excel']
            }
        },
        select: {
            style: 'os', // 选择样式 ('os', 'multi', 'single', 'api')
            items: 'cell', // 指定选择的是单元格
            selector: 'td:nth-child(n+3)'
        }
    };
}

// 创建表格，注册事件
function create_table_and_register_event(is_init) {
    if ("$table" in window) {
        // $table.off('column-reorder'); // 取消注册列排序事件，否则destroy时会再次触发事件导致异常
        // 记录宽度
        window.width = $('#myTable').css('width');
        window.widths = $('#myTable tr[originalTr] th:nth-child(n+3)').map(function() {
            return $(this).css('width');
        }).get();
        $table.destroy(); // 销毁现有表格
        $('#myTable').empty(); // 必须有这步，否则会导致无法调整列宽
    }
    if (data_set.gtm && is_init) {
        get_data_from_gtm();
        return;
    }
    window.$table = $('#myTable').DataTable(get_tableSettings(baseColumns, data_set));

    // 表头上色
    $('#myTable th').css('background-color', 'rgb(233, 236, 239)');
    $('#myTable thead tr').attr('originalTr', true)

    // 恢复宽度
    if (window.width && window.widths) {
        $('#myTable').css('width', window.width);
        $('#myTable th:nth-child(n+3)').each(function(index) {
            let width = window.widths[index];
            if (!width) {
                width = 300; // 新列的宽度
                $('#myTable').css('width', `${parseFloat(window.width)+width}px`);
            }
            $(this).css('width', width); // 强制设置内联样式
        });
    }

    if (!data_set.columns) {
        update_data_set_input();
    }
    if (data_set.columns.length === 0) { // 没有有效数据时不要占满屏幕
        $('#myTable').css('width', COLUMN_WIDTHS.MOVE+COLUMN_WIDTHS.NUM+100);
    }

    // 创建用于调整列宽的行，防止和行排序冲突
    const $originalTr = $('#myTable tr[originalTr]');
    const thCount = 2 + data_set.columns.length;
    const $newTr = $('<tr newTr=true></tr>');
    for (let i = 0; i < thCount; i++) {
        if (i > 1) {
            $newTr.append('<th style="text-align: right; color: lightsteelblue"><div class="icon-resize-horizontal"></div></th>');
        } else {
            $newTr.append('<th></th>');
        }
    }
    $newTr.insertBefore($originalTr);

    // 表头提示设置
    $originalTr.find('th:nth-child(n+3)').attr('title', '双击修改名称，拖动修改排序');
    $newTr.find('th:nth-child(n+3)').attr('title', '拖动本行边框修改宽度');

    // 列表可调宽度
    table_col_resizable($('#myTable'), 'tr[newTr] th:nth-child(n+3)');

    // 监听所有textarea的焦点事件避免数据更新过程中拖动排序导致异常
    window.isTextareaFocused = false
    $('#myTable textarea').off('focus').on('focus', function() {
        $table.rowReorder.enable(false);
        $table.colReorder.enable(false);
        window.isTextareaFocused = true;
    }).off('blur').on('blur', function() {
        $table.rowReorder.enable(true);
        $table.colReorder.enable(true);
        window.isTextareaFocused = false;
    });

    bing_row_data_change();
    bind_change_row_order();
    bind_change_col_order();
    bind_change_col_name();
    bind_select_event();
    bind_sub_add_row_button();
    bind_sub_add_col_button();
    bind_sub_delete_row_button();
    bind_sub_delete_col_button();
    bind_sub_gtm_button();
    check_and_set_whether_the_table_is_interactive();
    $('#table_selected_mask').hide();
    $("#sub_delete_row_button, #sub_delete_col_button").attr("disabled", true);
    float_tr('#myTable tr[originalTr]:not([temp])', window.button_top + get_element_full_height($('#sub_button_group')));
}

// 修改data，更新并重绘datatable，重新绑定事件
function bing_row_data_change() {
    let td_textarea = $('#myTable tbody td:nth-child(n+3) textarea');
    // 监听单元格编辑完成的事件
    td_textarea.off('change').on('change', function () {
        const newValue = $(this).val();
        const cell = $table.cell($(this).closest('td'));
        // 更新单元格数据到 DataTables 内部
        cell.data(newValue);
        // console.log('Cell updated:', {
        //     row: cell.index().row,
        //     column: cell.index().column,
        //     newValue: newValue
        // });
        $table.draw();
        data_set.data = $table.rows().data().toArray();
        create_table_and_register_event();
    });
}

// 行排序
function bind_change_row_order() {
    $table.off('row-reorder').on('row-reorder', function (e, details, edit) {
        if (isTextareaFocused) return;
        if (details.length) {
            let original_data = $table.rows().data()
            details.forEach((item, index) => {
                $table.row(item.newPosition).data(original_data[item.oldPosition])
            });
            // 更新表格显示
            $table.draw();
            data_set.data = $table.rows().data().toArray();
            create_table_and_register_event();
        }
    });
}

// 列排序
function bind_change_col_order() {
    //通过mouseup事件来更新数据，防止拖拽过程中表格重绘导致异常
    window.isDragging = false;
    window.clickTimeout = null;
    $('#myTable th:nth-child(n+3)').on('mousedown', function () {
        if (isTextareaFocused) return;
        window.clickTimeout = setTimeout(() => {
            window.isDragging = true;  // 延迟标记为拖拽，让双击事件能被触发
        }, 300);  // 设置 300ms 延时
    });
    $(document).off('mouseup').on('mouseup', function() {
        if (isTextareaFocused) return;
        if (window.isDragging) {
            window.isDragging = false;
            const newOrderIndexes = $table.colReorder.order();
            // 映射索引到列名（排除无 data 属性的固定列）
            const newColumns = newOrderIndexes
            .map(index => $table.settings().init().columns[index].data) // 获取列配置中的 data 属性
            .filter(data => data !== undefined); // 过滤无 data 的列（如操作列）

            // 更新 data_set.columns
            data_set.columns = newColumns;
            create_table_and_register_event();
        }
    });
}

// 修改列名
function change_col_name(newName, oldName) {
    if (!check_col_name(newName, oldName)) {
        return;
    }
    // 获取列的索引
    // let columnIdx = $table.settings()[0].aoColumns.findIndex(col => col.data === oldName);
    let columnIdx = data_set.columns.indexOf(oldName);

    if (columnIdx === -1) {
        console.error(`Column with name "${oldName}" not found.`);
        return;
    }

    data_set.data.forEach(obj => {
        if (oldName in obj) {
            obj[newName] = obj[oldName];
            delete obj[oldName];
        }
    });
    data_set.columns[columnIdx] = newName;
    // 重新初始化表格
    create_table_and_register_event();
}

function create_new_row(row_data) {
    if (!row_data || typeof row_data === 'undefined' || row_data === "") {
        row_data = {};
        data_set.columns.forEach(col => { row_data[col] = '' }); // 设置空值
    }
    data_set.data.push(row_data);
    create_table_and_register_event();
}

function bind_sub_add_row_button() {
    $('#sub_add_row_button').off('click').click(function () {
        create_new_row();
        $('html, body').animate({
            scrollTop: $(document).height()
        }, 500);
    });
}

function popup(title, message, default_value, readonly, func, other_value) {
    let body = $('<div>').addClass('modal-body');
    let div = $('<div>' + message + '</div>');
    body.append(div);
    let input = $('<input class="form-control" autocomplete="off" type="text" id="dialog_input">').attr('value', default_value);
    if (readonly) {
        input.attr('disabled', true);
    }
    body.append(input);
    let buttons = {
        cancel: {
            label: '<i class="icon-undo">&nbsp;</i>取消',
            className: 'btn btn-secondary'
        },
        ok: {
            label: '<i class="icon-ok">&nbsp;</i>确认',
            className: 'btn btn-primary',
            callback: function () {
                func($('#dialog_input').val(), other_value)
            }
        }
    }

    bootbox.dialog({
        size: 'large',
        title: '<i class="icon-exclamation-sign">&nbsp;</i>' + title,
        message: body.html(),
        onEscape: true,
        backdrop: true,
        buttons: buttons
    });

    // 等弹框渲染完成后，设置选中状态
    setTimeout(function () {
        $('#dialog_input').focus().select();
    }, 500);
}

// 检查字符串是否以数字开头
function startsWithNumber(str) {
    return /^[0-9]/.test(str);
}

// 检查字符串是否在数组中，忽略大小写
function isStringNotInArray(str, strArray) {
    return !strArray.some(item => item.toLowerCase() === str.toLowerCase());
}

function check_col_name(newName, oldName) {
    let passed = false
    let msg = "Passed"
    if (newName !== null && newName.trim() !== '' && newName.trim() !== oldName) {
        if (!startsWithNumber(newName)) {
            let titles = $table.columns().titles().toArray()
            if (isStringNotInArray(newName, titles)) {
                passed = true;
            } else {
                msg = "列名不能重复。"
            }
        } else {
            msg = "列名不能以数字开头。"
        }
    } else {
        msg = "新列名不能为空，也不能和旧列名一致。"
    }

    if (!passed) {
        bootbox.alert({
            title: '<i class="icon-exclamation-sign">&nbsp;</i>请检查',
            message: msg,
            size: 'large',
            backdrop: true,
            buttons: {
                ok: {
                    label: '<i class="icon-undo">&nbsp;</i>返回',
                    className: 'btn-secondary'
                }
            }
        });
    }
    return passed;
}

function create_new_col(columnName) {
    if (!check_col_name(columnName)) {
        return;
    }
    // 如果没有任何数据，先添加一行
    // if (data_set.data === null || (Array.isArray(data_set.data) && data_set.data.length === 0)) {
    //     create_new_row()
    // }
    data_set.data.forEach(row => {
        row[columnName] = ''; // 添加新列，值为空
    });
    data_set.columns.push(columnName);
    // 重新初始化表格
    create_table_and_register_event();
    $('html, body').animate({
        scrollLeft: $(document).width()
    }, 500);
}

function bind_sub_add_col_button() {
    $("#sub_add_col_button").off("click").on("click", function () {
        popup("添加新列", "列名", "", false, create_new_col)
    });
}

// 双击列名修改列名
function bind_change_col_name() {
    $("#myTable th:nth-child(n+3)").off("dblclick").on("dblclick", function () {
        clearTimeout(window.clickTimeout);  // 清除拖拽标记
        window.isDragging = false;  // 强制重置拖拽状态
        let oldName = $(this).text();
        popup("修改【" + oldName + "】列名称", "新列名", oldName, false, change_col_name, oldName)
    });
}

// 选中事件
function bind_select_event(disable) {
    if (disable) {
        $table.off('select').off('deselect');
    } else {
        $table.off('select').on('select', function (e, dt, type, indexes) {
            $("#sub_delete_row_button, #sub_delete_col_button").removeAttr("disabled");
        });
        $table.off('deselect').on('deselect', function (e, dt, type, indexes) {
            if ($table.cells('.selected').toArray()[0].length === 0) {
                $("#sub_delete_row_button, #sub_delete_col_button").attr("disabled", true);
            }
        });
    }
}

function delete_row(indexes) {
    $table.cells().deselect(); // 取消选择
    indexes = JSON.parse(indexes);
    indexes.forEach(item => {
        $table.row(item - 1).remove();
    });
    data_set.data = $table.rows().data().toArray();
    create_table_and_register_event();
}

function bind_sub_delete_row_button() {
    $("#sub_delete_row_button").off("click").on("click", function () {
        const selected = $table.cells('.selected').toArray()[0];
        const uniqueRows = [...new Set(selected.map(item => item.row + 1))];
        popup("删除行", "确认要删除以下行吗？", JSON.stringify(uniqueRows), true, delete_row);
    });
}

function deleteMultipleValueInArray(originalArray, toDeleteValues) {
    const toDeleteSet = new Set(toDeleteValues);
    return originalArray.filter(item => !toDeleteSet.has(item));
}

function delete_col(col_name) {
    $table.cells().deselect(); // 取消选择
    let col_name_list = JSON.parse(col_name);
    data_set.data.forEach(obj => {
        col_name_list.forEach(key => {
            delete obj[key]; // 删除对象中的 key
        });
    });
    data_set.columns = deleteMultipleValueInArray(data_set.columns, col_name_list);
    create_table_and_register_event();
}

function bind_sub_delete_col_button() {
    $("#sub_delete_col_button").off("click").on("click", function () {
        const selected = $table.cells('.selected').toArray()[0]
        let uniqueCols = []
        let indexes = []
        selected.forEach(item => {
            if (!indexes.includes(item.column)) {
                indexes.push(item.column);
                uniqueCols.push($table.column(item.column).title());
            }
        })
        popup("删除列", "确认要删除以下列吗？", JSON.stringify(uniqueCols), true, delete_col)
    });
}


function create_table_from_gtm_data(success, data) {
    if (success) {
        data_set.data = data.data;
        create_table_and_register_event();
        update_mask($('#table_selected_mask'), -1);
    } else {
        console.error(data);
        if (!window.errs) { window.errs = [] }
		window.errs.push("cannot get gtm data");
    }
}

function get_data_from_gtm() {
    update_mask($('#table_selected_mask'), 1);
    getData(get_gtm_data_url, $csrf_input.val(), create_table_from_gtm_data, JSON.stringify(data_set.gtm))
}

function bind_sub_gtm_button() {
    $("#sub_gtm_button").removeAttr('disabled').off("click").on("click", function () {
        let new_gtm = {"tcNumber": "", "version": ""}
        if (data_set.gtm) new_gtm = data_set.gtm;

        let body = $('<div>').addClass('modal-body');
        let div = $('<div>tcNumber</div>');
        body.append(div);
        let input = $('<input class="form-control" autocomplete="off" type="text" id="tcNumber">').attr('value', new_gtm.tcNumber);
        body.append(input);
        div = $('<div>version</div>');
        body.append(div);
        input = $('<input class="form-control" autocomplete="off" type="text" id="version">').attr('value', new_gtm.version);
        body.append(input);
        let buttons = {
            cancel: {
                label: '<i class="icon-undo">&nbsp;</i>取消',
                className: 'btn btn-secondary'
            },
            reset: {
                label: '<i class="icon-undo">&nbsp;</i>取消关联',
                className: 'btn btn-danger',
                callback: function () {
                    delete data_set.gtm;
                    create_table_and_register_event();
                }
            },
            ok: {
                label: '<i class="icon-ok">&nbsp;</i>关联',
                className: 'btn btn-primary',
                callback: function () {
                    let tcNumber = $('#tcNumber').val().trim();
                    let version = $('#version').val().trim();
                    if (tcNumber && version) {
                        data_set.gtm.tcNumber = tcNumber;
                        data_set.gtm.version = version;
                        get_data_from_gtm();
                    } else {
                        bootbox.alert({
                            title: '<i class="icon-exclamation-sign">&nbsp;</i>请检查',
                            message: "请输入正确的 tcNumber 和 version",
                            size: 'large',
                            backdrop: true,
                            buttons: {
                                ok: {
                                    label: '<i class="icon-undo">&nbsp;</i>返回',
                                    className: 'btn-secondary'
                                }
                            }
                        });
                    }
                }
            }
        }
        if (!window.editable) {
            body.find("input").attr('disabled', true);
            delete buttons.reset;
            delete buttons.ok;
        }

        bootbox.dialog({
            size: 'large',
            title: '<i class="icon-exclamation-sign">&nbsp;</i>关联GTM用例',
            message: body.html(),
            onEscape: true,
            backdrop: true,
            buttons: buttons
        });
    });
}

function check_and_set_whether_the_table_is_interactive() {
    // 禁用表格交互
    if (!window.editable || data_set.gtm) {
        let tableContainer = $('#dataTableContainer')
        tableContainer.find('th').off('dblclick').attr('disabled', true);
		tableContainer.find('td, input, textarea, select').off().attr('disabled', true);
        if ("$table" in window) {
            $table.rowReorder.disable();
            $('#sub_button_group button:not(#sub_gtm_button)').off('click').attr('disabled', true);
            bind_select_event(true);
        }
    }
    // 允许非作者查看GTM信息
    if (!window.editable) {
        bind_sub_gtm_button();
    }
    // 取消GTM绑定后，启用行列添加按钮
    if (window.editable && !data_set.gtm) {
        $('#sub_add_row_button, #sub_add_col_button').removeAttr("disabled");
    }
}

function float_tr(tr_selector, top) {
    let $el = $(tr_selector);
    if (!$el || $el.length === 0) {
        return false;
    }
    if (!top) top = 0;
    let el_top = $el.offset().top;
    let original_style = $el.attr('style');
    if (!original_style) {
        original_style = true
    }
    let doing = [];
    let $el_temp = [];

    window.widths = $('#myTable tr[originalTr] th').map(function() {
        return get_element_full_width($(this));
    }).get();

    $(window).off('scroll.float_tr').on('scroll.float_tr', function () {
        if (doing.length > 0) return false;  // 防止频繁判断导致跳动
        $el = $(tr_selector)
        if (!$el.data('float')) el_top = $el.offset().top;  // 未浮动时通过自身确定位置
        const el_height = get_element_full_height($el);
        const el_width = get_element_full_width($el);
        const is_vertical_out= $(window).scrollTop() > el_top - top;

        if (window.widths) {
            $el.find('th').each(function(index) {
                let width = window.widths[index];
                if (index===0) { // 保持前两列固定宽度
                    width = parseFloat(width) < COLUMN_WIDTHS.MOVE ? width : `${COLUMN_WIDTHS.MOVE}px`
                } else if (index===1) {
                    width = parseFloat(width) < COLUMN_WIDTHS.NUM ? width : `${COLUMN_WIDTHS.NUM}px`
                }
                $(this).css('width', width); // 强制设置内联样式
            });
        }

        if (is_vertical_out) {
            if (!$el.data('float')) {
                doing.push(true);
                setTimeout(function () {
                    doing.pop();
                }, 50);
                $el_temp = $el.clone().insertAfter($el).css('visibility', 'hidden').attr('temp', true);  // 占位
                $el_temp.removeAttr('id').removeAttr('name').find('*').removeAttr('id').removeAttr('name');  // 防止和占位元素交互

                $el.height(el_height);
                $el.css('min-width', el_width);
                $el.css({
                    'position': 'fixed',
                    'top': top + 'px',
                    'z-index': 998,
                });
                $el.data('float', original_style);
            } else {
                // 浮动时通过占位元素确定大小及位置
                // $el.width(el_width);
                $el.height(el_height);
                $el.css('top', top + 'px');
            }
            // 动态更新其水平位置
            $el.css('left', $el_temp[0].getBoundingClientRect().left + 'px');
            // 动态更新宽度
            // window.widths_new = $el_temp.find('th').map(function() {
            //     return get_element_full_width($(this));
            // }).get();
            // if (window.widths_new) {
            //     $el.find('th').each(function(index) {
            //         let width = window.widths_new[index];
            //         $(this).css('width', width); // 强制设置内联样式
            //     });
            // }
        } else {
            const style = $el.data('float');
            if (style) {
                $el.data('float', false);
                if ($el_temp.length > 0) {
                    $el_temp.remove();
                }  // 取消占位
                if (style !== true) {
                    $el.attr('style', style);
                } else {
                    $el.removeAttr('style');
                }
            }
        }
    })
}