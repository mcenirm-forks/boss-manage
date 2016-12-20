import json
from collections import OrderedDict

class Branch(dict):
    def __init__(self, states=None, start=None):
        super().__init__()
        self['States'] = OrderedDict() # Makes states be dumped in the same order they were added

        if type(states) == list:
            for state in states:
                self.addState(state)
        elif type(states) == dict:
            self['States'].update(states)

        if start is not None:
            self.setStart(start)

    def setStart(self, state):
        self['StartAt'] = str(state)

    def addState(self, state):
        self['States'][state.Name] = state


class Machine(Branch):
    def __init__(self, comment="", states=None, start=None):
        super().__init__(states, start)
        self['Comment'] = comment

    def definition(self):
        return json.dumps(self)

class State(dict):
    # DP ???: should catches and retries be only for Tasks??
    def __init__(self, name, type_, next=None, end=None, catches=None, retries=None):
        super().__init__(Type = type_)
        self.Name = name

        if next is not None:
            self['Next'] = str(next)

        if end is not None:
            self['End'] = bool(end)

        if catches is not None:
            if type(catches) != list:
                catches = [catches]
            self['Catches'] = catches

        if retries is not None:
            if type(retries) != list:
                retries = [retries]
            self['Retry'] = retries

    def addCatch(self, catch):
        if 'Catches' not in self:
            self['Catches'] = []
        self['Catches'].add(catch)

    def addRetry(self, retry):
        if 'Retry' not in self:
            self['Retry'] = []
        self['Retry'].add(retry)

    def __str__(self):
        return self.Name

class PassState(State):
    def __init__(self, name, **kwargs):
        super().__init__(name, 'Pass', **kwargs)

class SuccessState(State):
    def __init__(self, name, **kwargs):
        super().__init__(name, 'Success', **kwargs)

class FailState(State):
    def __init__(self, name, error, cause, **kwargs):
        super().__init__(name, 'Fail', **kwargs)
        self['Error'] = error
        self['Cause'] = cause

class TaskState(State):
    def __init__(self, name, resource, **kwargs):
        super().__init__(name, 'Task', **kwargs)
        self['Resource'] = resource

class WaitState(State):
    def __init__(self, name, seconds=None, timestamp=None, timestamp_path=None, seconds_path=None, **kwargs):
        super().__init__(name, 'Wait', **kwargs)

        if seconds is not None:
            self['Seconds'] = int(seconds)

        if timestamp is not None:
            self['Timestamp'] = str(timestamp)

        if timestamp_path is not None:
            self['TimestampPath'] = str(timestamp_path)

        if seconds_path is not None:
            self['SecondsPath'] = str(seconds_path)

class ParallelState(State):
    def __init__(self, name, branches=None, **kwargs):
        super().__init__(name, 'Parallel', **kwargs)

        if branches is None:
            branches = []
        elif type(branches) != list:
            branches = [branches]
        self['Branches'] = branches

    def addBranch(self, branch):
        self['Branches'].add(branch)

class ChoiceState(State):
    def __init__(self, name, choices=None, default=None, **kwargs):
        super().__init__(name, 'Choice', **kwargs)

        if choices is None:
            choices = []
        elif type(choices) != list:
            choices = [choices]
        self['Choices'] = choices

        if default is not None:
            self['Default'] = str(default)

    def addChoice(self, choice):
        self['Choices'].add(choice)

    def setDefault(self, default):
        self['Default'] = str(default)

class Choice(dict):
    def __init__(self, variable, equals, next):
        super().__init__(Variable = variable,
                         NumericEquals = int(equals),
                         Next = str(next))

class Retry(dict):
    def __init__(self, errors, interval, max, backoff):
        if type(errors) != list:
            errors = [errors]

        super().__init__(ErrorEquals = errors,
                         IntervalSeconds = int(interval),
                         MaxAttempts = int(max),
                         BackoffRate = float(backoff))

class Catch(dict):
    def __init__(self, errors, next):
        if type(errors) != list:
            errors = [errors]

        super().__init__(ErrorEquals = errors,
                         Next = str(next))

def Lambda(session, name):
    region = 'us-east-1'
    account = None # DP TODO: lookup account id
    return 'arn:aws:lambda:{}:{}:function:{}'.format(region, account, name)

def Timestamp(datetime):
    pass # DP TODO: format into appropriate format
