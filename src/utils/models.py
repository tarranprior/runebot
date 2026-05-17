from dataclasses import dataclass


@dataclass
class DefaultAccount:
    account_id: int
    username: str
    account_type: str
