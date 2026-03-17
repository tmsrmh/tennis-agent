import requests

SESSION = requests.Session()
REQUEST_TIMEOUT = 15
COURT_COUNT = 6
COMPLEX_ID = 12
SPORT = "Tenisz"
DEFAULT_FIELD_ID = 27

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

    try:
        res = SESSION.post(url, data=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        return True
    except requests.RequestException:
        return False


# 📅 FETCH AVAILABLE SLOTS
def get_available_slots(date):
    # Bootstrap session context; this endpoint relies on page context/cookies.
    init_url = (
        "https://pitchpro.hu/fieldday"
        f"?complex_id={COMPLEX_ID}&date={date}&sport={SPORT}&field_id={DEFAULT_FIELD_ID}"
    )
    SESSION.get(init_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=REQUEST_TIMEOUT)

    url = "https://pitchpro.hu/fetchReservations2.php"

    params = {
        "start": f"{date}T00:00:00+01:00",
        "end": f"{date}T23:59:59+01:00"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Referer": (
            "https://pitchpro.hu/fieldday"
            f"?complex_id={COMPLEX_ID}&date={date}&sport={SPORT}&field_id={DEFAULT_FIELD_ID}"
        ),
        "Origin": "https://pitchpro.hu"
    }

    res = SESSION.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    res.raise_for_status()

    text = res.text.strip()

    if not text.startswith("["):
        raise Exception(f"Non-JSON response: {text[:200]}")

    reservations = res.json()

    # ✅ USE YOUR NEW FUNCTION HERE
    slots = compute_available_slots(reservations)

    return slots, reservations

def compute_available_slots(reservations):
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

        if len(fields_taken) < COURT_COUNT:
            available.append(time)

    return available

def find_free_field(reservations, time):
    taken = set(
        str(r["field_id"])
        for r in reservations
        if r["reservation_start_time"] == time
    )

    for field_id in range(1, COURT_COUNT + 1):
        if str(field_id) not in taken:
            return field_id

    return None

def run_agent(date, preference, email, password):
    if not login(email, password):
        return {"status": "login_failed"}

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

    res = SESSION.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()

    return res.text
