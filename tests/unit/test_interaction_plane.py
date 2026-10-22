import pytest
from pydantic import ValidationError

from collaborative_hill.experiments.scenario import InteractionPlane


def test_messages_communication_is_rejected_until_implemented() -> None:
    with pytest.raises(ValidationError, match="not implemented"):
        InteractionPlane(structure="commons", communication="messages")


def test_no_communication_is_the_accepted_default() -> None:
    assert InteractionPlane(structure="commons").communication == "none"
