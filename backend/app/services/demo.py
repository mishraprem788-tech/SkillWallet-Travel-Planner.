from datetime import timedelta

from app.schemas import Activity, DayPlan, Itinerary, TripRequest

INTEREST_BLOCKS = {
    "food": (
        ("Neighborhood breakfast", "Sample cafes and bakeries near your stay in {place}."),
        ("Market lunch", "Demo food-market stop matched to a {style} budget in {place}."),
        ("Regional dinner", "Sample evening meal featuring local dishes in {place}."),
    ),
    "culture": (
        ("Old-town walk", "Demo morning circuit of streets, courtyards, and local life in {place}."),
        ("Museum or gallery block", "Sample indoor culture stop paced for a {pace} {group} trip."),
        ("Live performance or night market", "Demo evening cultural outing in {place}."),
    ),
    "nature": (
        ("Park or waterfront", "Sample outdoor morning in a green or scenic pocket of {place}."),
        ("Viewpoint or garden", "Demo afternoon outdoors without leaving the city core."),
        ("Sunset lookout", "Sample wind-down with a view, kept inside the daily budget."),
    ),
    "adventure": (
        ("Active morning", "Demo bike, hike, or water activity scaled to a {pace} pace."),
        ("Hands-on workshop", "Sample booked experience that fits a {style} {place} trip."),
        ("Night neighborhood loop", "Demo lively evening circuit rather than a late club crawl."),
    ),
    "shopping": (
        ("Independent shops", "Sample morning browse of local makers in {place}."),
        ("Main market", "Demo afternoon market time with a hard spend cap."),
        ("Souvenir stop", "Sample short evening shop before dinner."),
    ),
    "nightlife": (
        ("Late start, cafe morning", "Demo slower morning so the evening can run later."),
        ("Sunset bar or rooftop", "Sample early-evening stop suited to a {group} group."),
        ("Live music district", "Demo nightlife block in {place}, still labelled as sample data."),
    ),
    "history": (
        ("Landmark morning", "Sample flagship historic site in {place}."),
        ("Heritage quarter", "Demo afternoon among older streets and monuments."),
        ("Storytelling walk", "Sample evening history walk or illuminated landmark visit."),
    ),
    "relaxation": (
        ("Slow breakfast", "Demo unhurried morning with extra buffer for a {pace} plan."),
        ("Spa, bath, or quiet garden", "Sample restorative afternoon in {place}."),
        ("Early dinner nearby", "Demo short travel evening so the group can rest."),
    ),
}

DAY_THEMES = [
    "Arrival and orientation",
    "Local food trail",
    "Culture and landmarks",
    "Nature and outdoors",
    "Neighborhood wandering",
    "Hidden gems",
    "Slow morning, lively evening",
]


def _split_amount(total: float, parts: int) -> list[float]:
    if parts <= 0:
        return [round(total, 2)]
    base = round(total / parts, 2)
    values = [base] * parts
    values[-1] = round(total - sum(values[:-1]), 2)
    return values


def _block_for(interest: str, slot: int) -> tuple[str, str]:
    blocks = INTEREST_BLOCKS.get(interest, INTEREST_BLOCKS["culture"])
    return blocks[slot]


def build_demo_itinerary(trip: TripRequest) -> Itinerary:
    interests = trip.interests or ["culture"]
    daily_budgets = _split_amount(trip.budget, trip.days)
    days: list[DayPlan] = []

    for index in range(trip.days):
        current = trip.start_date + timedelta(days=index)
        interest = interests[index % len(interests)]
        daily = daily_budgets[index]
        slot_costs = _split_amount(daily, 3)
        theme = DAY_THEMES[index % len(DAY_THEMES)]
        if index == 0:
            theme = f"Arrive in {trip.destination}"
        elif index == trip.days - 1 and trip.days > 1:
            theme = f"Last day in {trip.destination}"

        activities: list[Activity] = []
        for slot, time_of_day in enumerate(("morning", "afternoon", "evening")):
            title, description = _block_for(interest, slot)
            activities.append(
                Activity(
                    time_of_day=time_of_day,
                    title=title,
                    description=description.format(
                        place=trip.destination,
                        style=trip.travel_style,
                        pace=trip.pace,
                        group=trip.group_type,
                    ),
                    estimated_cost=slot_costs[slot],
                    location=trip.destination,
                )
            )

        days.append(
            DayPlan(
                day=index + 1,
                date=current.isoformat(),
                theme=theme,
                daily_budget=daily,
                activities=activities,
            )
        )

    interest_list = ", ".join(interests)
    return Itinerary(
        destination=trip.destination,
        summary=(
            f"DEMO itinerary for {trip.days} days in {trip.destination} "
            f"for {trip.travelers} {trip.group_type} traveler(s), focused on {interest_list}. "
            "This is sample content, not Gemini output."
        ),
        days=days,
        total_estimated_cost=round(sum(daily_budgets), 2),
        currency=trip.currency,
        tips=[
            "This plan is a labelled demo fallback because GEMINI_API_KEY is not set.",
            "Add a Google Gemini API key to generate a live personalized itinerary.",
            f"Stay near {trip.currency} {daily_budgets[0]:,.0f} per day to match the {trip.travel_style} budget.",
        ],
    )
