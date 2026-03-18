from typing import Tuple, List

import toml
from loguru import logger


def validate_hand_toml(toml_content: str) -> Tuple[bool, List[str]]:
    """Validate a hand.toml configuration string.

    Required structure:
        [hand]
        name = "..."
        version = "..."

    Args:
        toml_content: Raw TOML string to validate.

    Returns:
        A tuple of (is_valid, list_of_error_messages).
    """
    errors: List[str] = []

    try:
        data = toml.loads(toml_content)
    except toml.TomlDecodeError as exc:
        logger.debug("TOML parse error: {}", str(exc))
        return False, [f"Invalid TOML syntax: {exc}"]

    # Check for [hand] section
    if "hand" not in data:
        errors.append("Missing required [hand] section")
    else:
        hand = data["hand"]
        if not isinstance(hand, dict):
            errors.append("[hand] must be a table/section")
        else:
            if "name" not in hand:
                errors.append("Missing required field: hand.name")
            elif not isinstance(hand["name"], str) or not hand["name"].strip():
                errors.append("hand.name must be a non-empty string")

            if "version" not in hand:
                errors.append("Missing required field: hand.version")
            elif not isinstance(hand["version"], str) or not hand["version"].strip():
                errors.append("hand.version must be a non-empty string")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.debug("hand.toml validation failed: {}", errors)
    return is_valid, errors
