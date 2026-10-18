"""
Campus location graph: places students might be located, connected by walking paths.
Used by the meeting-point search module.
"""

LOCATIONS = {
    "Main Gate":       (0, 0),
    "Library":         (2, 2),
    "Cafeteria":       (-2, 1),
    "Hostel A":        (4, 4),
    "Hostel B":        (-4, 3),
    "Sports Complex":  (3, -2),
    "Auditorium":      (-1, 4),
    "Lab Block":       (1, -3),
    "Admin Block":     (-3, -2),
    "Food Court":      (0, 2),
    "Parking Lot":     (5, 0),
    "Park":            (-2, -4),
}

PATHS = [
    ("Main Gate", "Library"),
    ("Main Gate", "Cafeteria"),
    ("Main Gate", "Admin Block"),
    ("Main Gate", "Lab Block"),
    ("Library", "Food Court"),
    ("Library", "Hostel A"),
    ("Library", "Auditorium"),
    ("Cafeteria", "Hostel B"),
    ("Cafeteria", "Food Court"),
    ("Hostel A", "Sports Complex"),
    ("Hostel A", "Parking Lot"),
    ("Hostel B", "Auditorium"),
    ("Hostel B", "Park"),
    ("Sports Complex", "Lab Block"),
    ("Sports Complex", "Parking Lot"),
    ("Admin Block", "Park"),
    ("Admin Block", "Lab Block"),
    ("Food Court", "Auditorium"),
    ("Lab Block", "Park"),
]


def _distance(loc1, loc2):
    (x1, y1), (x2, y2) = LOCATIONS[loc1], LOCATIONS[loc2]
    return round(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5, 2)


def build_graph():
    graph = {loc: [] for loc in LOCATIONS}
    for a, b in PATHS:
        d = _distance(a, b)
        graph[a].append((b, d))
        graph[b].append((a, d))
    return graph


GRAPH = build_graph()
