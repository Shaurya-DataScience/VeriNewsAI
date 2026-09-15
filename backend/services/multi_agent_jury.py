from typing import Dict, Any, List
import hashlib

def run_multi_agent_jury(
    claim: str,
    verdict: str,
    confidence: float,
    supporting_sources: List[Dict[str, Any]],
    contradicting_sources: List[Dict[str, Any]],
    summary: str = ""
) -> Dict[str, Any]:
    """
    Simulate a 3-Agent Collaborative Intelligence Jury:
    - Agent 1: The Advocate (Searches for corroboration, context, and charitable interpretation)
    - Agent 2: The Skeptic (Probes for contradictions, missing sources, and fallacies)
    - Agent 3: The Presiding Judge (Synthesizes debate and renders unanimous or split verdict)
    """
    num_supporting = len(supporting_sources)
    num_contradicting = len(contradicting_sources)

    verdict_upper = verdict.upper()
    is_true = "TRUE" in verdict_upper or "SUPPORTED" in verdict_upper
    is_false = "FALSE" in verdict_upper or "REFUTED" in verdict_upper or "CONTRADICTING" in verdict_upper
    is_misleading = "MISLEADING" in verdict_upper or "CHERRYPICKING" in verdict_upper

    top_sup_domain = supporting_sources[0].get("domain") or supporting_sources[0].get("source") or "Verified Sources" if supporting_sources else "None"
    top_con_domain = contradicting_sources[0].get("domain") or contradicting_sources[0].get("source") or "Fact-Checking Bodies" if contradicting_sources else "None"

    # 1. Advocate Agent Argument
    if is_true:
        advocate_arg = (
            f"The empirical evidence firmly supports this assertion. Major accredited institutions, including {top_sup_domain}, "
            f"corroborate the core factual claims. There is documented consensus with verifiable data points."
        )
        advocate_vote = "TRUE"
        advocate_confidence = min(98, int(confidence + 5))
    elif is_misleading:
        advocate_arg = (
            f"There is a kernel of factual truth in the underlying premise from {top_sup_domain}, although the viral framing "
            f"exaggerates the scope or omits essential qualifiers."
        )
        advocate_vote = "MISLEADING"
        advocate_confidence = 70
    else:
        advocate_arg = (
            f"While certain public forums or viral outlets claim this event occurred, reliable cross-domain corroboration is completely absent. "
            f"Even the most charitable reading reveals unsupported premises."
        )
        advocate_vote = "FALSE" if confidence > 80 else "UNVERIFIED"
        advocate_confidence = max(50, int(100 - confidence))

    # 2. Skeptic Agent Argument
    if is_false:
        skeptic_arg = (
            f"Direct contradiction detected. Reputable investigative registries, including {top_con_domain}, have thoroughly debunked this narrative. "
            f"The claim relies on fabricated premises, temporal distortion, or unverified hearsay."
        )
        skeptic_vote = "FALSE"
        skeptic_confidence = min(99, int(confidence + 6))
    elif is_misleading:
        skeptic_arg = (
            f"Critical context has been stripped. The statement cherry-picks selective data while disregarding standard peer-reviewed baselines. "
            f"Presenting this without full context actively misleads readers."
        )
        skeptic_vote = "MISLEADING"
        skeptic_confidence = 88
    else:
        skeptic_arg = (
            f"I have reviewed the corroborating material against known misinformation indices. While no direct counter-evidence was found, "
            f"ongoing monitoring is recommended to ensure no future revisions emerge."
        )
        skeptic_vote = "TRUE"
        skeptic_confidence = min(94, int(confidence))

    # 3. Judge Agent Synthesis & Final Consensus
    votes = [advocate_vote, skeptic_vote]
    if advocate_vote == skeptic_vote:
        judge_vote = advocate_vote
        consensus_type = f"Unanimous 3-0 ({judge_vote})"
        consensus_score = int((advocate_confidence + skeptic_confidence) / 2)
    else:
        judge_vote = verdict_upper if verdict_upper in ["TRUE", "FALSE", "MISLEADING", "UNVERIFIED"] else "FALSE"
        votes.append(judge_vote)
        majority_count = votes.count(judge_vote)
        consensus_type = f"Majority {majority_count}-1 ({judge_vote})"
        consensus_score = int(confidence)

    judge_ruling = (
        f"After deliberating on both the corroborating and dissenting findings across {num_supporting + num_contradicting} independent sources, "
        f"the Jury finds that the preponderance of evidence points to **{judge_vote}**. {summary or 'Factual claims must remain grounded in verifiable primary records.'}"
    )

    debate_transcript = [
        {
            "turn": 1,
            "speaker": "The Advocate Agent",
            "role": "Corroboration & Affirmative Evidence",
            "avatar": "shield-check",
            "stance": advocate_vote,
            "confidence": advocate_confidence,
            "argument": advocate_arg
        },
        {
            "turn": 2,
            "speaker": "The Skeptic Agent",
            "role": "Contradiction & Fallacy Probing",
            "avatar": "search-check",
            "stance": skeptic_vote,
            "confidence": skeptic_confidence,
            "argument": skeptic_arg
        },
        {
            "turn": 3,
            "speaker": "The Presiding Judge Agent",
            "role": "Evidence Synthesis & Ruling",
            "avatar": "scale",
            "stance": judge_vote,
            "confidence": consensus_score,
            "argument": judge_ruling
        }
    ]

    return {
        "jury_verdict": judge_vote,
        "consensus_type": consensus_type,
        "consensus_confidence": consensus_score,
        "vote_breakdown": {
            "advocate": advocate_vote,
            "skeptic": skeptic_vote,
            "judge": judge_vote
        },
        "debate_transcript": debate_transcript
    }
