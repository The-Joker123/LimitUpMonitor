from fastapi import APIRouter
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time

router = APIRouter(prefix="/api/claude-code", tags=["claude-code"])

HN_API = "https://hn.algolia.com/api/v1/search"
CACHE = {}
CACHE_TTL = 1800


def get_cache(key):
    if key in CACHE:
        data, timestamp = CACHE[key]
        if time.time() - timestamp < CACHE_TTL:
            return data
    return None


def set_cache(key, data):
    CACHE[key] = (data, time.time())


@router.get("/updates")
async def get_official_updates():
    cached = get_cache("official_updates")
    if cached:
        return {"data": cached}

    updates = [
        {
            "version": "v2.1.126",
            "date": "2026-05-01",
            "highlights": "/model picker lists models from gateway's /v1/models endpoint. Added claude project purge command.",
        },
        {
            "version": "v2.1.123",
            "date": "2026-04-29",
            "highlights": "Fixed OAuth authentication failing with a 401 retry loop when CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1 is set.",
        },
        {
            "version": "v2.1.122",
            "date": "2026-04-28",
            "highlights": "Added ANTHROPIC_BEDROCK_SERVICE_TIER env var to select Bedrock service tier (default, flex, or priority).",
        },
        {
            "version": "v2.1.121",
            "date": "2026-04-28",
            "highlights": "Added alwaysLoad option to MCP server config. Added claude plugin prune command.",
        },
        {
            "version": "v2.1.119",
            "date": "2026-04-23",
            "highlights": "/config settings now persist to ~/.claude/settings.json. Added prUrlTemplate for custom PR URLs.",
        },
        {
            "version": "v2.1.118",
            "date": "2026-04-23",
            "highlights": "Added vim visual mode (v) and visual-line mode (V). Merged /cost and /stats into /usage.",
        },
        {
            "version": "v2.1.117",
            "date": "2026-04-22",
            "highlights": "Forked subagents can be enabled on external builds via CLAUDE_CODE_FORK_SUBAGENT=1. Agent frontmatter mcpServers support.",
        },
        {
            "version": "v2.1.116",
            "date": "2026-04-20",
            "highlights": "/resume on large sessions is up to 67% faster. Faster MCP startup with multi-server configs.",
        },
        {
            "version": "v2.1.114",
            "date": "2026-04-18",
            "highlights": "Fixed a crash in the permission dialog when an agent teams teammate requested tool permission.",
        },
        {
            "version": "v2.1.113",
            "date": "2026-04-17",
            "highlights": "CLI spawns native Claude Code binary instead of bundled JavaScript. Added sandbox.network.deniedDomains setting.",
        },
        {
            "version": "v2.1.112",
            "date": "2026-04-16",
            "highlights": "Fixed 'claude-opus-4-7 is temporarily unavailable' for auto mode.",
        },
        {
            "version": "v2.1.111",
            "date": "2026-04-16",
            "highlights": "Claude Opus 4.7 xhigh available! Use /effort to tune speed vs. intelligence. Auto mode for Max subscribers.",
        },
        {
            "version": "v2.1.110",
            "date": "2026-04-15",
            "highlights": "Added /tui command for flicker-free rendering. Changed Ctrl+O to toggle normal and verbose output.",
        },
        {
            "version": "v2.1.109",
            "date": "2026-04-15",
            "highlights": "Improved the extended-thinking indicator with a rotating progress hint.",
        },
        {
            "version": "v2.1.108",
            "date": "2026-04-14",
            "highlights": "Added ENABLE_PROMPT_CACHING_1H env var to opt into 1-hour prompt cache TTL on API key, Bedrock, Vertex, and Foundry.",
        },
        {
            "version": "v2.1.107",
            "date": "2026-04-14",
            "highlights": "Show thinking hints sooner during long operations.",
        },
        {
            "version": "v2.1.105",
            "date": "2026-04-13",
            "highlights": "Added path parameter to EnterWorktree tool. Added PreCompact hook support.",
        },
        {
            "version": "v2.1.101",
            "date": "2026-04-10",
            "highlights": "/team-onboarding command generates teammate ramp-up guide from local usage. OS CA certificate store trust by default.",
        },
        {
            "version": "v2.1.98",
            "date": "2026-04-09",
            "highlights": "Interactive Google Vertex AI setup wizard. Perforce mode support. Monitor tool for streaming events from background scripts.",
        },
        {
            "version": "v2.1.97",
            "date": "2026-04-08",
            "highlights": "Thinking summaries disabled by default. Added showThinkingSummaries setting to restore.",
        },
        {
            "version": "v2.1.81",
            "date": "2026-03-15",
            "highlights": "Added --bare flag for scripted -p calls that skips hooks, LSP, plugin sync, and skill directory walks.",
        },
        {
            "version": "v2.1.70",
            "date": "2026-03-07",
            "highlights": "Third-party API proxy fixes. Windows stability improvements. VS Code session management enhancements.",
        },
        {
            "version": "v2.1.68",
            "date": "2026-03-05",
            "highlights": "Memory leak fixes. Resume and plugin fixes.",
        },
        {
            "version": "v2.1.63",
            "date": "2026-02-23",
            "highlights": "New slash commands. HTTP hooks. Worktree config sharing. Memory leak fixes.",
        },
        {
            "version": "v2.1.50",
            "date": "2026-02-20",
            "highlights": "Improved memory usage during long sessions. 1M context toggle with CLAUDE_CODE_DISABLE_1M_CONTEXT.",
        },
        {
            "version": "v2.1.47",
            "date": "2026-02-18",
            "highlights": "FileWriteTool trailing blank line fix. Windows terminal rendering fixes. Background agent control with Ctrl+F.",
        },
        {
            "version": "v2.1.20",
            "date": "2026-01-27",
            "highlights": "Improved agent task error recovery. Fixed permission prompt display.",
        },
        {
            "version": "v2.0.71",
            "date": "2025-12-31",
            "highlights": "Enhanced bash autocomplete suggestions. Fixed MCP tool discovery.",
        },
        {
            "version": "v2.0.68",
            "date": "2025-12-28",
            "highlights": "Claude Code for Desktop released. UTM SE support for iPhone. Team Metrics feature.",
        },
        {
            "version": "v2.0.0",
            "date": "2025-12-15",
            "highlights": "Native VS Code extension. Thinking toggle with Tab. History search with Ctrl+R. Claude Agent SDK.",
        },
        {
            "version": "v1.0.23",
            "date": "2025-06-15",
            "highlights": "SDK releases - TypeScript SDK and Python SDK available.",
        },
        {
            "version": "v1.0.0",
            "date": "2025-05-01",
            "highlights": "Claude Code generally available. Introducing Sonnet 4 and Opus 4 models.",
        },
    ]

    set_cache("official_updates", updates)
    return {"data": updates}


@router.get("/hacker-news")
async def get_hacker_news():
    cached = get_cache("hn_claude")
    if cached:
        return {"data": cached}

    try:
        params = {
            "query": "Claude Code",
            "tags": "story",
            "hitsPerPage": 15,
            "numericFilters": "created_at_i > " + str(int(time.time()) - 604800),
        }
        response = requests.get(HN_API, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()

        articles = []
        for hit in result.get("hits", []):
            title = hit.get("title", "")
            if not title:
                continue

            if not re.search(r"claude|anthropic", title, re.I):
                continue

            articles.append(
                {
                    "title": title,
                    "url": hit.get(
                        "url",
                        f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    ),
                    "score": hit.get("points", 0),
                    "comments": hit.get("num_comments", 0),
                    "author": hit.get("author", ""),
                    "time": hit.get("created_at", "")[:10],
                }
            )

        if not articles:
            params["numericFilters"] = ""
            params["query"] = "Anthropic Claude AI coding"
            response = requests.get(HN_API, params=params, timeout=10)
            result = response.json()
            for hit in result.get("hits", [])[:10]:
                articles.append(
                    {
                        "title": hit.get("title", ""),
                        "url": hit.get("url", ""),
                        "score": hit.get("points", 0),
                        "comments": hit.get("num_comments", 0),
                        "author": hit.get("author", ""),
                        "time": hit.get("created_at", "")[:10],
                    }
                )

        set_cache("hn_claude", articles)
        return {"data": articles}

    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/status")
async def get_status():
    return {
        "data": {
            "cache_entries": len(CACHE),
            "cache_ttl_seconds": CACHE_TTL,
            "last_check": datetime.now().isoformat(),
        }
    }
