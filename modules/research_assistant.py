from __future__ import annotations
import os
import time
import json
import asyncio
import logging
import re
from typing import List, Dict, Any

from .config import LoopConfig, SourceDoc
from .faiss_index import SemanticMemory
from .semantic_rank import rank_sources
from .loop_memory import LoopMemory
from .report_view import generate_html_report
from .llm_engines import OpenAIEngine
from .search_clients import SerpAPISearch
from .extractors import TrafilaturaExtractor
from .social_clients import TwitterExtractor

"""Integrated Next-Gen Research Assistant
Includes: FAISS Memory, Semantic Ranking, Loop Memory, HTML Report Generation
"""

class ResearchAssistant:
    def __init__(self,
                 llm,
                 search_client,
                 extractor,
                 social_client=None,
                 config=None,
                 memory_layer=None,
                 loop_logger=None,
                 ranker=None,
                 reporter=None):
        self.llm = llm
        self.search = search_client
        self.extract = extractor
        self.social = social_client
        self.cfg = config or LoopConfig()
        self.memory = memory_layer
        self.loop_memory = loop_logger or LoopMemory()
        self.ranker = ranker
        self.reporter = reporter
        self.logger = logging.getLogger("ResearchAssistant")

    async def run(self, query: str) -> Dict[str, Any]:
        """Run the research loop on a query. Returns a dict with answer, sources, etc."""
        start_ts = time.time()
        context: List[SourceDoc] = []
        analysis_log: List[str] = []
        confidence = 0.0

        for loop in range(1, self.cfg.max_loops + 1):
            self.logger.info("Loop %d/%d …", loop, self.cfg.max_loops)
            next_action, conf = await self._decide_next_step(query, context)
            analysis_log.append(f"<Loop {loop}> {next_action} (conf={conf:.2%})")
            confidence = conf

            # If confident enough or LLM decides to answer, stop looping
            if confidence >= self.cfg.confidence_threshold or next_action.lower().startswith("answer"):
                if confidence >= self.cfg.confidence_threshold:
                    self.logger.info("Confidence %.2f >= threshold %.2f; stopping.",
                                     confidence, self.cfg.confidence_threshold)
                else:
                    self.logger.info("Assistant decided to provide final answer.")
                break

            # Otherwise, treat the next_action as a new search query
            search_query = next_action
            self.logger.info("Searching for: %s", search_query)
            results = await self.search.search(search_query, num_results=5)
            docs = await self._gather_content(results)
            context.extend(docs)

            # Optional: fetch social media posts (e.g., tweets) for sentiment
            social_docs = []
            if self.social:
                social_posts = await self.social.fetch_posts(search_query, limit=25)
                social_docs = [
                    SourceDoc(
                        source="twitter.com",
                        title=f"Tweet by {post.get('author_id')}",
                        url=f"https://twitter.com/i/web/status/{post.get('id')}",
                        content=post.get("text", "")
                    )
                    for post in social_posts
                ]
                context.extend(social_docs)

            # Add new information to semantic memory
            if self.memory:
                new_entries = docs + social_docs
                if new_entries:
                    self.memory.add([d.content for d in new_entries],
                                    [d.title for d in new_entries])

        # After exiting the loop, synthesize the final answer
        ordered_context = context
        if self.ranker:
            ranked_list = self.ranker(query, context)
            ordered_context = [doc for doc, _ in ranked_list]
        answer = await self._synthesize_answer(query, ordered_context)
        self.logger.info("Finished in %.1fs with %d sources.", time.time() - start_ts, len(context))

        result = {
            "query": query,
            "answer": answer,
            "sources": [doc.dict(exclude={"content"}) for doc in ordered_context],
            "analysis_log": analysis_log,
            "confidence": confidence
        }
        # Generate an HTML report if a reporter function is provided
        result["report"] = self.reporter({
            "answer": answer,
            "sources": result["sources"],
            "analysis_log": analysis_log
        }) if self.reporter else None

        # Log the run to loop memory (with timestamp and final confidence)
        self.loop_memory.append({
            "query": query,
            "timestamp": time.time(),
            "confidence": confidence
        })
        return result

    async def _decide_next_step(self, query: str, context: List[SourceDoc]) -> tuple[str, float]:
        """Use LLM to decide the next action (search query or final answer)."""
        sys_prompt = (
            "You are an expert researcher with rigorous methodology. "
            "Given the question and current sources, decide either:\n"
            "1. 'answer' if there is now enough information; or\n"
            "2. 'search: <new query>' if more information is needed.\n\n"
            "Output MUST be JSON with fields {'action': str, 'confidence': float}. "
            "confidence is your certainty in having enough data to answer (0-1)."
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"QUESTION: {query}"},
            {"role": "user", "content": f"CURRENT_SOURCES: {self._brief_sources(context)}"}
        ]
        response = await self.llm.chat(messages)
        try:
            data = json.loads(response)
            action = data["action"]
            confidence = float(data["confidence"])
        except Exception:
            # If parsing fails, default to doing another search with the original query
            action = f"search: {query}"
            confidence = 0.0
        if action.lower().startswith("search"):
            action = action.split("search:", 1)[1].strip()
        return action, confidence

    @staticmethod
    def _brief_sources(ctx: List[SourceDoc], k: int = 3) -> str:
        """Return a brief bullet list of the last k source titles in context."""
        return "\n".join(f"- {d.title} [{d.source}]" for d in ctx[-k:])

    async def _gather_content(self, raw_results: List[Dict[str, Any]]) -> List[SourceDoc]:
        """Fetch and clean content for all search results in parallel."""
        tasks = []
        for item in raw_results:
            url = item.get("link") or item.get("url")
            title = item.get("title") or (url or "")
            if not url:
                continue
            # Domain whitelisting/blacklisting
            if self.cfg.whitelist_domains and not any(
                url.endswith(d) or d in url for d in self.cfg.whitelist_domains
            ):
                continue
            if self.cfg.blacklist_domains and any(
                url.endswith(d) or d in url for d in self.cfg.blacklist_domains
            ):
                continue
            tasks.append(self._extract_single(url, title))
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def _extract_single(self, url: str, title: str) -> SourceDoc:
        """Download and extract text from a single URL, with retries."""
        for attempt in range(3):
            try:
                content = await self.extract.extract(url)
                return SourceDoc(source=self._domain(url), title=title, url=url, content=content)
            except Exception as e:
                await asyncio.sleep(1.5 * (attempt + 1))
                self.logger.warning("Retrying %s (%s)", url, e)
        # If extraction fails after retries:
        return SourceDoc(source=self._domain(url), title=title, url=url, content="(failed to extract)")

    @staticmethod
    def _domain(url: str) -> str:
        """Extract the domain name from a URL for use as source identifier."""
        return re.sub(r"https?://([^/]+)/?.*", r"\1", url)

    async def _synthesize_answer(self, query: str, ctx: List[SourceDoc]) -> str:
        """Use the LLM to synthesize a final answer with citations given the context."""
        # Prepare citation mappings
        cit_fmt = lambda d, i: f"[{i+1} – {d.source}]"
        citations = {id_: cit_fmt(d, i) for i, (id_, d) in enumerate(zip(range(len(ctx)), ctx))}
        prompt = (
            "You are writing a well‑sourced research brief for a policymaker.\n"
            "INSTRUCTIONS:\n"
            "• Use plain, professional language.\n"
            "• When asserting a fact, cite like this: (see {citation}) using the citation map given.\n"
            "• Summarize social sentiment if available.\n"
            "• Output 16 paragraphs."
        )
        citation_map = "\n".join(f"{v}: {ctx[i].title} – {ctx[i].url}"
                                 for i, v in enumerate(citations.values()))
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"QUESTION: {query}"},
            {"role": "user", "content": f"CITATION_MAP:\n{citation_map}"},
            {"role": "user", "content": f"SOURCES:\n{self._prepare_chunks(ctx)}"}
        ]
        answer = await self.llm.chat(messages)
        # Optional hallucination guard: have the model critique its own answer
        if self.cfg.enable_hallucination_guard:
            guard_msg = [
                {"role": "system", "content": (
                    "You are a critic looking for hallucinations. "
                    "Does the answer below cite facts that aren't in the sources? "
                    "Respond ONLY 'ok' if safe, otherwise 'revise'."
                )},
                {"role": "user", "content": answer},
                {"role": "user", "content": "\n\nSOURCES:\n" + self._prepare_chunks(ctx)}
            ]
            verdict = await self.llm.chat(guard_msg)
            if "revise" in verdict.lower():
                answer += "\n\n⚠️ Model self‑flagged potential unverifiable statements."
        return answer

    @staticmethod
    def _prepare_chunks(ctx: List[SourceDoc], max_chars: int = 18000) -> str:
        """Join source contents until reaching a character limit (to avoid overflow)."""
        text_chunks = []
        total = 0
        for doc in ctx:
            chunk = f"\n⎯⎯ {doc.title} ({doc.url}) ⎯⎯\n{doc.content[:2000]}"
            total += len(chunk)
            if total > max_chars:
                break
            text_chunks.append(chunk)
        return "\n".join(text_chunks)

def build_your_assistant():
    """Factory to build a ResearchAssistant with all components."""
    # Initialize persistent memory and loop logger
    memory = SemanticMemory()
    loop_log = LoopMemory()
    # Build the research assistant with configured components
    assistant = ResearchAssistant(
        llm=OpenAIEngine(model="gpt-4o-mini", temperature=0.6, timeout=30.0),
        search_client=SerpAPISearch(os.environ["SERPAPI_API_KEY"]),
        extractor=TrafilaturaExtractor(),
        social_client=TwitterExtractor(os.getenv("TWITTER_BEARER_TOKEN", "")) if os.getenv("TWITTER_BEARER_TOKEN") else None,
        config=LoopConfig(),
        memory_layer=memory,
        loop_logger=loop_log,
        ranker=rank_sources,
        reporter=generate_html_report
    )
    return assistant


def gather_info(topic: str) -> str:
    """Run the research assistant on ``topic`` and return the answer text."""
    assistant = build_your_assistant()
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(assistant.run(topic))
    finally:
        loop.close()
    return result.get("answer", "")

# CLI Entrypoint for direct execution
async def _amain(question: str):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
    assistant = build_your_assistant()
    result = await assistant.run(question)
    print("\n============= FINAL ANSWER =============")
    print(result["answer"])
    print("\n============= SOURCES ==================")
    for i, s in enumerate(result["sources"], 1):
        print(f"[{i}] {s['title']} – {s['url']}")
    # Write HTML report to file if available
    if result.get("report"):
        with open("report.html", "w") as f:
            f.write(result["report"])
        print("\n📄 Full HTML report written to report.html")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run the AI Research Assistant")
    parser.add_argument("question", type=str, help="The research question to answer")
    args = parser.parse_args()
    asyncio.run(_amain(args.question))

if __name__ == "__main__":
    main()
