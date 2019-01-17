import ast
import datetime
import logging
from copy import deepcopy


class EvalObject:
    def __init__(self, eval_expression, variable_dict=None, logger=logging.getLogger('py_test')):
        if isinstance(eval_expression, str):
            self.__eval_expression = eval_expression.replace('\n', '').replace('\r', '').strip()
        else:
            raise ValueError('Eval expression should be str class')
        # 不建议把__valid_operator_list作为参数开放给调用者
        # =======================================================================
        # if isinstance(valid_operator_list, list):
        #     self.__valid_operator_list = valid_operator_list
        # else:
        #     raise ValueError('Valid operator list should be list class')
        # =======================================================================
        # 必须把较长的操作符放在前面
        self.__valid_operator_list = ['round',
                                      'not', 'and',
                                      'or', 'in', '==', '!=', '<=', '>=', '**', '//', '<<', '>>',
                                      '<', '>', '(', ')', '[', ']', '+', '-', '*', '/', '%', '&', '|', '^', '~', ',']
        if variable_dict is None:
            variable_dict = dict()
        if isinstance(variable_dict, dict):
            self.__variable_dict = variable_dict
        else:
            raise ValueError('Variables should be dict class, now is %s' % type(variable_dict))
        # self.__invalid_value_list = self.get_invalid_value_list()
        self.__left_separator = '$['
        self.__right_separator = ']$'
        self.logger = logger

    # 去掉表达式中的变量
    def _get_without_variables_expression(self, expression):
        for k in self.__variable_dict.keys():
            if not isinstance(k, str):
                raise ValueError('Variables\' key should be str class')
            k = self.__left_separator + k.replace(self.__left_separator, '').replace(
                self.__right_separator, '') + self.__right_separator
            expression = expression.replace(k, '')
        return expression

    # 去掉表达式中的字符串
    @staticmethod
    def _get_without_string_expression(expression):
        expression = expression.replace('\\"', '').replace("\\'", '')
        _str = "'''"
        while True:
            start_index = expression.find(_str)  # 找第一个左边界
            end_index = expression.find(_str, start_index + len(_str))  # 找第一个左边界右边的第一个右边界
            if start_index < 0 or end_index < 0:  # 以上任意一个边界找不到则结束替换
                break
            else:
                expression = expression[:start_index] + expression[end_index + len(_str):]
        _str = '"'
        while True:
            start_index = expression.find(_str)  # 找第一个左边界
            end_index = expression.find(_str, start_index + len(_str))  # 找第一个左边界右边的第一个右边界
            if start_index < 0 or end_index < 0:  # 以上任意一个边界找不到则结束替换
                break
            else:
                expression = expression[:start_index] + expression[end_index + len(_str):]
        _str = "'"
        while True:
            start_index = expression.find(_str)  # 找第一个左边界
            end_index = expression.find(_str, start_index + len(_str))  # 找第一个左边界右边的第一个右边界
            if start_index < 0 or end_index < 0:  # 以上任意一个边界找不到则结束替换
                break
            else:
                expression = expression[:start_index] + expression[end_index + len(_str):]
        return expression

    # 去掉有效操作符，返回表达式值列表
    def _get_new_value_list(self, value_list, valid_operator_list):
        operator = valid_operator_list[0]
        del valid_operator_list[0]
        new_value_list = list()
        for value in value_list:
            new_value_list.extend(value.split(operator))
        if valid_operator_list:
            new_value_list = self._get_new_value_list(new_value_list, valid_operator_list)
        return new_value_list

    # 去掉表达式中的变量，常量，有效操作符，返回表达式值列表
    def _get_value_list(self):
        _valid_operator_list = deepcopy(self.__valid_operator_list)
        expression = self._get_without_variables_expression(self.__eval_expression)
        expression = self._get_without_string_expression(expression)
        return self._get_new_value_list([expression], _valid_operator_list)

    def check_eval_expression(self):
        result = True
        invalid_value_list = []
        value_list = list()
        try:
            value_list = self._get_value_list()
        except Exception as e:
            result = False
            invalid_value_list = e
            self.logger.error('Get value list error')
            if self.logger.level < 10:
                raise
        for value in value_list:
            value = value.strip()
            if value != '':
                try:
                    ast.literal_eval(value)
                except:
                    result = False
                    invalid_value_list.append(value)
                    self.logger.error('Invalid value [%s] ' % value)
                    if self.logger.level < 10:
                        raise
        e = ValueError('Invalid value list: {}'.format(invalid_value_list))
        return result, e

    # 替换表达式中的变量
    def get_final_expression(self):
        final_expression = self.__eval_expression
        locals_dict = dict()
        for k, v in self.__variable_dict.items():
            if not isinstance(k, str):
                raise ValueError('Variables\' key should be str class')
            # 加上左右边界，但不能重复添加
            k_ = self.__left_separator + k.replace(self.__left_separator, '').replace(
                self.__right_separator,  '') + self.__right_separator
            if not final_expression.find(k) == -1:
                if isinstance(v, (int, float)):
                    v = str(v)
                elif isinstance(v, str):
                    v = v.replace('"', '\\"')
                    v = '"' + v + '"'
                elif isinstance(v, datetime.datetime):
                    try:
                        datetime.datetime.strptime(str(v), '%Y-%m-%d %H:%M:%S.%f')
                        v = "datetime.datetime.strptime('{}', '%Y-%m-%d %H:%M:%S.%f')".format(v)
                    except ValueError:
                        v = "datetime.datetime.strptime('{}', '%Y-%m-%d %H:%M:%S')".format(v)
                elif isinstance(v, (tuple, list, dict)):
                    v = k
                else:
                    raise ValueError('Variables\' value should be str, int, float, bool or datatime class')
                final_expression = final_expression.replace(k_, v)
        return final_expression

    def get_eval_result(self):
        success = False
        final_expression = self.__eval_expression
        success_ = False
        try:
            success_, eval_result = self.check_eval_expression()
        except Exception as e:
            eval_result = e
            self.logger.error('Check eval expression error')
            if self.logger.level < 10:
                raise
        if success_:
            try:
                final_expression = self.get_final_expression()
            except Exception as e:
                eval_result = e
                self.logger.error('Get final expression error')
                if self.logger.level < 10:
                    raise
            else:
                self.logger.debug('Final expression:{}'.format(final_expression))
                try:
                    if self.__variable_dict:
                        eval_result = eval(final_expression, None, self.__variable_dict)
                    else:
                        eval_result = eval(final_expression)
                    success = True
                except Exception as e:
                    eval_result = e
                    self.logger.error('Eval error')
                    if self.logger.level < 10:
                        raise
        return success, eval_result, final_expression
