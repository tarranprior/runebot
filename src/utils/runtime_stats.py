#! /usr/bin/env python3

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from version import VERSION


@dataclass
class CommunityStats:
    servers: int
    channels: int
    users: int
    uptime_seconds: int


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def get_community_stats(bot, started_at_utc: Optional[datetime]) -> CommunityStats:
    total_users = 0
    total_channels = 0

    for guild in bot.guilds:
        total_users += guild.member_count or 0
        total_channels += len(guild.channels)

    uptime_seconds = 0
    if started_at_utc is not None:
        now_utc = datetime.now(timezone.utc)
        uptime_seconds = max(0, int((now_utc - started_at_utc).total_seconds()))

    return CommunityStats(
        servers=len(bot.guilds),
        channels=total_channels,
        users=total_users,
        uptime_seconds=uptime_seconds
    )


def build_community_stats_payload(bot, started_at_utc: Optional[datetime]) -> dict:
    stats = get_community_stats(bot, started_at_utc)

    return {
        'generatedAt': utc_now_iso(),
        'stats': {
            'servers': stats.servers,
            'channels': stats.channels,
            'users': stats.users,
            'uptimeSeconds': stats.uptime_seconds
        },
        'meta': {
            'source': 'runebot-runtime',
            'version': VERSION
        }
    }
