#TODO сделать более красивую админку, добавить __str__ для моделей
from sqladmin import ModelView

from src.users.models import User
from src.evaluations.models import Evaluation
from src.meetings.models import Meeting
from src.tasks.models import Task, TaskComment
from src.teams.models import Team


class UserAdmin(ModelView, model=User):
    column_list = [User.id]

class EvaluationAdmin(ModelView, model=Evaluation):
    column_list = [Evaluation.id]

class MeetingAdmin(ModelView, model=Meeting):
    column_list = [Meeting.id]

class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id]

class TaskCommentAdmin(ModelView, model=TaskComment):
    column_list = [TaskComment.id]

class TeamAdmin(ModelView, model=Team):
    column_list = [Team.id]