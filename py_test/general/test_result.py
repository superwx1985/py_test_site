class CaseResult:
    def __init__(self, id_, name, type_):
        self.id = id_
        self.name = name
        self.type = type_
        self.status = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.step_list = list()
        self.all_step_count = 0
        self.run_step_count = 0
        self.pass_step_count = 0
        self.fail_step_count = 0
        self.error_step_count = 0
        self.skip_step_count = 0
        self.other_step_count = 0
        self.data_dict = dict()

    def add_step_result(self, step_result):
        self.step_list.append(step_result)
        self.all_step_count += 1
        if step_result.status == 'p':
            self.pass_step_count += 1
            self.run_step_count += 1
        elif step_result.status == 'f':
            self.fail_step_count += 1
            self.run_step_count += 1
        elif step_result.status == 'e':
            self.error_step_count += 1
            self.run_step_count += 1
        elif step_result.status == 's':
            self.skip_step_count += 1
        elif step_result.status == 'o':
            self.other_step_count += 1
        if self.error_step_count > 0:
            self.status = 'e'
        elif self.fail_step_count > 0:
            self.status = 'f'
        elif self.pass_step_count > 0:
            self.status = 'p'
        else:
            self.status = 's'


class StepResult:
    def __init__(self, id_, name, status, message, start_time, end_time, data_dict):
        self.id = id_
        self.name = name
        self.status = status
        self.message = message
        self.start_time = start_time
        self.end_time = end_time
        self.data_dict = data_dict
