import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.services.agent_team.consensus_service import ConsensusService
from app.models.consensus_session import ConsensusSession
from app.models.consensus_session import ConsensusVote

@pytest.mark.asyncio
async def test_create_session(test_db_session):
    service = ConsensusService(test_db_session)
    session = await service.create_session(
        conversation_id=uuid4(),
        topic="Test Topic",
        created_by="agent1",
        quorum_type="majority",
        required_voters=["agent1", "agent2"]
    )
    assert session.id is not None
    assert session.topic == "Test Topic"
    assert session.status == "open"

@pytest.mark.asyncio
async def test_cast_vote(test_db_session):
    service = ConsensusService(test_db_session)
    conv_id = uuid4()
    session = await service.create_session(
        conversation_id=conv_id,
        topic="Test Topic",
        created_by="agent1",
        quorum_type="majority",
        required_voters=["agent1", "agent2", "agent3"]
    )
    
    await service.cast_vote(conv_id, "agent1", "approve", "Reason")
    await service.cast_vote(conv_id, "agent2", "approve", "Reason 2")
    
    result = await service.cast_vote(conv_id, "agent3", "reject", "Reason 3")
    assert result["status"] == "decided"
    assert result["result"]["decision"] == "approve"

@pytest.mark.asyncio
async def test_timeout_expired_sessions(test_db_session):
    service = ConsensusService(test_db_session)
    conv_id = uuid4()
    
    # Create an already expired session (or we can just manipulate the expires_at field)
    session = await service.create_session(
        conversation_id=conv_id,
        topic="Test Expired",
        created_by="agent1",
        required_voters=["agent1", "agent2"]
    )
    
    # Manually set expires_at to the past
    session.expires_at = datetime.utcnow()
    test_db_session.add(session)
    await test_db_session.commit()
    
    # Run timeout task
    count = await service.timeout_expired_sessions()
    
    assert count == 1
    # Refresh and check status
    await test_db_session.refresh(session)
    assert session.status == "expired"
