from app.rag.service import RAGThreatAnalyzer


def main():
    analyzer = RAGThreatAnalyzer()

    # Representative BOGEY-ALERT detection.
    employee = {
        "role": "developer",
        "department": "engineering",
    }

    window = {
        "observed_activity": "delete",
        "total_events": 120,
        "files_created": 0,
        "files_modified": 10,
        "files_deleted": 110,
        "files_moved": 0,
        "sensitive_events": 80,
        "sensitive_ratio": 80 / 120,
        "total_data_volume": 524288000,
        "activity_rate": 2.0,
        "after_hours": True,
    }

    anomaly = {
        "is_anomaly": True,
        "anomaly_score": 0.9718,
    }

    risk = {
        "risk_score": 90,
        "risk_level": "HIGH",
        "reasons": [
            "Behavior is highly anomalous compared with the employee baseline.",
            "Sensitive-file activity is significantly higher than normal.",
            "Data volume is significantly higher than the employee baseline.",
            "Activity rate indicates an unusual behavioral burst.",
            "Activity occurred outside the employee's normal working hours.",
        ],
    }

    policy = {
        "violations": [
            "Activity 'delete' is not permitted by the employee's role policy.",
            "Sensitive-data activity was observed, but the employee's role policy does not permit sensitive data access.",
        ]
    }

    authorization = {
        "allowed_activity": "delete",
        "scope_match": True,
    }

    result = analyzer.analyze(
        employee=employee,
        window=window,
        anomaly=anomaly,
        risk=risk,
        policy=policy,
        authorization=authorization,
    )

    print("=" * 70)
    print("BOGEY-ALERT RAG THREAT ANALYSIS")
    print("=" * 70)

    print("\n--- SECURITY CONTEXT ---")
    print(result["query_context"])

    print("\n--- RETRIEVED POLICIES ---")

    for index, policy_result in enumerate(
        result["retrieved_policies"],
        start=1,
    ):
        print(f"\n[{index}] {policy_result['title']}")
        print(
            f"Distance: "
            f"{policy_result['distance']:.4f}"
        )
        print(
            f"Source: "
            f"{policy_result['source']}"
        )
        print(
            f"Content: "
            f"{policy_result['content']}"
        )

    print("\n" + "=" * 70)
    print(
        f"Policies retrieved: "
        f"{result['policy_count']}"
    )
    print("=" * 70)
    print("\n--- AI THREAT EXPLANATION ---")
    print(result["threat_explanation"])

if __name__ == "__main__":
    main()