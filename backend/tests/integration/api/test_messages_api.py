"""Integration tests for message API endpoints."""

from uuid import uuid4

import pytest
from fastapi import status


class TestMessagesAPI:
    """Test message API endpoints."""

    @pytest.mark.asyncio
    async def test_get_session_messages(self, client, session, message):
        """Test GET /api/v1/sessions/{session_id}/messages."""
        response = await client.get(f"/api/v1/sessions/{session.id}/messages")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_session_messages_not_found(self, client):
        """Test getting messages for non-existent session."""
        response = await client.get(f"/api/v1/sessions/{uuid4()}/messages")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_message_success(self, client, message):
        """Test GET /api/v1/messages/{id}."""
        response = await client.get(f"/api/v1/messages/{message.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(message.id)

    @pytest.mark.asyncio
    async def test_get_message_not_found(self, client):
        """Test getting non-existent message."""
        response = await client.get(f"/api/v1/messages/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_save_message_success(self, client, session):
        """Test POST /api/v1/messages."""
        message_data = {
            "id": str(uuid4()),
            "session_id": str(session.id),
            "role": "user",
            "content": "Test message",
            "sequence": 1,
        }

        response = await client.post(
            "/api/v1/messages",
            json=message_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == "Test message"

    @pytest.mark.asyncio
    async def test_save_batch_messages_success(self, client, session):
        """Test POST /api/v1/messages/batch."""
        messages = [
            {
                "id": str(uuid4()),
                "session_id": str(session.id),
                "role": "user",
                "content": f"Message {i}",
                "sequence": i,
            }
            for i in range(1, 4)
        ]

        response = await client.post(
            "/api/v1/messages/batch",
            json=messages,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_delete_message_success(self, client, message):
        """Test DELETE /api/v1/messages/{id}."""
        response = await client.delete(f"/api/v1/messages/{message.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT
