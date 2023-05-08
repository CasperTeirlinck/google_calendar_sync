import json
from unittest import mock
from unittest.mock import ANY

import pytest
from requests.models import Response

from src.api_client.notion import Notion
from src.models.database import Database, DatabaseName, WorkspaceName


@pytest.fixture()
def notion_client() -> Notion:
    notion_client = Notion()
    notion_client.auth_headers = {WorkspaceName("test"): {}}
    return notion_client


@pytest.fixture()
def database() -> Database:
    return Database(
        workspace=WorkspaceName("test"),
        name=DatabaseName("test"),
        id="test",
        calendar_id="test",
        title_property="test",
        date_property="test",
        icon_property="test",
        icon_property_path="test",
        icon_value_mapping="test",
        icon_default="test",
    )


@mock.patch("src.api_client.notion.requests.post")
def test_post_paginated(
    mock_post: mock.Mock,
    notion_client: Notion,
    database: Database,
):
    """
    Test if the post requests to the Notion API handles pagination correctly.
    """

    # Mock api response
    responses = []
    for response_content in [
        {
            "results": ["result_1", "result_2"],
            "next_cursor": "cursor_1",
        },
        {
            "results": ["result_3"],
        },
    ]:
        response = Response()
        response.status_code = 200
        response._content = json.dumps(response_content).encode("ascii")
        responses.append(response)
    mock_post.side_effect = responses

    # Act
    body = {"key": "value"}
    result = list(
        notion_client.post_paginated(
            path="test",
            database=database,
            body=body,
        )
    )

    # Assert
    mock_post.assert_has_calls(
        [
            mock.call(
                ANY,
                json={
                    **body,
                    "page_size": 100,
                },
                params=ANY,
                headers=ANY,
            ),
            mock.call(
                ANY,
                json={
                    **body,
                    "start_cursor": "cursor_1",
                    "page_size": 100,
                },
                params=ANY,
                headers=ANY,
            ),
        ],
    )

    assert result == ["result_3", "result_1", "result_2"]
