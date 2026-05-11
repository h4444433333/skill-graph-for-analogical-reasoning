from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def load_graph_engine():
    try:
        from auto_grap_skill.core import GraphSkillEngine
        return GraphSkillEngine
    except ImportError:
        repo_src = Path(__file__).resolve().parent / "src"
        if repo_src.exists():
            sys.path.insert(0, str(repo_src))
            from auto_grap_skill.core import GraphSkillEngine
            return GraphSkillEngine
        raise


GraphSkillEngine = load_graph_engine()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Example GitHub entrypoint: build/load a skill graph, run query, and optionally call an OpenAI-compatible LLM."
    )
    parser.add_argument("task", help="The end-user task or question.")
    parser.add_argument(
        "--skills-source",
        action="append",
        default=[],
        help="Directory containing SKILL.md folders. Repeat to add multiple sources.",
    )
    parser.add_argument(
        "--graph-dir",
        default=".grap-skill",
        help="Directory that stores graph.json. If graph.json is missing, the script will build it here.",
    )
    parser.add_argument(
        "--rebuild-graph",
        action="store_true",
        help="Force rebuilding graph.json from --skills-source even if a saved graph already exists.",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Only print selected skills and the prepared prompt context without calling an LLM.",
    )
    parser.add_argument(
        "--show-query-json",
        action="store_true",
        help="Print the raw query JSON before any LLM call.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="HTTP timeout in seconds when calling the LLM endpoint.",
    )
    return parser.parse_args()


def ensure_graph(skill_sources: list[str], graph_dir: str, rebuild: bool):
    graph_dir_path = Path(graph_dir).expanduser().resolve()
    graph_path = graph_dir_path / "graph.json"

    if graph_path.exists() and not rebuild:
        engine = GraphSkillEngine.load(graph_path)
        return engine, graph_path, False

    if not skill_sources:
        raise SystemExit(
            "graph.json does not exist yet. Provide at least one --skills-source so the script can build the graph first."
        )

    sources = [Path(item).expanduser().resolve() for item in skill_sources]
    engine = GraphSkillEngine.build_from_sources(sources)
    graph_path = engine.save(graph_dir_path)
    return engine, graph_path, True


def format_skill_block(title: str, items: list[dict], *, limit: int | None = None) -> str:
    if limit is not None:
        items = items[:limit]
    if not items:
        return f"{title}:\n- none"

    lines = [f"{title}:"]
    for item in items:
        description = item.get("description", "").strip()
        reason = item.get("selection_reason")
        lines.append(f"- {item['name']} ({item['id']})")
        if description:
            lines.append(f"  description: {description}")
        if "score" in item:
            lines.append(f"  score: {item['score']}")
        if "support_score" in item:
            lines.append(f"  support_score: {item['support_score']}")
        if reason:
            lines.append(f"  why_supporting: {reason}")
    return "\n".join(lines)


def build_prompt_bundle(task: str, result: dict, graph_path: Path) -> tuple[str, str]:
    primary = result["primary_skill"]
    supporting = result.get("supporting_skills", [])
    fallback = result.get("fallback_skills", [])
    similar = result.get("similar_skills", [])

    system_prompt = (
        "You are an assistant that must answer using retrieved skill context.\n"
        "Treat the primary skill as the execution center.\n"
        "Use supporting skills only when they add non-redundant value.\n"
        "Do not blindly merge fallback or similar skills into the main answer.\n"
        "If the retrieved skills do not fully solve the task, say what is still missing."
    )

    user_prompt = "\n\n".join(
        [
            f"User task:\n{task}",
            f"Graph source:\n{graph_path}",
            format_skill_block("Primary skill", [primary], limit=1),
            format_skill_block("Supporting skills", supporting, limit=3),
            format_skill_block("Fallback skills", fallback, limit=2),
            format_skill_block("Similar skills", similar, limit=3),
            (
                "Instruction:\n"
                "Answer the user's task. Let the primary skill lead the workflow. "
                "Use supporting skills only as complementary context."
            ),
        ]
    )
    return system_prompt, user_prompt


def print_selection_summary(result: dict, graph_path: Path, rebuilt: bool) -> None:
    print("=== Graph ===")
    print(f"graph_path: {graph_path}")
    print(f"graph_action: {'rebuilt' if rebuilt else 'loaded'}")
    print()
    print("=== Retrieval ===")
    print(f"status: {result['status']}")
    primary = result.get("primary_skill")
    if primary:
        print(f"primary_skill: {primary['name']} ({primary['id']})")
    supporting = ", ".join(item["name"] for item in result.get("supporting_skills", [])) or "none"
    fallback = ", ".join(item["name"] for item in result.get("fallback_skills", [])) or "none"
    similar = ", ".join(item["name"] for item in result.get("similar_skills", [])) or "none"
    print(f"supporting_skills: {supporting}")
    print(f"fallback_skills: {fallback}")
    print(f"similar_skills: {similar}")
    print()


def llm_settings() -> dict[str, str]:
    return {
        "base_url": os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/"),
        "model": os.getenv("LLM_MODEL", "").strip(),
        "api_key": os.getenv("LLM_API_KEY", "").strip(),
    }


def call_openai_compatible(system_prompt: str, user_prompt: str, *, timeout: int) -> str:
    settings = llm_settings()
    if not settings["model"]:
        raise RuntimeError(
            "No LLM model configured. Set LLM_MODEL and optionally LLM_BASE_URL / LLM_API_KEY before using main.py."
        )

    payload = {
        "model": settings["model"],
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if settings["api_key"]:
        headers["Authorization"] = f"Bearer {settings['api_key']}"

    request = urllib.request.Request(
        f"{settings['base_url']}/chat/completions",
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM request failed with HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc

    message = body["choices"][0]["message"]["content"]
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        chunks = []
        for item in message:
            if isinstance(item, dict) and item.get("type") == "text":
                chunks.append(item.get("text", ""))
        return "".join(chunks)
    return str(message)


def main() -> int:
    args = parse_args()
    engine, graph_path, rebuilt = ensure_graph(args.skills_source, args.graph_dir, args.rebuild_graph)
    result = engine.query(args.task)

    if args.show_query_json:
        print("=== Query JSON ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()

    if result["status"] != "ok":
        print_selection_summary(result, graph_path, rebuilt)
        print("The query did not resolve to a single primary skill.")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1

    print_selection_summary(result, graph_path, rebuilt)
    system_prompt, user_prompt = build_prompt_bundle(args.task, result, graph_path)

    if args.skip_llm:
        print("=== Prepared Prompt Context ===")
        print(user_prompt)
        return 0

    settings = llm_settings()
    if not settings["model"]:
        print("No LLM is configured for main.py.")
        print("This repository's build/query commands work locally without a model.")
        print("To run end-to-end QA from main.py, configure an OpenAI-compatible endpoint first.")
        print("Suggested local example:")
        print("  export LLM_BASE_URL=http://127.0.0.1:11434/v1")
        print("  export LLM_MODEL=qwen2.5:7b-instruct")
        print("Optional if your endpoint requires auth:")
        print("  export LLM_API_KEY=your_api_key")
        print()
        print("=== Prepared Prompt Context ===")
        print(user_prompt)
        return 0

    answer = call_openai_compatible(system_prompt, user_prompt, timeout=args.timeout)
    print("=== LLM Answer ===")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
