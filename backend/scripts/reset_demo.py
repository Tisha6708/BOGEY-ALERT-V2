from sqlmodel import Session, text

from app.db.session import engine


def reset_demo_data():
    print("=" * 60)
    print("BOGEY-ALERT DEMO DATA RESET")
    print("=" * 60)

    with Session(engine) as session:
        print("\n[1/3] Deleting alerts...")
        session.exec(text("DELETE FROM alert"))
        print("      Alerts deleted.")

        print("[2/3] Deleting behavioral windows...")
        session.exec(text("DELETE FROM behavioralwindow"))
        print("      Behavioral windows deleted.")

        print("[3/3] Deleting activity events...")
        session.exec(text("DELETE FROM activityevent"))
        print("      Activity events deleted.")

        session.commit()

    print("\n" + "=" * 60)
    print("RESET COMPLETE")
    print("=" * 60)
    print("\nPreserved:")
    print("  [OK] Employees")
    print("  [OK] Devices")
    print("  [OK] Role policies")
    print("  [OK] Behavioral baselines")
    print("  [OK] Exceptions")
    print("  [OK] ML model artifacts")
    print("  [OK] RAG knowledge base")

    print("\nRemoved:")
    print("  [X] Alerts")
    print("  [X] Behavioral windows")
    print("  [X] Activity events")
    print()


if __name__ == "__main__":
    reset_demo_data()