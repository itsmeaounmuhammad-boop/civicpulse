"""
Idempotent seed script — loads >= 30 realistic complaints.

Idempotency strategy: each seed complaint gets a deterministic UUID
(uuid5, namespaced) derived from its text, so re-running this script
never inserts duplicates — it relies on the primary key conflict being
a no-op, not on checking count() first (which would race under concurrent runs).

Run with: python -m scripts.seed  (from backend/, with DATABASE_URL set)
"""

import asyncio
import time
import uuid

from sqlalchemy import text

from app.database import AsyncSessionLocal

SEED_NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

COMPLAINTS = [
    ("Burst water main flooding Street 12 since fajr, water entering ground floors", "Street 12, G-9", "water", "high"),
    ("Transformer sparking near mohalla chowk, bohat khatarnak lag raha hai", "Mohalla Chowk, Sector F-10", "electricity", "high"),
    ("Sewerage overflow outside house number 45, boo phel gayi hai poore gali mein", "House 45, Street 8, Model Town", "sanitation", "high"),
    ("Bijli 3 din se gayi hui hai is area mein, WAPDA ko call kiya koi response nahi", "Block C, Johar Town", "electricity", "high"),
    ("Deep pothole on main road, do motorcycle gir chuke hain is hafte", "Main Boulevard, DHA Phase 5", "roads", "high"),
    ("Streetlight khraab hai teen hafte se, raat ko bohat andhera hota hai", "Street 22, Satellite Town", "streetlights", "normal"),
    ("Garbage collection nahi hua is hafte, kachra sarak par phail gaya", "Sector G-11/3", "sanitation", "normal"),
    ("Water pressure bohat kam hai subha se, tank bhi nahi bhar raha", "Gulberg III", "water", "normal"),
    ("Road par manhole cover missing hai, khula gaddha hai, bacchon ke liye khatarnak", "Township Block 2", "roads", "high"),
    ("Electricity pole leaning dangerously after storm last night", "Chak Jhumra Road", "electricity", "high"),
    ("Traffic signal not working at main intersection since Monday", "Faisal Town Signal", "roads", "normal"),
    ("Sui gas leak smell near park, families are worried", "Iqbal Park Area", "other", "high"),
    ("Stray dogs increasing in park, walkers scared, koi action nahi liya gaya", "F-8 Park", "other", "low"),
    ("Water tanker line ganda pani supply kar raha hai, bachon ko ulti ho rahi hai", "Green Town", "water", "high"),
    ("Streetlight pole gir gaya road ke beech mein, traffic block hai", "Canal Road", "streetlights", "high"),
    ("Illegal encroachment on footpath, pedestrians forced onto main road", "Anarkali Bazaar", "other", "low"),
    ("Sewer line choked for two weeks, bohat badbu aa rahi hai", "Samanabad", "sanitation", "normal"),
    ("Speed breaker missing sign board, do accidents ho chuke hain raat mein", "Ferozepur Road", "roads", "high"),
    ("Meter reading galat aa rahi hai, bill double ho gaya is mahine", "Wapda Town", "electricity", "low"),
    ("Park ki grass overgrown hai, saanp dekha gaya hai bachon ne", "Model Town Park", "other", "normal"),
    ("Water supply timing changed without notice, subha nahi aata ab", "Faisalabad Road", "water", "low"),
    ("Broken drain cover on footpath, ek bacha girte girte bacha", "Susan Road", "sanitation", "high"),
    ("New streetlights installed but not switched on yet, ilaqa andhera hai", "Peoples Colony", "streetlights", "normal"),
    ("Overhead wires hanging low near school, bachon ko chot lag sakti hai", "Millat Road", "electricity", "high"),
    ("Road construction debris left on street for a month, gaadi nikalna mushkil hai", "Susan Road Extension", "roads", "normal"),
    ("Public toilet in market is non-functional, sfai bilkul nahi hai", "Clock Tower Market", "sanitation", "low"),
    ("Voltage fluctuation damaging appliances, teesri martaba fridge kharab hua", "Abdullahpur", "electricity", "normal"),
    ("Footpath streetlight flickering all night, complaint diya tha last month bhi", "D Ground Road", "streetlights", "low"),
    ("Open drain near bus stop overflowing after light rain", "Batala Colony", "sanitation", "high"),
    ("Median plants dead and blocking driver visibility at turn", "Jail Road", "roads", "low"),
    ("Community park swings broken for months, bachay khel nahi sakte", "Rehmanpura Park", "other", "low"),
    ("Water line burst near school gate, road bhi dhas gaya hai", "Government School Road, Chak Jhumra", "water", "high"),
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        inserted = 0
        for complaint_text, location, category, priority in COMPLAINTS:
            complaint_id = uuid.uuid5(SEED_NAMESPACE, complaint_text)
            result = await session.execute(
                text(
                    """
                    INSERT INTO complaints
                        (id, text, location, category, priority, status,
                         triaged_by, triage_latency_ms, created_at, updated_at)
                    VALUES
                        (:id, :text, :location, :category, :priority, 'open',
                         'rules', 5, now(), now())
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                {
                    "id": complaint_id,
                    "text": complaint_text,
                    "location": location,
                    "category": category,
                    "priority": priority,
                },
            )
            inserted += result.rowcount

        await session.commit()
        print(f"Seed complete. {inserted} new rows inserted (0 means already seeded).")


if __name__ == "__main__":
    start = time.time()
    asyncio.run(seed())
    print(f"Took {time.time() - start:.2f}s")