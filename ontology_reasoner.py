"""
OWL 온톨로지 기반 에이전트 추론기.

agent_ontology.ttl 을 로드하여 도구 능력, 루프 단계 유효성,
모델 토큰 한도 등을 SPARQL 쿼리로 조회한다.
기존 tools.py 함수들과 병행 사용 가능하며 추가 의존성 없음(rdflib만 필요).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from rdflib import XSD, Graph, Literal, Namespace, RDF, RDFS
from rdflib.plugins.sparql import prepareQuery

AG = Namespace("http://antigravity.local/agent#")

# 온톨로지 파일 탐색 (같은 폴더 우선, 이후 상위 폴더)
_self = Path(__file__).resolve()
_ONTOLOGY_CANDIDATES = [
    _self.parent / "agent_ontology.ttl",                 # 같은 폴더
    Path(os.getcwd()) / "agent_ontology.ttl",            # 실행 위치
    *[_self.parents[i] / "agent_ontology.ttl" for i in range(1, min(7, len(_self.parents)))],
]


def _find_ontology() -> Path:
    for path in _ONTOLOGY_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError(
        "agent_ontology.ttl 을 찾을 수 없습니다. "
        f"탐색 경로: {[str(p) for p in _ONTOLOGY_CANDIDATES]}"
    )


@lru_cache(maxsize=1)
def _load_graph() -> Graph:
    g = Graph()
    g.parse(str(_find_ontology()), format="turtle")
    return g


# ── 미리 컴파일한 SPARQL 쿼리 ──────────────────────────────────────────────

_Q_TOOL_CAPS = prepareQuery(
    """
    SELECT ?cap WHERE {
        ?tool rdfs:label ?label ;
              ag:providesCapability ?cap .
    }
    """,
    initNs={"ag": AG, "rdfs": RDFS},
)

_Q_TOOL_META = prepareQuery(
    """
    SELECT ?desc ?pub ?needsKey ?fallback ?imgUrl WHERE {
        ?tool rdfs:label ?label .
        OPTIONAL { ?tool ag:toolDescription ?desc }
        OPTIONAL { ?tool ag:publicDescription ?pub }
        OPTIONAL { ?tool ag:requiresApiKey ?needsKey }
        OPTIONAL { ?tool ag:fallbackTo ?fb .
                   ?fb rdfs:label ?fallback }
        OPTIONAL { ?tool ag:imageUrl ?imgUrl }
    }
    """,
    initNs={"ag": AG, "rdfs": RDFS},
)

_Q_STEP_TOOLS = prepareQuery(
    """
    SELECT ?toolLabel WHERE {
        ?step rdfs:label ?stepLabel ;
              ag:usesTool ?tool .
        ?tool rdfs:label ?toolLabel .
    }
    """,
    initNs={"ag": AG, "rdfs": RDFS},
)

_Q_STEP_CAPS = prepareQuery(
    """
    SELECT ?cap WHERE {
        ?step rdfs:label ?stepLabel ;
              ag:requiresCapability ?cap .
    }
    """,
    initNs={"ag": AG, "rdfs": RDFS},
)

_Q_MODEL = prepareQuery(
    """
    SELECT ?maxTokens WHERE {
        ?model a ag:LLMModel ;
               rdfs:label ?modelId ;
               ag:maxTokens ?maxTokens .
    }
    """,
    initNs={"ag": AG, "rdfs": RDFS},
)

_Q_LOOP_ORDER = prepareQuery(
    """
    SELECT ?label ?nextLabel WHERE {
        ?step a ag:LoopStep ;
              rdfs:label ?label .
        OPTIONAL { ?step ag:nextStep ?next .
                   ?next rdfs:label ?nextLabel }
    }
    """,
    initNs={"ag": AG, "rdfs": RDFS},
)

_Q_ALL_TOOLS = prepareQuery(
    """
    SELECT ?label ?isDefault ?needsKey WHERE {
        ?tool ag:isDefault ?isDefault ;
              rdfs:label ?label .
        OPTIONAL { ?tool ag:requiresApiKey ?needsKey }
    }
    """,
    initNs={"ag": AG, "rdfs": RDFS},
)


# ── Public API ──────────────────────────────────────────────────────────────

class AgentOntologyReasoner:
    """
    agent_ontology.ttl 기반 추론기.

    사용 예::

        r = AgentOntologyReasoner()
        caps  = r.get_tool_capabilities("Search")   # ["WebSearch"]
        limit = r.get_model_max_tokens("gpt-4")      # 8000
        tools = r.get_tools_for_step("execute")      # ["Search", "Code", ...]
    """

    def __init__(self) -> None:
        self._g = _load_graph()

    # ── 도구 조회 ──────────────────────────────────────────────────────────

    def get_tool_capabilities(self, tool_label: str) -> List[str]:
        """도구가 제공하는 능력 목록 반환."""
        rows = self._g.query(
            _Q_TOOL_CAPS,
            initBindings={"label": Literal(tool_label)},
        )
        return [str(row.cap).split("#")[-1] for row in rows]

    def get_tool_metadata(self, tool_label: str) -> Dict[str, object]:
        """도구의 설명, API 키 필요 여부, 폴백 도구, 이미지 URL 반환."""
        rows = list(
            self._g.query(
                _Q_TOOL_META,
                initBindings={"label": Literal(tool_label)},
            )
        )
        if not rows:
            return {}
        row = rows[0]
        return {
            "description":        str(row.desc)     if row.desc     else "",
            "public_description": str(row.pub)      if row.pub      else "",
            "requires_api_key":   str(row.needsKey) == "true" if row.needsKey else False,
            "fallback_tool":      str(row.fallback) if row.fallback else None,
            "image_url":          str(row.imgUrl)   if row.imgUrl   else "",
        }

    def requires_api_key(self, tool_label: str) -> bool:
        return bool(self.get_tool_metadata(tool_label).get("requires_api_key"))

    def get_fallback_tool(self, tool_label: str) -> Optional[str]:
        return self.get_tool_metadata(tool_label).get("fallback_tool")  # type: ignore[return-value]

    def get_all_tools(self) -> List[Dict[str, object]]:
        """온톨로지에 등록된 모든 도구와 기본 포함 여부 반환."""
        rows = self._g.query(_Q_ALL_TOOLS)
        return [
            {
                "name":        str(row.label),
                "is_default":  str(row.isDefault) == "true",
                "needs_key":   str(row.needsKey) == "true" if row.needsKey else False,
            }
            for row in rows
        ]

    def get_default_tools(self) -> List[str]:
        """isDefault=true 인 도구 이름 목록."""
        return [t["name"] for t in self.get_all_tools() if t["is_default"]]  # type: ignore[misc]

    # ── 루프 단계 조회 ─────────────────────────────────────────────────────

    def get_tools_for_step(self, step_label: str) -> List[str]:
        """특정 루프 단계에서 사용 가능한 도구 목록."""
        rows = self._g.query(
            _Q_STEP_TOOLS,
            initBindings={"stepLabel": Literal(step_label)},
        )
        return [str(row.toolLabel) for row in rows]

    def get_capabilities_for_step(self, step_label: str) -> List[str]:
        """특정 루프 단계에 필요한 능력 목록."""
        rows = self._g.query(
            _Q_STEP_CAPS,
            initBindings={"stepLabel": Literal(step_label)},
        )
        return [str(row.cap).split("#")[-1] for row in rows]

    def validate_tool_for_step(self, tool_label: str, step_label: str) -> bool:
        """도구가 해당 루프 단계에 등록되어 있는지 확인."""
        return tool_label in self.get_tools_for_step(step_label)

    def get_loop_order(self) -> Dict[str, Optional[str]]:
        """루프 단계 실행 순서를 {현재단계: 다음단계} 딕셔너리로 반환."""
        rows = self._g.query(_Q_LOOP_ORDER)
        return {
            str(row.label): str(row.nextLabel) if row.nextLabel else None
            for row in rows
        }

    # ── 모델 조회 ──────────────────────────────────────────────────────────

    def get_model_max_tokens(self, model_id: str) -> Optional[int]:
        """온톨로지에서 모델의 maxTokens 조회. 없으면 None."""
        rows = list(
            self._g.query(
                _Q_MODEL,
                initBindings={"modelId": Literal(model_id)},
            )
        )
        if not rows:
            return None
        return int(rows[0].maxTokens)

    # ── 능력 기반 도구 추천 ────────────────────────────────────────────────

    def find_tools_by_capability(self, capability: str) -> List[str]:
        """
        특정 능력을 제공하는 도구 이름 목록.
        capability: 'WebSearch' | 'CodeGeneration' | 'ImageGeneration' | ...
        """
        cap_uri = AG[capability]
        tools = []
        for tool in self._g.subjects(AG.providesCapability, cap_uri):
            label = self._g.value(tool, RDFS.label)
            if label:
                tools.append(str(label))
        return tools

    def recommend_tool(self, task_keywords: List[str]) -> str:
        """
        태스크 키워드 기반으로 최적 도구 추천.
        키워드-능력 매핑으로 단순 규칙 추론.
        """
        keyword_map = {
            "search": "WebSearch",
            "find":   "WebSearch",
            "news":   "WebSearch",
            "code":   "CodeGeneration",
            "write":  "CodeGeneration",
            "debug":  "CodeGeneration",
            "image":  "ImageGeneration",
            "draw":   "ImageGeneration",
            "sketch": "ImageGeneration",
        }
        for keyword in task_keywords:
            capability = keyword_map.get(keyword.lower())
            if capability:
                candidates = self.find_tools_by_capability(capability)
                if candidates:
                    return candidates[0]
        return "search"  # 기본값: Search 도구


# ── 편의 함수 ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_reasoner() -> AgentOntologyReasoner:
    """싱글턴 Reasoner 인스턴스 반환."""
    return AgentOntologyReasoner()
