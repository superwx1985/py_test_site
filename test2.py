import re
import datetime
from py_test.vic_tools import vic_eval
from py_test.general import vic_variables

other_data = '\'123\''
variables = vic_variables.Variables()
variables.set_variable('x', 123)

eo = vic_eval.EvalObject(other_data, vic_variables.get_variable_dict(variables))
eval_success, eval_result, final_expression = eo.get_eval_result()

print(eval_success)
print(eval_result)
print(final_expression)
