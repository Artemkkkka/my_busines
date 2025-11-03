from datetime import datetime, timedelta, timezone
import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from src.evaluations.crud import TaskEvaluationCRUD
from src.evaluations.models import Evaluation
from src.tasks.models import Status
from src.users.models import TeamRole
from tests.helpers import _make_user, _make_task, _make_team


@pytest.mark.anyio
async def test_get_avg_rating_for_period_filters_by_team_status_and_inclusive_dates(session: AsyncSession):
    owner = await _make_user(session, "owner@example.com", role=TeamRole.admin)
    team_a = await _make_team(session, "A", owner_id=owner.id)
    owner.team_id = team_a.id

    other_owner = await _make_user(session, "other@example.com", role=TeamRole.admin)
    team_b = await _make_team(session, "B", owner_id=other_owner.id)
    other_owner.team_id = team_b.id
    await session.flush()

    base = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    ta1 = await _make_task(session, team_id=team_a.id, author_id=owner.id, status=Status.done)
    ta2 = await _make_task(session, team_id=team_a.id, author_id=owner.id, status=Status.done)
    ta3 = await _make_task(session, team_id=team_a.id, author_id=owner.id, status=next(s for s in Status if s != Status.done))
    tb1 = await _make_task(session, team_id=team_b.id, author_id=other_owner.id, status=Status.done)

    e1 = Evaluation(task_id=ta1.id, value=1, rated_at=base - timedelta(days=2))  # вне окна
    e2 = Evaluation(task_id=ta2.id, value=5, rated_at=base - timedelta(days=1))  # целевой
    e3 = Evaluation(task_id=tb1.id, value=3, rated_at=base - timedelta(days=1))  # другая команда — исключить
    e4 = Evaluation(task_id=ta3.id, value=4, rated_at=base - timedelta(days=1))  # не done — исключить
    session.add_all([e1, e2, e3, e4])
    await session.flush()

    date_from = e2.rated_at
    date_to = e2.rated_at

    avg, cnt = await TaskEvaluationCRUD.get_avg_rating_for_period(session, team_id=team_a.id, date_from=date_from, date_to=date_to)

    assert cnt == 1
    assert avg == pytest.approx(5.0, rel=1e-12)
