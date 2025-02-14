// 生成带错误提示的输入框
function get_invalid_input($input, check_result) {
    $input.removeClass('is-invalid');
    $input.siblings('div.invalid-feedback').remove();
    let errorDiv = $('<div class="invalid-feedback">' + check_result + '</div>');
    $input.addClass('is-invalid');
    $input.after(errorDiv);
}

function check_unsaved() {
    let unsaved = false;

    if (unsaved) {

    } else {
        update_data_set_input();
        $('#object_form').removeAttr('onsubmit').submit();
    }
    return false;
}

window.baseColumns = [
    {
        title: 'MOVE',
        type: 'html',
        defaultContent: '<div class="icon-sort icon-2x"></div>',
        width: '30px',
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
        width: '30px',
        className: 'text-center middle'
    },
];

function get_tableSettings(baseColumns, data) {

    // 检查 data 是否有数据，如果没有数据只使用 baseColumns
    let dynamicColumns = data !== null && data.length > 0
        ? Object.keys(data[0] || {}).map(key => ({
            title: key,
            data: key,
            type: 'string',
            render: function (data, type, row) {
                if (typeof data === 'string') {
                    return `<textarea rows="2" cols="30" class="form-control">${data}</textarea>`;
                }
            },
            width: 100
        }))
        : [];

    let columns = baseColumns.concat(dynamicColumns);

    return {
        data: data,
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
        // colReorder: {
        //     columns: ':gt(1)'
        // },
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
    // 确保data已保存
    // update_data_set_input();
    if ("$table" in window) {
        // 销毁现有表格
        $table.destroy();
        $('#myTable').empty(); // 必须有这步，否则会导致无法调整列宽
    }
    if (data_set.gtm && is_init) {
        get_data_from_gtm();
        return;
    }
    window.$table = $('#myTable').DataTable(get_tableSettings(baseColumns, data_set.data));

    // 列表可调宽度
    table_col_resizable($('#myTable'), 'th:not(:nth-child(1)):not(:nth-child(2))');

    // 行排序
    $table.off('row-reorder');
    $table.on('row-reorder', function (e, details, edit) {
        if (details.length) {
            let original_data = $table.rows().data()
            details.forEach((item, index) => {
                $table.row(item.newPosition).data(original_data[item.oldPosition])
            });
            // 更新表格显示
            $table.draw(false);
        }
    });

    bing_row_data_change();
    bind_change_col_name();
    bind_select_event();
    bind_sub_add_row_button();
    bind_sub_add_col_button();
    bind_sub_delete_row_button();
    bind_sub_delete_col_button();
    bind_sub_gtm_button();
    check_and_set_whether_the_table_is_interactive();
    $('#table_selected_mask').hide();
}

// 修改data，更新并重绘datatable，重新绑定事件
function bing_row_data_change() {
    let td_textarea = $('#myTable tbody td:nth-child(n+3) textarea');
    // 监听单元格编辑完成的事件
    td_textarea.off('change');
    td_textarea.on('change', function () {
        const newValue = $(this).val();
        const cell = $table.cell($(this).closest('td'));
        // 更新单元格数据到 DataTables 内部
        cell.data(newValue);
        console.log('Cell updated:', {
            row: cell.index().row,
            column: cell.index().column,
            newValue: newValue
        });
        $table.draw(false);
        bing_row_data_change();
    });
}

// 修改列名
function change_col_name(newName, oldName) {
    if (!check_col_name(newName, oldName)) {
        return;
    }
    // 获取列的索引
    let columnIdx = $table.settings()[0].aoColumns.findIndex(col => col.data === oldName);

    if (columnIdx === -1) {
        console.error(`Column with name "${oldName}" not found.`);
        return;
    }

    // 获取表格当前数据
    let updatedData = $table.rows().data().toArray().map(row => {
        const reorderedRow = {};

        // 重新排列数据顺序，保持列位置
        $table.settings()[0].aoColumns.forEach((col, idx) => {
            if (idx === columnIdx) {
                reorderedRow[newName] = row[oldName]; // 使用新列名
            } else if (col.data in row) {
                reorderedRow[col.data] = row[col.data]; // 保持原列数据
            }
        });
        return reorderedRow;
    });

    data_set.data=updatedData;
    // 重新初始化表格
    create_table_and_register_event();
}

// 序列化data，更新data_set_data input
function update_data_set_input() {
    let json_str;
    data_set.data = $table.rows().data().toArray();
    json_str = JSON.stringify(data_set);
    $('#data_set_data').val(json_str);
}

function create_new_row(row_data) {
    if (!row_data || typeof row_data === 'undefined' || row_data === "") {
        row_data = {}
        data_set.data.forEach(item => {
            for (let key in item) {
                row_data[key] = '';  // 设置空值
            }
        });
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
    if (data_set.data === null || (Array.isArray(data_set.data) && data_set.data.length === 0)) {
        create_new_row()
    }
    data_set.data.forEach(row => {
        row[columnName] = ''; // 添加新列，值为空
    });
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
            $("#sub_delete_row_button, #sub_delete_col_button").attr("disabled", true);
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
        popup("删除行", "确认要删除以下行吗？（注意：删除全部行会清空列名！）", JSON.stringify(uniqueRows), true, delete_row);
    });
}

function delete_col(indexes) {
    $table.cells().deselect(); // 取消选择
    indexes = JSON.parse(indexes);
    data_set.data.forEach(obj => {
        indexes.forEach(key => {
            delete obj[key]; // 删除对象中的 key
        });
    });
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
        if (!data_set.gtm) {
            data_set.gtm = {};
            data_set.gtm.tcNumber = "";
            data_set.gtm.version = "";
        }

        let body = $('<div>').addClass('modal-body');
        let div = $('<div>tcNumber</div>');
        body.append(div);
        let input = $('<input class="form-control" autocomplete="off" type="text" id="tcNumber">').attr('value', data_set.gtm.tcNumber);
        body.append(input);
        div = $('<div>version</div>');
        body.append(div);
        input = $('<input class="form-control" autocomplete="off" type="text" id="version">').attr('value', data_set.gtm.version);
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
                    if (tcNumber || version) {
                        data_set.gtm.tcNumber = tcNumber;
                        data_set.gtm.version = version;
                        get_data_from_gtm();
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
    // 添加行按钮应该在添加列后激活
    if (data_set.data === null || (Array.isArray(data_set.data) && data_set.data.length === 0)) {
        $('#sub_add_row_button').attr('disabled', true)
    }
}