from .database import Base, SessionLocal, engine
from .models import Match, Need, Report, Volunteer


def create_db_tables():
    Base.metadata.create_all(bind=engine)


def seed_data():
    db = SessionLocal()
    try:
        # Clear existing demo data (order matters due to foreign keys)
        db.query(Match).delete()
        db.query(Report).delete()
        db.query(Need).delete()
        db.query(Volunteer).delete()

        volunteers = [
            Volunteer(name="Dr. Riya Sinha", skills=["doctor"], location="Patna", availability="full-time", contact="+91-900001001"),
            Volunteer(name="Amit Kumar", skills=["driver"], location="Bihar rural", availability="weekends", contact="+91-900001002"),
            Volunteer(name="Nazia Parveen", skills=["food distribution"], location="Guwahati", availability="evenings", contact="+91-900001003"),
            Volunteer(name="Samuel Raj", skills=["logistics"], location="Chennai", availability="full-time", contact="+91-900001004"),
            Volunteer(name="Dr. Ananya Das", skills=["doctor"], location="Assam", availability="day shift", contact="+91-900001005"),
            Volunteer(name="Pankaj Yadav", skills=["driver"], location="Patna", availability="night shift", contact="+91-900001006"),
            Volunteer(name="Lalita Devi", skills=["food distribution"], location="Bihar rural", availability="full-time", contact="+91-900001007"),
            Volunteer(name="Rohit Menon", skills=["logistics"], location="Chennai", availability="weekdays", contact="+91-900001008"),
            Volunteer(name="Dr. Iqbal Ahmed", skills=["doctor"], location="Guwahati", availability="on-call", contact="+91-900001009"),
            Volunteer(name="Meena Kumari", skills=["food distribution"], location="Patna", availability="mornings", contact="+91-900001010"),
            Volunteer(name="Harish Nair", skills=["driver"], location="Chennai", availability="weekends", contact="+91-900001011"),
            Volunteer(name="Kaberi Dutta", skills=["logistics"], location="Assam", availability="full-time", contact="+91-900001012"),
            Volunteer(name="Dr. Sneha Joseph", skills=["doctor"], location="Chennai", availability="day shift", contact="+91-900001013"),
            Volunteer(name="Vikram Singh", skills=["driver"], location="Bihar rural", availability="full-time", contact="+91-900001014"),
            Volunteer(name="Paromita Bora", skills=["food distribution"], location="Assam", availability="weekdays", contact="+91-900001015"),
            Volunteer(name="Arjun Prakash", skills=["logistics"], location="Patna", availability="evenings", contact="+91-900001016"),
            Volunteer(name="Dr. Neelam Verma", skills=["doctor"], location="Bihar rural", availability="on-call", contact="+91-900001017"),
            Volunteer(name="Dinesh Rai", skills=["driver"], location="Guwahati", availability="full-time", contact="+91-900001018"),
            Volunteer(name="Sujata Rao", skills=["food distribution"], location="Chennai", availability="weekends", contact="+91-900001019"),
            Volunteer(name="Imran Ali", skills=["logistics"], location="Assam", availability="night shift", contact="+91-900001020"),
        ]

        needs = [
            Need(source_text="Flood-hit hamlet near Patna needs cooked meal packets for 120 families.", category="food", location="Patna", urgency_score=8, status="open"),
            Need(source_text="Mobile medical camp required in Assam village for fever and dehydration cases.", category="medical", location="Assam", urgency_score=9, status="open"),
            Need(source_text="Boat and vehicle coordination needed to evacuate elderly from low-lying Guwahati area.", category="rescue", location="Guwahati", urgency_score=10, status="open"),
            Need(source_text="Temporary tarpaulin shelters needed for displaced families in Bihar rural block.", category="shelter", location="Bihar rural", urgency_score=7, status="open"),
            Need(source_text="Dry ration distribution support required in Chennai relief center.", category="food", location="Chennai", urgency_score=6, status="open"),
            Need(source_text="First-aid support needed at Assam camp with 60 children.", category="medical", location="Assam", urgency_score=8, status="open"),
            Need(source_text="Rescue transport needed overnight for stranded workers near Patna bypass.", category="rescue", location="Patna", urgency_score=9, status="open"),
            Need(source_text="Community hall in Guwahati needs partitioning and bedding for emergency shelter.", category="shelter", location="Guwahati", urgency_score=5, status="open"),
            Need(source_text="Cooked food delivery needed for marooned households in Bihar rural panchayat.", category="food", location="Bihar rural", urgency_score=7, status="open"),
            Need(source_text="Medical volunteers needed for wound care in Chennai suburban relief point.", category="medical", location="Chennai", urgency_score=6, status="open"),
            Need(source_text="Rescue team with drivers required to move families from embankment zone in Assam.", category="rescue", location="Assam", urgency_score=8, status="open"),
            Need(source_text="Shelter setup needed at Patna school building for 90 evacuees.", category="shelter", location="Patna", urgency_score=4, status="open"),
            Need(source_text="Food kit sorting and distribution needed in Guwahati NGO warehouse.", category="food", location="Guwahati", urgency_score=3, status="open"),
            Need(source_text="Medical screening camp requested in Bihar rural for post-flood infections.", category="medical", location="Bihar rural", urgency_score=10, status="open"),
            Need(source_text="Emergency shelter support requested in Chennai for migrant families after cyclone.", category="shelter", location="Chennai", urgency_score=2, status="open"),
        ]

        db.add_all(volunteers)
        db.add_all(needs)
        db.commit()

        print("Seed complete: inserted 20 volunteers and 15 needs.")
    finally:
        db.close()


if __name__ == "__main__":
    create_db_tables()
    seed_data()
