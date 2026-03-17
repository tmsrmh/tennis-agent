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
    url = "https://pitchpro.hu/fetchReservations2"

    params = {
        "start": f"{date}T00:00:00+01:00",
        "end": f"{date}T23:59:59+01:00"
    }

    res = SESSION.get(url, params=params)

    text = res.text.strip()

    if not text.startswith("["):
        raise Exception(f"Non-JSON response: {text[:200]}")

    reservations = res.json()

    # ✅ USE YOUR NEW FUNCTION HERE
    slots = compute_available_slots(reservations)

    return slots, reservations

def compute_available_slots(reservations):
    ALL_SLOTS = [f"{h:02d}:00" for h in range(7, 21)]

    # map: time → set of occupied fields
    occupied = {}

    for r in reservations:
        time = r["reservation_start_time"]
        field = r["field_id"]

        if time not in occupied:
            occupied[time] = set()

        occupied[time].add(field)

    available = []

    for time in ALL_SLOTS:
        fields_taken = occupied.get(time, set())

        # assume 6 courts (adjust if needed)
        if len(fields_taken) < 6:
            available.append(time)

    return available

def find_free_field(reservations, time):
    taken = set(
        r["field_id"]
        for r in reservations
        if r["reservation_start_time"] == time
    )

    for field_id in range(1, 7):
        if str(field_id) not in taken:
            return field_id

    return None

def run_agent(date, preference, email, password):
    login(email, password)

    slots, reservations = get_available_slots(date)

    if not slots:
        return {"status": "no_slots"}

    if preference == "PM":
        slots = [s for s in slots if int(s[:2]) >= 12]

    if not slots:
        return {"status": "no_matching_slots"}

    chosen_slot = slots[0]

    field_id = find_free_field(reservations, chosen_slot)

    response = create_reservation(date, chosen_slot, field_id)

    return {
        "status": "attempted_booking",
        "slot": chosen_slot,
        "field_id": field_id,
        "response": response
    }

def create_reservation(date, time_slot, field_id):
    url = "https://pitchpro.hu/reservationHandler2.php"

    payload = {
        "field_id": field_id,
        "reservation_date": date,
        "reservation_start_time": time_slot,
        "reservation_end_time": f"{int(time_slot[:2])+1:02d}:00"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Referer": f"https://pitchpro.hu/fieldday?complex_id=12&date={date}&sport=Tenisz&field_id={field_id}",
        "Origin": "https://pitchpro.hu"
    }

    res = SESSION.post(url, json=payload, headers=headers)

    return res.text
