import requests
from datetime import datetime, timedelta
import time

SESSION = requests.Session()

ALL_SLOTS = [
    "07:00","08:00","09:00","10:00","11:00","12:00",
    "13:00","14:00","15:00","16:00","17:00","18:00",
    "19:00","20:00"
]

# 🔐 LOGIN
def login(email, password):
    url = "https://pitchpro.hu/signin_handler.php"

    payload = {
        "email": email,
        "jelszo": password
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://pitchpro.hu",
        "Referer": "https://pitchpro.hu/index",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    res = SESSION.post(url, data=payload, headers=headers)

    return res.status_code == 200


# 📅 FETCH AVAILABLE SLOTS
def get_available_slots(date):
    # ✅ STEP 1 — initialize session context (CRITICAL FIX)
    init_url = f"https://pitchpro.hu/fieldday?complex_id=12&date={date}&sport=Tenisz&field_id=27&time=13:00"

    SESSION.get(init_url, headers={
        "User-Agent": "Mozilla/5.0"
    })

    # small delay helps session consistency
    time.sleep(0.5)

    # ✅ STEP 2 — build time range
    start = f"{date}T00:00:00+01:00"
    next_day = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    end = f"{next_day}T00:00:00+01:00"

    # ✅ STEP 3 — fetch reservations
    url = "https://pitchpro.hu/fetchReservations2.php"

    params = {
        "start": start,
        "end": end
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Referer": f"https://pitchpro.hu/fieldday?complex_id=12&date={date}&sport=Tenisz&field_id=27",
        "Origin": "https://pitchpro.hu"
    }

    res = SESSION.get(url, params=params, headers=headers, allow_redirects=True)

    # 🧠 Debug protection
    if "application/json" not in res.headers.get("Content-Type", ""):
        raise Exception(f"Non-JSON response: {res.text[:200]}")

    data = res.json()

    booked = set()

    for r in data:
        if r.get("field_id") == "27" and r.get("reservation_date") == date:
            start_h = int(r["reservation_start_time"][:2])
            end_h = int(r["reservation_end_time"][:2])

            for h in range(start_h, end_h):
                booked.add(f"{h:02d}:00")

    available = [s for s in ALL_SLOTS if s not in booked]

    return available


# 🤖 MAIN AGENT
def run_agent(date, preference, email, password):
    # login first
    if not login(email, password):
        return {"status": "login_failed"}

    slots = get_available_slots(date)

    # filter preference
    if preference == "AM":
        slots = [s for s in slots if int(s[:2]) < 12]
    elif preference == "PM":
        slots = [s for s in slots if int(s[:2]) >= 12]

    if not slots:
        return {"status": "no_slots"}

    return {
        "status": "available",
        "suggested_slot": slots[0],
        "all_slots": slots
    }