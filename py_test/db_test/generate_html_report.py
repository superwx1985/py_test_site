import dominate
import os
from dominate.tags import *


def create_step(step_list, full_case_id):
    for step in step_list:
        step_id = str(step.id)
        full_id = full_case_id + '-' + step_id
        level_id = full_case_id
        case_id = full_case_id
        status = step.status
        if status == 'p':
            step_class = 'passStep'
            step_state = 'PASS'
        elif status == 's':
            step_class = 'skipStep'
            step_state = 'SKIP'
        elif status == 'e':
            step_class = 'errorStep'
            step_state = 'ERROR'
        elif status == 'f':
            step_class = 'failStep'
            step_state = 'FAIL'
        elif status == 'o':
            step_class = 'otherStep'
            step_state = 'SUCCESS'
        with tr(id='step_' + full_id, name='step_' + full_id, cid=case_id, lid=level_id, sid=step_id, type='tr_step',
                state=status):
            td(a(full_id, href='javascript:;',
                 onclick="this.style.color='#800080';toggleStepDetail('%s', '%s')" % (case_id, full_id)),
               id='step_id_column_%s' % full_id,
               style='white-space:nowrap;border-bottom: 2px solid #AAAAAA; overflow: auto;', cls=step_class,
               type='id_column')
            td(span(step.name, cls='pre_span'), id='step_step_column_%s' % full_id,
               style='border-bottom: 2px solid #AAAAAA; overflow: auto;')
            td(a(step_state, href='javascript:;',
                 onclick="this.style.color='#800080';toggleStepDetail('%s', '%s')" % (case_id, full_id)),
               id='step_state_column_%s' % full_id, style='border-bottom: 2px solid #AAAAAA;', colspan='6',
               cls=step_class, type='state_column')
            step_elapsed_time = round((step.end_time - step.start_time).total_seconds(), 3)
            td(step_elapsed_time, id='step_time_column_%s' % full_id,
               style='border-bottom:2px solid #AAAAAA; text-align:center')
        with tr(id='step_detail_1_%s' % full_id, cid=case_id, lid=level_id, sid=step_id, type='tr_detail',
                state=status):
            td(span('database type:', cls='boldFont'), br(), span(step.data_dict['database_type'], cls='pre_span'),
               style='overflow: auto;')
            td(span('database host:', cls='boldFont'), br(), span(step.data_dict['database_host'], cls='pre_span'),
               colspan='7',
               style='overflow: auto;')
        with tr(id='step_detail_2_%s' % full_id, cid=case_id, lid=level_id, sid=step_id, type='tr_detail',
                state=status):
            td(span('database port:', cls='boldFont'), br(), span(step.data_dict['database_port'], cls='pre_span'),
               style='overflow: auto;')
            td(span('database name:', cls='boldFont'), br(), span(step.data_dict['database_name'], cls='pre_span'),
               colspan='7',
               style='overflow: auto;')
        with tr(id='step_detail_3_%s' % full_id, cid=case_id, lid=level_id, sid=step_id, type='tr_detail',
                state=status):
            td(span('user:', cls='boldFont'), br(), span(step.data_dict['user'], cls='pre_span'),
               style='overflow: auto;')
            td(span('password:', cls='boldFont'), br(), span(step.data_dict['password'], cls='pre_span'), colspan='7',
               style='overflow: auto;')
        with tr(id='step_detail_4_%s' % full_id, cid=case_id, lid=level_id, sid=step_id, type='tr_detail',
                state=status):
            td(span('SQL:', cls='boldFont'), br(), span(step.data_dict['sql'], cls='pre_span'),
               style='overflow: auto;')
            td(span('expect:', cls='boldFont'), br(), span(step.data_dict['expect'], cls='pre_span'), colspan='7',
               style='overflow: auto;')
        with tr(id='step_detail_5_%s' % full_id, cid=case_id, lid=level_id, sid=step_id, type='tr_detail',
                state=status):
            td(div(step.message, cls='pre_div'), style='border-bottom:2px solid #AAAAAA; height:180px',
               colspan='8')


def generate_report(result_dir, report_file_name, case_result_list, start_time, end_time,
                    report_title='Automation Test Report'):
    report_file_name = os.path.splitext(report_file_name)[0]  # 保证report_file_name不带后缀名
    # 创建报告目录
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    all_case_count = 0
    pass_case_count = 0
    fail_case_count = 0
    error_case_count = 0
    skip_case_count = 0
    for case_result in case_result_list:
        all_case_count += 1
        if case_result.status == 'p':
            pass_case_count += 1
        elif case_result.status == 'f':
            fail_case_count += 1
        elif case_result.status == 'e':
            error_case_count += 1
        else:
            skip_case_count += 1
        # db测试暂不支持调用子用例
        # for step in case_result.step_list:
        #     if step.data_dict['action'] == 'sub case' and step.status != 's' and type(step.message.step_list) == list:
        #         sub_case_result = step.message
        #         sub_result_dir = os.path.join(result_dir, 'sub_case')
        #         sub_report_file_name = '%s_%s' % (sub_case_result.id, os.path.splitext(sub_case_result.name)[0])
        #         sub_report_title = '子用例【%s】' % sub_report_file_name
        #         generate_case_report(case_type=sub_case_result.type, result_dir=sub_result_dir,
        #                              report_file_name=sub_report_file_name, case_result_list=(sub_case_result,),
        #                              start_time=sub_case_result.start_time, end_time=sub_case_result.end_time,
        #                              report_title=sub_report_title)

    elapsed_time = end_time - start_time
    d = dominate.document(title=report_title, doctype='<!DOCTYPE HTML>', )
    css_str = '''
    body {
        font-family: verdana, arial, helvetica, sans-serif;
        font-size: 80%;
        width: 99%;}
    table {font-size: 100%; }
    a:visited {color:#800080; }
    a:hover {color:red; }
    
    /* -- heading ---------------------------------------------------------------------- */
    
    .heading {
        margin-top: 0ex;
        font-size: 16pt;
        color: gray;
        font-weight: bold;
    }
    #time { width:100%; }
    #time div {
        white-space: nowrap;
        width: 300px;
        display: table-cell;
        /*border: 1px solid red;*/
    }
    #summary { width:100%;}
    #summary div {
        white-space: nowrap;;
        display: table-cell;
        /*border: 1px solid red;*/
    }
    
    /* -- report ------------------------------------------------------------------------ */
    td {
        word-wrap:break-word;
        overflow:hidden;
    }
    #result_table {
        table-layout:fixed;
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #AAAAAA;
    }
    #header_row {
        font-weight: bold;
        color: white;
        background-color: #777777;
        text-shadow: black 2px 2px 2px;
    }
    #result_table td {
        padding: 2px;
        border: 1px solid #AAAAAA;
        height: 60px;
    }
    .case  { font-weight: bold; }
    .allCase { background-color: #EEEEEE; }
    .runCase { background-color: #DDDDDD; }
    .passCase { background-color: limegreen; }
    .skipCase { background-color: #CCFF99; }
    .failCase { background-color: #FFCC22; }
    .errorCase { background-color: #FF3333; }
    .allStep { background-color: #EEEEEE; }
    .runStep { background-color: #DDDDDD; }
    .passStep { background-color: limegreen; }
    .skipStep { background-color: #CCFF99; }
    .failStep { background-color: #FFCC22; font-weight: bold; }
    .errorStep { background-color: #FF3333; font-weight: bold;}
    .otherStep { background-color: #CCFF99; }
    td[type='state_column'] a {color: black;}
    td[type='state_column'] a:hover {color: white;}
    td[type='id_column'] a {color: black;}
    td[type='id_column'] a:hover {color: white;}
    td[type='state_column'] {text-align:center;}
    td[type='id_column'] {text-align:center;}

    .testStep { margin-left: 2em; }
    .boldFont { font-weight: bold; }
    tr[type='tr_step'] {display: none;}
    tr[type='tr_detail'] {display: none;}
    tr[trcls='passStep'] { background-color: #6c6; }
    tr[trcls='skipStep'] { background-color: #DDDDDD; }
    tr[trcls='failStep'] { background-color: #c60; font-weight: bold; }
    tr[trcls='errorStep'] { background-color: #c00; font-weight: bold; }
    tr[trcls='otherStep'] { background-color: #DDDDDD; }
    
    .pre_div {
        width: 100%;
        height: 100%;
        border-width: 0;
        border: 0;
        overflow: auto;
        margin: 0;
        padding: 0;
        text-align: left;
        /*text-align: inherit;
        vertical-align:inherit;
        font-family: inherit;
        font-size: inherit;*/
        white-space: pre;
        word-wrap: normal;
    }
    
    .pre_span {
        /*width: 100%;
        height: 100%;*/
        border-width: 0;
        border: 0;
        overflow: auto;
        margin: 0;
        padding: 0;
        text-align: left;
        /*text-align: inherit;
        vertical-align:inherit;
        font-family: inherit;
        font-size: inherit;*/
        white-space: pre;
        word-wrap: normal;
    }
    /* -- ending ---------------------------------------------------------------------- */
'''

    script_str = '''
var show = [];
var show_case = [];
var show_detail = [];
var case_id_list = new Array();
${fill_case_id_list}$

function arrContainsObj(arr, obj) {
    var i = arr.length;
    while (i--) {
        if (arr[i] === obj) {
            return true;
        }
    }
    return false;
}

function arrRemoveObj(arr, obj) {
    var i = arr.length;
    while (i--) {
        if(arr[i] == obj) {
            arr.splice(i, 1);
            break;
        }
    }
}

function hideAllSteps() {
    for (var i in case_id_list) {
        case_id = case_id_list[i];
        document.getElementById('css_step_'+case_id).innerHTML='tr[cid=|dd|'+case_id+'|dd|][type=|dd|tr_step|dd|] {display:none;}'
        document.getElementById('css_step_detail_show_'+case_id).innerHTML='tr.show[cid=|dd|'+case_id+'|dd|][type=|dd|tr_detail|dd|] {display:none;}'
    }
    show= []
    show_case = []
}

function toggleTestCase(cid) {
    cid = cid.toString()
    if (arrContainsObj(show, cid)) {
        arrRemoveObj(show, cid)
        document.getElementById('css_step_'+cid).innerHTML=''
        document.getElementById('css_step_detail_show_'+cid).innerHTML=''
        var temp = []
        for (var i = 0; i |lessthan| show_case.length; i++) {
            if (show_case[i].substr(0,cid.length) != cid) {
                temp.push(show_case[i])
            }
        }
        show_case = temp.slice(0)
    }
    else {
        show.push(cid)
        document.getElementById('css_step_'+cid).innerHTML='tr[cid=|dd|'+cid+'|dd|][lid=|dd|'+cid+'|dd|][type=|dd|tr_step|dd|] {display:table-row;}'
        document.getElementById('css_step_detail_show_'+cid).innerHTML='tr.show[cid=|dd|'+cid+'|dd|][lid=|dd|'+cid+'|dd|][type=|dd|tr_detail|dd|] {display:table-row;}'
        document.getElementById('css_step_filter_'+cid).innerHTML=''
    }
}

function hideShareSteps(cid, lid) {
    if (arrContainsObj(show_case, lid)) {
        var temp = []
        for (var i = 0; i |lessthan| show_case.length; i++) {
            if (show_case[i].substr(0,lid.length) != lid) {
                temp.push(show_case[i])
            }
        }
        show_case = temp.slice(0)
        var css = 'tr[cid=|dd|'+cid+'|dd|][lid=|dd|'+cid+'|dd|][type=|dd|tr_step|dd|] {display:table-row;}'
        var css2 = 'tr.show[cid=|dd|'+cid+'|dd|][lid=|dd|'+cid+'|dd|][type=|dd|tr_detail|dd|] {display:table-row;}'
        for (var i = 0; i |lessthan| show_case.length; i++) {
            css = css + 'tr[cid=|dd|'+cid+'|dd|][lid=|dd|'+show_case[i]+'|dd|][type=|dd|tr_step|dd|] {display:table-row;}'
            css2 = css2 + 'tr.show[cid=|dd|'+cid+'|dd|][lid=|dd|'+show_case[i]+'|dd|][type=|dd|tr_detail|dd|] {display:table-row;}'
        }
        document.getElementById('css_step_'+cid).innerHTML=css
        document.getElementById('css_step_detail_show_'+cid).innerHTML=css2
        return true
    } else {
        return false
    }
}

function showShareSteps(cid, lid) {
    show_case.push(lid)
    document.getElementById('css_step_'+cid).innerHTML = document.getElementById('css_step_'+cid).innerHTML + 'tr[cid=|dd|'+cid+'|dd|][lid=|dd|'+lid+'|dd|][type=|dd|tr_step|dd|] {display:table-row;}'
    document.getElementById('css_step_detail_show_'+cid).innerHTML = document.getElementById('css_step_detail_show_'+cid).innerHTML + 'tr.show[cid=|dd|'+cid+'|dd|][lid=|dd|'+lid+'|dd|][type=|dd|tr_detail|dd|] {display:table-row;}'
}

function toggleShareSteps(cid, lid) {
    if (!hideShareSteps(cid, lid)) {showShareSteps(cid, lid)}
}

function showStateSteps(cid, state) {
    cid = cid.toString()
    if (!arrContainsObj(show, cid)) {
        toggleTestCase(cid)
    }
    var state_=[]
    if (state.indexOf(',') |morethan| 0) {
        state_ = state.split(',');
    }
    else {
        state_=[state]
    }
    states=['p','f','e','o','s']
    css = ''
    for (var i = 0; i |lessthan| states.length; i++) {
        if (arrContainsObj(state_,states[i])) {
            continue
        }
        css = css + 'tr[cid=|dd|'+cid+'|dd|][type=|dd|tr_step|dd|][state=|dd|'+states[i]+'|dd|] {display:none;}'
        css = css + 'tr[cid=|dd|'+cid+'|dd|][type=|dd|tr_detail|dd|][state=|dd|'+states[i]+'|dd|] {display:none;}'
    }
    document.getElementById('css_step_filter_'+cid).innerHTML=css
    var temp = []
    for (var i = 0; i |lessthan| show_detail.length; i++) {
        if (show_detail[i].substr(0,cid.length) == cid) {
            temp.push(show_detail[i])
        }
    }
    for (var i = 0; i |lessthan| temp.length; i++) {
        toggleStepDetail(cid, temp[i])
    }
}

function toggleStepDetail(cid, full_id) {
    var e1 = document.getElementById('step_detail_1_'+full_id)
    var e2 = document.getElementById('step_detail_2_'+full_id)
    var e3 = document.getElementById('step_id_column_'+full_id)
    var e4 = document.getElementById('step_step_column_'+full_id)
    var e5 = document.getElementById('step_state_column_'+full_id)
    var e6 = document.getElementById('step_time_column_'+full_id)
    var e7 = document.getElementById('step_detail_3_'+full_id)
    var e8 = document.getElementById('step_detail_4_'+full_id)
    var e9 = document.getElementById('step_detail_5_'+full_id)
    if (arrContainsObj(show_detail, full_id)) {
        arrRemoveObj(show_detail, full_id)
        hideShareSteps(cid, full_id)
        e1.className = '';
        e2.className = '';
        e7.className = '';
        e8.className = '';
        e9.className = '';
        e3.setAttribute('rowspan',1);
        e4.style.borderBottom='2px solid #AAAAAA';
        e5.style.borderBottom='2px solid #AAAAAA';
        e6.style.borderBottom='2px solid #AAAAAA';
    }
    else {
        show_detail.push(full_id)
        e1.className = 'show';
        e2.className = 'show';
        e7.className = 'show';
        e8.className = 'show';
        e9.className = 'show';
        e3.setAttribute('rowspan',6);
        e4.style.borderBottom='';
        e5.style.borderBottom='';
        e6.style.borderBottom='';
    }
}'''

    with d.head:
        meta(http_equiv='Content-Type', content='text/html; charset=utf-8')
        style(css_str, type='text/css', media='screen', id='css0')
        fill_case_id_list = '\n'
        i = 0
        for case_result in case_result_list:
            case_id_str = str(case_result.id)
            css_step = "tr[cid='" + case_id_str + "'][type='tr_step'] {display: none;}"
            style(css_step, type='text/css', media='screen', id='css_step_' + case_id_str)
            css_step_detail_show = "tr.show[cid='" + case_id_str + "'][type='tr_detail'] {display: none;}"
            style(css_step_detail_show, type='text/css', media='screen', id='css_step_detail_show_' + case_id_str)
            style("", type='text/css', media='screen', id='css_step_filter_' + case_id_str)
            fill_case_id_list = fill_case_id_list + "case_id_list[%d]='%s';\n" % (i, case_id_str)
            i += 1
        script(script_str.replace('${fill_case_id_list}$', fill_case_id_list))

    with d.body:
        div(report_title, cls='heading')
        with div(id='time'):
            div('开始时间', cls='boldFont', style="width:100px;")
            div(str(start_time))
            div('结束时间', cls='boldFont', style="width:100px;")
            div(str(end_time))
            div('测试用时', cls='boldFont', style="width:100px;")
            div(str(elapsed_time))
        with div(id='summary'):
            div('用例统计', style="width:100px; font-weight:bold;")
            div('全部\t%r' % all_case_count, cls='allCase',
                style="text-align:center; width:100px; font-weight:normal; white-space:pre;")
            div('通过\t%r' % pass_case_count, cls='passCase',
                style="text-align:center; width:100px; font-weight:normal; white-space:pre;")
            div('失败\t%r' % fail_case_count, cls='failCase',
                style="text-align:center; width:100px; font-weight:normal; white-space:pre;")
            div('出错\t%r' % error_case_count, cls='errorCase',
                style="text-align:center; width:100px; font-weight:normal; white-space:pre;")
            div('跳过\t%r' % skip_case_count, cls='skipCase',
                style="text-align:center; width:100px; font-weight:normal; white-space:pre;")
        with div(style="text-align:right;"):
            button('收起用例详情', onclick='hideAllSteps()', id='hide_all_details_button_1')
        with table(id='result_table'):
            with tr(id='header_row', type='tr_header', style='text-align:center;'):
                td('ID', style='white-space:nowrap; width:60px')
                td('用例/步骤名称', style='white-space:nowrap')
                td('全部', style='white-space:nowrap; width:6.5%', cls='allCase')
                td('通过', style='white-space:nowrap; width:6.5%', cls='passCase')
                td('失败', style='white-space:nowrap; width:6.5%', cls='failCase')
                td('出错', style='white-space:nowrap; width:6.5%', cls='errorCase')
                td('跳过', style='white-space:nowrap; width:6.5%', cls='skipCase')
                td('其他', style='white-space:nowrap; width:6.5%', cls='skipCase')
                td('耗时', style='width:70px')
            for case_result in case_result_list:
                case_id = str(case_result.id)
                if case_result.status == 'p':
                    case_class = 'passCase'
                elif case_result.status == 'f':
                    case_class = 'failCase'
                elif case_result.status == 'e':
                    case_class = 'errorCase'
                else:
                    case_class = 'skipCase'
                with tr(id='case_' + case_id, name=case_result.name, cls='case', type='tr_case'):
                    td(a(case_id, href='javascript:;',
                         onclick="this.style.color='#800080';toggleTestCase('%s')" % case_id),
                       style='white-space:nowrap;border-bottom: 2px solid #AAAAAA;', cls=case_class, type='id_column')
                    td(a(case_result.name, href='javascript:;',
                         onclick="this.style.color='#800080';toggleTestCase('%s')" % case_id),
                       style='border-bottom: 2px solid #AAAAAA;')
                    td(a(case_result.all_step_count, href='javascript:;',
                         onclick="this.style.color='#800080';showStateSteps('%s','p,f,e,s,o')" % case_id),
                       style='border-bottom: 2px solid #AAAAAA;', cls='allStep', type='state_column')
                    td(a(case_result.pass_step_count, href='javascript:;',
                         onclick="this.style.color='#800080';showStateSteps('%s','p')" % case_id),
                       style='border-bottom: 2px solid #AAAAAA;', cls='passStep', type='state_column')
                    td(a(case_result.fail_step_count, href='javascript:;',
                         onclick="this.style.color='#800080';showStateSteps('%s','f')" % case_id),
                       style='border-bottom: 2px solid #AAAAAA;', cls='failStep', type='state_column')
                    td(a(case_result.error_step_count, href='javascript:;',
                         onclick="this.style.color='#800080';showStateSteps('%s','e')" % case_id),
                       style='border-bottom: 2px solid #AAAAAA;', cls='errorStep', type='state_column')
                    td(a(case_result.skip_step_count, href='javascript:;',
                         onclick="this.style.color='#800080';showStateSteps('%s','s')" % case_id),
                       style='border-bottom: 2px solid #AAAAAA;', cls='skipStep', type='state_column')
                    td(a(case_result.other_step_count, href='javascript:;',
                         onclick="this.style.color='#800080';showStateSteps('%s','o')" % case_id),
                       style='border-bottom: 2px solid #AAAAAA;', cls='otherStep', type='state_column')
                    case_elapsed_time = round((case_result.end_time - case_result.start_time).total_seconds(), 3)
                    td(case_elapsed_time,
                       style='border-bottom: 2px solid #AAAAAA; text-align:center; font-weight:normal')
                create_step(case_result.step_list, case_id)
        with div(style="text-align:right;"):
            button('收起用例详情', onclick='hideAllSteps()', id='hide_all_details_button_2')
        br()

    report = str(d).replace('|and|', '&').replace('|lessthan|', '<').replace('|morethan|', '>').replace('|dd|', '"')

    report_file_name = report_file_name + '.html'
    report_name = os.path.join(result_dir, report_file_name)

    with open(report_name, 'w', encoding='utf-8') as f:  # 必须带编码参数，否则含有中文时容易报错
        f.write(report)
    return report_name
