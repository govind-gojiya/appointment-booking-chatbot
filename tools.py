from langchain.tools import tool
from db import get_session, Appointment
from datetime import datetime, timedelta
from dateutil import parser
from sqlalchemy.exc import IntegrityError
import uuid
import secrets

WORK_START = 9
WORK_END = 18


def normalize_datetime(date_str: str, time_str: str):
    """ normalize datetime """
    try:
        dt = parser.parse(f"{date_str} {time_str}")
        if dt <= datetime.now():
            return False, "Appointment must be in the future."
        if not (WORK_START <= dt.hour < WORK_END):
            return False, "Bookings allowed only between 9 AM and 6 PM."
        # 1-hour slot rounding
        dt = dt.replace(minute=0, second=0, microsecond=0)
        return True, dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except Exception:
        return False, "Invalid date or time format."

def is_slot_available(session, date: str, time: str):
    """ Check if a given date-time slot is available """
    existing = session.query(Appointment).filter(
        Appointment.date == date,
        Appointment.time == time
    ).first()

    return existing is None

def generate_booking_id():
    return str(uuid.uuid4())[:8]

def generate_token():
    return secrets.token_hex(4)

def format_booking(appointment):
    return f"""
Booking Details:
-------------------------
Booking ID : {appointment.id}
Token      : {appointment.token}
Name       : {appointment.name}
Date       : {appointment.date}
Time       : {appointment.time}
-------------------------
"""


@tool
def book_appointment(name: str, date: str, time: str):
    """
    Book a new 1-hour appointment for a user.

    Call this tool ONLY when you have ALL THREE values: name, date, and time.
    If any value is missing, ask the user for it before calling this tool.

    Args:
        name: Full name of the person booking (e.g. "Alice Smith").
        date: Date in YYYY-MM-DD format (e.g. "2026-03-10").
              NEVER pass natural language like "tomorrow" or "next Friday".
              If the user gave a relative or year-less date, call
              get_current_datetime first to resolve it.
        time: Time in HH:MM 24-hour format (e.g. "14:00" for 2 PM).
              Allowed range: 9 AM to 6 PM (slots: 09:00, 10:00, ..., 17:00).

    Constraints:
        - Appointment must be in the future.
        - Only hourly slots between 9 AM and 6 PM are allowed.
        - A slot can only have one booking at a time.

    Returns:
        Booking confirmation with Booking ID and Token. Always show both to the user.
    """

    result = normalize_datetime(date, time)

    if result[0] is False:
        return result[1]

    
    _, normalized_date, normalized_time = result
    session = get_session()

    if not is_slot_available(session, normalized_date, normalized_time):
        session.close()
        return "This time slot is already booked."
    
    booking_id = generate_booking_id()
    token = generate_token()

    appointment = Appointment(
        id=booking_id,
        token=token,
        name=name,
        date=normalized_date,
        time=normalized_time
    )

    try:
        session.add(appointment)
        session.commit()
        formatted = format_booking(appointment)
        return f"Appointment booked successfully!\n{formatted}"
    except IntegrityError:
        session.rollback()
        return "This time slot is already booked."
    finally:
        session.close()

@tool
def cancel_appointment(booking_id: str = None, token: str = None,
                       name: str = None, date: str = None):
    """
    Cancel an existing appointment.

    Call this tool ONLY when you have one of these complete identifier sets:
        Option A (preferred): booking_id AND token — BOTH are required together.
        Option B: name AND date — BOTH are required together.

    IMPORTANT: Do NOT call with only booking_id alone, or only token alone.
    If the user gives only one of booking_id/token, ask for the other before calling.
    If the user gives only name without date, ask for the date before calling.

    Args:
        booking_id: Booking ID from the original confirmation (e.g. "a1b2c3d4").
                    Required when using Option A.
        token:      Token from the original confirmation (e.g. "ff00ab12").
                    Required when using Option A.
        name:       Full name used when the appointment was booked. Required for Option B.
        date:       Date of the appointment in YYYY-MM-DD format (e.g. "2026-03-10").
                    Required for Option B. Call get_current_datetime first if
                    the user gave a relative or year-less date.

    Returns:
        Formatted details of the cancelled appointment, or an error message.
    """

    session = get_session()

    if booking_id and token:
        appointment = session.query(Appointment).filter(
            Appointment.id == booking_id,
            Appointment.token == token
        ).first()

    elif name and date:
        appointment = session.query(Appointment).filter(
            Appointment.name == name,
            Appointment.date == date
        ).first()
    else:
        session.close()
        return "Provide booking_id + token OR name + date."

    if not appointment:
        session.close()
        return "No matching booking found."

    formatted = format_booking(appointment)
    session.delete(appointment)
    session.commit()
    session.close()

    return f"Appointment cancelled successfully.\n{formatted}"

@tool
def reschedule_appointment(booking_id: str = None, token: str = None,
                           name: str = None, date: str = None,
                           new_date: str = None, new_time: str = None):
    """
    Reschedule an existing appointment to a new date and time.

    Call this tool ONLY when you have BOTH:
        1. A way to identify the existing booking (one option below), AND
        2. new_date AND new_time for the new slot.

    If new_date or new_time is missing, ask the user for them before calling.

    Identification options (pick the first one the user has provided):
        Option A: booking_id alone
        Option B: token alone
        Option C: name AND date (both required together)

    Args:
        booking_id: Booking ID from the original confirmation. Use for Option A.
        token:      Token from the original confirmation. Use for Option B.
        name:       Full name used during booking. Required for Option C.
        date:       Current appointment date in YYYY-MM-DD format. Required for Option C.
                    Call get_current_datetime first if the user gave a relative date.
        new_date:   New date in YYYY-MM-DD format (e.g. "2026-03-10"). REQUIRED.
                    NEVER pass natural language. Call get_current_datetime first
                    if the user gave a relative or year-less date.
        new_time:   New time in HH:MM 24-hour format (e.g. "15:00"). REQUIRED.
                    Must be between 09:00 and 17:00.

    Returns:
        Updated formatted booking details, or an error message.
    """

    result = normalize_datetime(new_date, new_time)
    if result[0] is False:
        return result[1]

    _, normalized_date, normalized_time = result

    session = get_session()

    if booking_id:
        appointment = session.query(Appointment).filter(
            Appointment.id == booking_id
        ).first()
    elif token:
        appointment = session.query(Appointment).filter(
            Appointment.token == token
        ).first()
    elif name and date:
        appointment = session.query(Appointment).filter(
            Appointment.name == name,
            Appointment.date == date
        ).first()
    else:
        session.close()
        return "Provide booking_id OR token OR name + date."

    if not appointment:
        session.close()
        return "Booking not found."
    
    if not is_slot_available(
        session,
        normalized_date,
        normalized_time
    ):
        session.close()
        return "New time slot is already booked."

    appointment.date = normalized_date
    appointment.time = normalized_time

    try:
        session.commit()
        formatted = format_booking(appointment)
        return f"Appointment rescheduled successfully.\n{formatted}"

    except IntegrityError:
        session.rollback()
        return "New time slot is already booked."

    finally:
        session.close()


@tool
def get_free_slots(date: str = None):
    """
    Get all available (unbooked) 1-hour time slots for a given date.

    Call this tool when the user asks about availability, free slots, open times,
    or wants to know when they can book an appointment.

    Args:
        date: Date in YYYY-MM-DD format (e.g. "2026-03-10"). OPTIONAL — if not
              provided, returns slots for today and tomorrow automatically.
              NEVER pass natural language. Call get_current_datetime first to
              resolve "tomorrow", "next Friday", or any year-less date.

    Returns:
        List of available hourly slots (e.g. 9:00, 10:00, ..., 17:00) for each
        requested date. Working hours are 9 AM to 6 PM.
    """

    session = get_session()

    dates_to_check = []

    if date:
        parsed = parser.parse(date)
        dates_to_check.append(parsed.strftime("%Y-%m-%d"))
    else:
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        dates_to_check.append(today.strftime("%Y-%m-%d"))
        dates_to_check.append(tomorrow.strftime("%Y-%m-%d"))

    response = ""

    for check_date in dates_to_check:
        booked = session.query(Appointment).filter(
            Appointment.date == check_date
        ).all()

        booked_hours = {int(a.time.split(":")[0]) for a in booked}

        free_slots = [
            f"{hour}:00"
            for hour in range(WORK_START, WORK_END)
            if hour not in booked_hours
        ]

        response += f"\nDate: {check_date}\nAvailable Slots: {free_slots}\n"

    session.close()
    return response

@tool
def list_user_bookings(name: str):
    """
    List all appointments booked under a given name.

    Call this tool when the user asks to see, view, or check their bookings.
    If the user's name is not known, ask for it before calling this tool.

    Args:
        name: Full name used when the appointments were booked (e.g. "Alice Smith").
              Ask the user if not already provided.

    Returns:
        Formatted list of all bookings for that name, each showing Booking ID,
        Token, Date, and Time. Returns a message if no bookings are found.
    """

    session = get_session()

    bookings = session.query(Appointment).filter(
        Appointment.name == name
    ).all()

    if not bookings:
        session.close()
        return "No bookings found."

    response = "\nYour Bookings:\n"

    for booking in bookings:
        response += format_booking(booking)

    session.close()
    return response

@tool
def get_current_datetime() -> str:
    """
    Get the current date and time.

    Call this tool BEFORE passing any date to another tool when:
    - The user gives a date without a year (e.g. "7th March", "March 10", "10th").
    - The user says "today" or "tomorrow".
    - You are unsure what the current year, month, or day is.

    Do NOT guess or assume the current date — always call this tool first.

    Returns:
        Current date and time with full context:
        day name, date (YYYY-MM-DD), time (HH:MM), and year — so you can
        correctly resolve "today", "tomorrow", and year-less dates.
    """
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    return (
        f"Current datetime: {now.strftime('%A, %Y-%m-%d, %H:%M')}\n"
        f"Tomorrow's date: {tomorrow.strftime('%A, %Y-%m-%d')}"
    )


ALL_TOOLS = [
    get_current_datetime,
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
    get_free_slots,
    list_user_bookings,
]