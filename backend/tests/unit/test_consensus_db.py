import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import select
from app.models.consensus_session import ConsensusSession, ConsensusVote

@pytest.mark.asyncio
async def test_consensus_db_cascading_deletes(test_db_session):
    # Create parent session
    session = ConsensusSession(
        id=uuid4(),
        conversation_id=uuid4(),
        topic="Database Test",
        created_by="agent1",
        quorum_type="majority",
        required_voters=["agent1", "agent2"],
        expires_at=datetime.utcnow()
    )
    test_db_session.add(session)
    await test_db_session.flush()

    # Create associated vote
    vote = ConsensusVote(
        id=uuid4(),
        session_id=session.id,
        agent_id="agent1",
        vote="approve"
    )
    test_db_session.add(vote)
    await test_db_session.commit()

    # Verify they exist
    assert await test_db_session.get(ConsensusSession, session.id) is not None
    assert await test_db_session.get(ConsensusVote, vote.id) is not None

    # Delete parent
    await test_db_session.delete(session)
    await test_db_session.commit()

    # Verify vote was cascaded or we can't find it
    result = await test_db_session.execute(select(ConsensusVote).where(ConsensusVote.id == vote.id))
    assert result.scalar_one_or_none() is None
