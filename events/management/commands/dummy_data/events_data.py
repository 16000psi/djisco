from datetime import timedelta

from django.utils import timezone


def generate_datetimes():
    now = timezone.now()
    past_datetimes = [
        now - timedelta(days=10, hours=2),
        now - timedelta(days=9, hours=4),
        now - timedelta(days=8, hours=3),
        now - timedelta(days=7, hours=1),
        now - timedelta(days=6, hours=5),
    ]
    future_datetimes = [
        now + timedelta(days=1, hours=2),
        now + timedelta(days=2, hours=3),
        now + timedelta(days=3, hours=1),
        now + timedelta(days=4, hours=4),
        now + timedelta(days=5, hours=5),
    ]

    return past_datetimes + future_datetimes


start_times = generate_datetimes()

events_data = [
    {
        "title": "Django Workshop",
        "maximum_attendees": 50,
        "starts_at": start_times[0],
        "ends_at": start_times[0] + timedelta(hours=2),
        "location": "123 Django Lane, London",
        "description": "An introductory workshop on Django framework.",
    },
    {
        "title": "Python Meetup",
        "maximum_attendees": 100,
        "starts_at": start_times[1],
        "ends_at": start_times[1] + timedelta(hours=3),
        "location": "456 Python Street, Anglesey",
        "description": "Monthly meetup for Python enthusiasts.",
    },
    {
        "title": "Tech Conference",
        "maximum_attendees": 200,
        "starts_at": start_times[2],
        "ends_at": start_times[2] + timedelta(hours=4),
        "location": "789 Tech Avenue, London",
        "description": "Annual conference on the latest in technology.",
    },
    {
        "title": "Perfume Exhibition",
        "maximum_attendees": 150,
        "starts_at": start_times[3],
        "ends_at": start_times[3] + timedelta(hours=1),
        "location": "321 Fragrance Road, Birmingham",
        "description": "Exhibition showcasing the latest in perfume industry.",
    },
    {
        "title": "Stress Management Seminar",
        "maximum_attendees": 75,
        "starts_at": start_times[4],
        "ends_at": start_times[4] + timedelta(hours=5),
        "location": "654 Wellness Boulevard, Oxford",
        "description": "Seminar on managing stress in daily life.",
    },
    {
        "title": "Partisan Politics Discussion",
        "maximum_attendees": 60,
        "starts_at": start_times[5],
        "ends_at": start_times[5] + timedelta(hours=2),
        "location": "987 Debate Hall, London",
        "description": "Discussion on the current state of partisan politics.",
    },
    {
        "title": "Coding Bootcamp",
        "maximum_attendees": 80,
        "starts_at": start_times[6],
        "ends_at": start_times[6] + timedelta(hours=3),
        "location": "654 Code Street, Anglesey",
        "description": "Intensive coding bootcamp for beginners.",
    },
    {
        "title": "AI Symposium",
        "maximum_attendees": 120,
        "starts_at": start_times[7],
        "ends_at": start_times[7] + timedelta(hours=1),
        "location": "321 Innovation Park, London",
        "description": "Symposium on advancements in artificial intelligence.",
    },
    {
        "title": "Perfume Making Workshop",
        "maximum_attendees": 30,
        "starts_at": start_times[8],
        "ends_at": start_times[8] + timedelta(hours=4),
        "location": "456 Fragrance Studio, Birmingham",
        "description": "Hands-on workshop on making your own perfume.",
    },
    {
        "title": "Wellness Retreat",
        "maximum_attendees": 40,
        "starts_at": start_times[9],
        "ends_at": start_times[9] + timedelta(hours=5),
        "location": "789 Tranquility Base, Oxford",
        "description": "Day-long retreat focused on wellness and mindfulness.",
    },
]
