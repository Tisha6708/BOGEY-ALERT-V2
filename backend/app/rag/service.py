from app.rag.context_builder import build_threat_context
from app.rag.retriever import PolicyRetriever
from app.rag.generator import ThreatExplanationGenerator


class RAGThreatAnalyzer:
    """
    Main RAG intelligence layer for BOGEY-ALERT.

    Takes actual detection evidence, retrieves relevant
    organizational policies, and prepares contextual
    evidence for the analyst.
    """

    def __init__(self):
        self.retriever = PolicyRetriever()
        self.generator = ThreatExplanationGenerator()

    def analyze(
        self,
        *,
        employee: dict,
        window: dict,
        anomaly: dict,
        risk: dict,
        policy: dict | None = None,
        authorization: dict | None = None,
        top_k: int = 4,
    ) -> dict:

        # Build a query from the actual security evidence.
        context = build_threat_context(
            employee=employee,
            window=window,
            anomaly=anomaly,
            risk=risk,
            policy=policy,
            authorization=authorization,
        )

        # Retrieve relevant organizational policies.
        policies = self.retriever.retrieve(
            query=context,
            top_k=top_k,
        )

        explanation = self.generator.generate(
            security_context=context,
            retrieved_policies=policies,
        )

        return {
            "query_context": context,
            "retrieved_policies": policies,
            "policy_count": len(policies),
            "threat_explanation": explanation,
        }