// 验证名称
function check_variable_name(name, variable_name_list_) {
    if (!name || '' === name.trim()) {
        return '名称不能为空'
    }
    let index = $.inArray(name, variable_name_list_);
    if (index >= 0) {
        return '与第[' + (index + 1) + ']行重名'
    }
    return true;
}

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
        update_data_input();
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
        className: 'text-center no-lef-right-padding vertical-align-middle',
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
        className: 'text-center vertical-align-middle'
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
            snapX: 5,
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
            items: 'cell', // 指定选择的是行,
            selector: 'td:nth-child(n+3)'
        }
    };
}

// 创建表格，注册事件
function create_table_and_register_event(baseColumns, data) {
    // 确保data已保存
    update_data_input(data);
    if (window.table) {
        // 销毁现有表格
        table.destroy();
        $('#myTable').empty(); // 必须有这步，否则会导致无法调整列宽
    }
    window.table = $('#myTable').DataTable(get_tableSettings(baseColumns, data));

    // 列表可调宽度
    $('#myTable th:not(:nth-child(1)):not(:nth-child(2))').resizable({
        maxHeight: 1,
        alsoResize: '#myTable'
    });

    // 行排序
    table.off('row-reorder');
    table.on('row-reorder', function (e, details, edit) {
        if (details.length) {
            let original_data = table.rows().data()
            details.forEach((item, index) => {
                table.row(item.newPosition).data(original_data[item.oldPosition])
            });
            // 更新表格显示
            table.draw(false);
        }
    });
    bing_row_data_change();
    bind_change_col_name();
    bind_select_event();
    bind_sub_delete_row_button();
    bind_sub_delete_col_button();
    bind_sub_gtm_button();
}

// 修改data，更新并重绘datatable，重新绑定事件
function bing_row_data_change() {
    let td_textarea = $('#myTable tbody td:nth-child(n+3) textarea');
    // 监听单元格编辑完成的事件
    td_textarea.off('change');
    td_textarea.on('change', function () {
        const newValue = $(this).val();
        const cell = table.cell($(this).closest('td'));
        // 更新单元格数据到 DataTables 内部
        cell.data(newValue);
        console.log('Cell updated:', {
            row: cell.index().row,
            column: cell.index().column,
            newValue: newValue
        });
        table.draw(false);
        bing_row_data_change();
    });
}

// 修改列名
function change_col_name(newName, oldName) {
    if (!check_col_name(newName, oldName)) {
        return;
    }
    // 获取列的索引
    let columnIdx = table.settings()[0].aoColumns.findIndex(col => col.data === oldName);

    if (columnIdx === -1) {
        console.error(`Column with name "${oldName}" not found.`);
        return;
    }

    // 获取表格当前数据
    let updatedData = table.rows().data().toArray().map(row => {
        const reorderedRow = {};

        // 重新排列数据顺序，保持列位置
        table.settings()[0].aoColumns.forEach((col, idx) => {
            if (idx === columnIdx) {
                reorderedRow[newName] = row[oldName]; // 使用新列名
            } else if (col.data in row) {
                reorderedRow[col.data] = row[col.data]; // 保持原列数据
            }
        });
        return reorderedRow;
    });

    // 重新初始化表格
    create_table_and_register_event(baseColumns, updatedData);
}

// 序列化data，更新data_set_data input
function update_data_input(data) {
    let json_str;
    let data_set = {"data": null};
    if (!data || data === "") {
        data_set.data = table.rows().data().toArray();
    } else {
        data_set.data = data
    }
    json_str = JSON.stringify(data_set);
    $('#data_set_data').val(json_str);
}

function create_new_row(row_data) {
    let data = table.rows().data().toArray()
    let emptyObject = {};
    if (!row_data || row_data === "") {
        data.forEach(item => {
            for (let key in item) {
                emptyObject[key] = '';  // 设置空值
            }
        });

    } else {

    }
    data.push(emptyObject);
    create_table_and_register_event(baseColumns, data);
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
            let titles = table.columns().titles().toArray()
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
    let data = table.rows().data().toArray()

    data.forEach(row => {
        row[columnName] = ''; // 添加新列，值为空
    });
    // 重新初始化表格
    create_table_and_register_event(baseColumns, data);
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
function bind_select_event() {
    table.off('select').on('select', function (e, dt, type, indexes) {
        $("#sub_delete_row_button, #sub_delete_col_button").removeAttr("disabled");
    });
    table.off('deselect').on('deselect', function (e, dt, type, indexes) {
        $("#sub_delete_row_button, #sub_delete_col_button").attr("disabled", true);
    });
}

function delete_row(indexes) {
    indexes = JSON.parse(indexes);
    indexes.forEach(item => {
        table.row(item - 1).remove();
    });
    let data = table.rows().data().toArray();
    create_table_and_register_event(baseColumns, data);
}

function bind_sub_delete_row_button() {
    $("#sub_delete_row_button").off("click").on("click", function () {
        const selected = table.cells('.selected').toArray()[0];
        const uniqueRows = [...new Set(selected.map(item => item.row + 1))];
        popup("删除行", "确认要删除以下行吗", JSON.stringify(uniqueRows), true, delete_row);
    });
}

function delete_col(indexes) {
    indexes = JSON.parse(indexes);
    let data = table.rows().data().toArray();
    data.forEach(obj => {
        indexes.forEach(key => {
            delete obj[key]; // 删除对象中的 key
        });
    });
    create_table_and_register_event(baseColumns, data)
}

function bind_sub_delete_col_button() {
    $("#sub_delete_col_button").off("click").on("click", function () {
        const selected = table.cells('.selected').toArray()[0]
        let uniqueCols = []
        let indexes = []
        selected.forEach(item => {
            if (!indexes.includes(item.column)) {
                indexes.push(item.column);
                uniqueCols.push(table.column(item.column).title());
            }
        })
        popup("删除列", "确认要删除以下列吗", JSON.stringify(uniqueCols), true, delete_col)
    });
}


function create_table_from_gtm_data(success, data) {
    console.log(data);
    create_table_and_register_event(baseColumns, data.data)
}

function get_data_from_gtm(tcNumber, version) {
    let gtm = {tcNumber: tcNumber, version: version};
    console.log(gtm);
    getData(get_gtm_data_url, $csrf_input.val(), create_table_from_gtm_data, JSON.stringify(gtm))
}

function bind_sub_gtm_button() {
    $("#sub_gtm_button").off("click").on("click", function () {
        let data_set_str = $('#data_set_data').val();

        let data_set = {gtm: null};

        try {
            data_set = JSON.parse(data_set_str); // 转换字符串为 JSON 对象
        } catch (error) {
            console.error("Invalid JSON string:", error);
        }

        let tcNumber = '';
        let version = '';
        if (data_set.gtm) {
            tcNumber = data_set.gtm.tcNumber
            version = data_set.gtm.version
        }

        let body = $('<div>').addClass('modal-body');
        let div = $('<div>tcNumber</div>');
        body.append(div);
        let input = $('<input class="form-control" autocomplete="off" type="text" id="tcNumber">').attr('value', tcNumber);
        body.append(input);
        div = $('<div>version</div>');
        body.append(div);
        input = $('<input class="form-control" autocomplete="off" type="text" id="version">').attr('value', version);
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
                    get_data_from_gtm($('#tcNumber').val(), $('#version').val())
                }
            }
        }

        bootbox.dialog({
            size: 'large',
            title: '<i class="icon-exclamation-sign">&nbsp;</i>获取GTM数据',
            message: body.html(),
            onEscape: true,
            backdrop: true,
            buttons: buttons
        });
    });
}