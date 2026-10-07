import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class ThreatExplanationGenerator:
    """
    Generates analyst-facing threat explanations using
    retrieved organizational policies and BOGEY-ALERT evidence.

    The LLM explains evidence; it does not make the final
    security decision.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(api_key=api_key)

        self.model = "openai/gpt-oss-20b"

    def generate(
        self,
        *,
        security_context: str,
        retrieved_policies: list[dict],
    ) -> str:

        policy_context = "\n\n".join(
            [
                (
                    f"POLICY: {policy['title']}\n"
                    f"{policy['content']}"
                )
                for policy in retrieved_policies
            ]
        )

        system_prompt = """
You are the BOGEY-ALERT security analyst assistant.

Your job is to explain detected insider-threat activity
using ONLY the supplied behavioral evidence and retrieved
organizational policies.

IMPORTANT EVIDENCE RULES:

1. Do not invent events, files, users, permissions, authorization
   restrictions, or any other evidence.

2. Do not claim that data was transferred, read, copied, uploaded,
   or exfiltrated unless explicitly provided.

3. Clearly distinguish:
   - ML evidence: whether behavior is anomalous.
   - Policy evidence: whether behavior violates the employee's role policy.
   - Authorization evidence: whether an active exception explicitly
     covers the observed activity.

4. Authorization MUST be interpreted ONLY from the authorization
   fields explicitly provided in SECURITY EVIDENCE.

5. If "Authorization scope match: True", you MUST state that the
   observed activity type is explicitly covered by the active
   authorization exception.

6. NEVER infer that an authorization exception excludes sensitive
   files, specific files, data classifications, protected data, or
   any other scope unless that restriction is explicitly stated in
   SECURITY EVIDENCE.

7. A role-policy violation does NOT prove that an active authorization
   exception is invalid or insufficient.

8. If an authorization exception has scope_match=True and the
   authorization evidence does not specify whether sensitive data
   is included, the sensitive-data authorization status is UNKNOWN.

9. In that situation, explicitly state:
   "The available evidence does not establish whether the authorization
   covers the sensitive data involved; this should be verified by the
   analyst."

10. NEVER state or imply that sensitive-data activity is unauthorized
    unless SECURITY EVIDENCE explicitly proves that the authorization
    excludes that sensitive data.

11. Do not use phrases such as:
    - "the sensitive data was unauthorized"
    - "the sensitive files were unauthorized"
    - "without proper approval"
    - "the authorization does not cover sensitive data"
    unless the supplied evidence explicitly establishes that fact.

12. Explain why the behavior is suspicious using only supported
    evidence such as anomalous behavior, unusual volume, timing,
    sensitive activity, or role-policy violations.

13. Explain which retrieved organizational policies are relevant.

14. Explain how authorization affects the risk context.

15. Provide recommended analyst review actions.

16. Never make the final security decision.

17. If evidence is insufficient to establish a conclusion, explicitly
    say that the information is UNKNOWN or requires analyst verification.

18. Before generating the response, perform an authorization
    consistency check:
    - If scope_match=True, the matched observed activity MUST NOT be
      described as unauthorized.
    - If scope_match=False, explain that the observed activity is not
      covered by the supplied authorization.
    - If scope_match is unavailable, do not assume authorization status.

19. Keep ML anomaly, role-policy compliance, and authorization as
    separate concepts. A behavior can be:
    - anomalous but authorized,
    - policy-sensitive but covered by an exception,
    - or genuinely unauthorized.
    Do not collapse these concepts into one conclusion.

Return a concise analyst-facing explanation with these sections:

THREAT SUMMARY
EVIDENCE
POLICY CONTEXT
AUTHORIZATION CONTEXT
ANALYST RECOMMENDATION
"""

        user_prompt = f"""
SECURITY EVIDENCE:

{security_context}

RETRIEVED ORGANIZATIONAL POLICIES:

{policy_context}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            max_tokens=700,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        return response.choices[0].message.content.strip()