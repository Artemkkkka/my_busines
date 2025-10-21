import pytest
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.helpers import _make_user, _make_team
from src.tasks.crud import create_task, create_task_comment
from src.tasks.models import Task, Status
from src.users.models import TeamRole


@pytest.mark.anyio
async def test_create_task_with_assignee_persists_and_sets_all_fields(session: AsyncSession, engine):
    owner = await _make_user(session, "owner@example.com", role=TeamRole.employee)
    team = await _make_team(session, "Team A", owner_id=owner.id)

    author = await _make_user(session, "author@example.com", role=TeamRole.employee, team_id=team.id)
    assignee = await _make_user(session, "assignee@example.com", role=TeamRole.employee, team_id=team.id)

    name = "Fix critical bug"
    description = "Reproduce, write test, patch"
    deadline = datetime(2025, 1, 15, 12, 0, 0)

    task = await create_task(
        session=session,
        team_id=team.id,
        author_id=author.id,
        name=name,
        description=description,
        deadline_at=deadline,
        assignee_id=assignee.id,
    )

    assert isinstance(task, Task)
    assert task.id is not None
    assert task.team_id == team.id
    assert task.author_id == author.id
    assert task.assignee_id == assignee.id
    assert task.name == name
    assert task.description == description
    assert task.deadline_at == deadline
    assert task.status == Status.open

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as s2:
        fresh = await s2.get(Task, task.id)
        assert fresh is not None
        assert fresh.name == name
        assert fresh.status == Status.open
        assert fresh.assignee_id == assignee.id


@pytest.mark.anyio
async def test_create_task_without_assignee(session: AsyncSession, engine):
    owner = await _make_user(session, "owner2@example.com")
    team = await _make_team(session, "Team B", owner_id=owner.id)
    author = await _make_user(session, "author2@example.com", team_id=team.id)

    task = await create_task(
        session=session,
        team_id=team.id,
        author_id=author.id,
        name="Write docs",
        description = "",
        deadline_at=datetime(2025, 2, 1, 18, 0, 0),
    )

    assert task.id is not None
    assert task.team_id == team.id
    assert task.author_id == author.id
    assert task.assignee_id is None
    assert task.description == "" 
    assert task.deadline_at == datetime(2025, 2, 1, 18, 0, 0)
    assert task.status == Status.open

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as s2:
        fresh = await s2.get(Task, task.id)
        assert fresh is not None
        assert fresh.assignee_id is None
        assert fresh.description == ""
        assert fresh.deadline_at == datetime(2025, 2, 1, 18, 0, 0)


@pytest.mark.anyio
async def test_create_task_raises_when_team_not_found(session: AsyncSession):
    author = await _make_user(session, "lonely_author@example.com")

    with pytest.raises(Exception):
        await create_task(
            session=session,
            team_id=999_999,
            author_id=author.id,
            name="Ghost task",
        )


@pytest.mark.anyio
async def test_create_task_raises_when_author_not_found(session: AsyncSession):
    owner = await _make_user(session, "owner3@example.com")
    team = await _make_team(session, "Team C", owner_id=owner.id)

    with pytest.raises(Exception):
        await create_task(
            session=session,
            team_id=team.id,
            author_id=999_999,
            name="No author here",
        )


@pytest.mark.anyio
async def test_create_task_raises_when_assignee_not_found(session: AsyncSession):
    owner = await _make_user(session, "owner4@example.com")
    team = await _make_team(session, "Team D", owner_id=owner.id)
    author = await _make_user(session, "author4@example.com", team_id=team.id)

    with pytest.raises(Exception):
        await create_task(
            session=session,
            team_id=team.id,
            author_id=author.id,
            name="Bad assignee",
            assignee_id=777_777,
        )

@pytest.mark.anyio
async def test_create_task_comment_persists_and_links_to_task(session: AsyncSession, engine):
    owner = await _make_user(session, "owner5@example.com")
    team = await _make_team(session, "Team Comments", owner_id=owner.id)
    author = await _make_user(session, "author5@example.com", team_id=team.id)
    commenter = await _make_user(session, "commenter@example.com", team_id=team.id)

    task = await create_task(
        session=session,
        team_id=team.id,
        author_id=author.id,
        name="Task with comments",
        description="",
        deadline_at=datetime(2025, 5, 1, 9, 0, 0),
    )

    comment = await create_task_comment(
        session=session,
        team_id=team.id,
        task_id=task.id,
        author_id=commenter.id,
        body="Looks good!",
    )

    assert comment.id is not None
    assert comment.task_id == task.id
    assert comment.author_id == commenter.id
    assert comment.body == "Looks good!"