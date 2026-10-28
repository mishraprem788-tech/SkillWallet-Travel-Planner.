const activityTemplates = {
  food: ["Local breakfast café", "Regional food market", "Local dinner favourite"],
  culture: ["Historic district walk", "Museum or cultural site", "Local performance or evening market"],
  nature: ["City park or waterfront", "Garden or scenic viewpoint", "Sunset lookout"],
  adventure: ["Outdoor adventure", "Hands-on local experience", "Evening neighbourhood walk"],
  shopping: ["Independent local shops", "Main market visit", "Souvenir and craft stop"],
  nightlife: ["Relaxed café morning", "Rooftop or sunset viewpoint", "Live music district"],
  history: ["Historic landmark", "Heritage quarter", "Guided history walk"],
  relaxation: ["Slow breakfast", "Quiet garden or wellness break", "Easy dinner near your stay"],
};

function localDatePlus(start, offset) {
  const date = new Date(`${start}T12:00:00`);
  date.setDate(date.getDate() + offset);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

export function buildLocalDemo(trip) {
  const start = trip.start_date;
  const end = trip.end_date;
  const daysCount = Math.max(1, Math.round((new Date(`${end}T12:00:00`) - new Date(`${start}T12:00:00`)) / 86400000) + 1);
  const budget = Number(trip.budget);
  const perDay = budget / daysCount;
  const interests = trip.interests?.length ? trip.interests : ["culture"];
  const slots = ["morning", "afternoon", "evening"];
  const days = Array.from({ length: daysCount }, (_, index) => {
    const interest = interests[index % interests.length];
    const titles = activityTemplates[interest] || activityTemplates.culture;
    const activityCost = perDay / 3;
    return {
      day: index + 1,
      date: localDatePlus(start, index),
      theme: index === 0 ? `Arrival and orientation in ${trip.destination}` : index === daysCount - 1 ? `Final day in ${trip.destination}` : `${interest[0].toUpperCase()}${interest.slice(1)} and local discovery`,
      daily_budget: Number(perDay.toFixed(2)),
      activities: slots.map((time_of_day, slot) => ({
        time_of_day,
        title: titles[slot],
        description: `Sample ${time_of_day} idea for a ${trip.travel_style} ${trip.pace} trip in ${trip.destination}. Check current opening hours, travel time, and prices before visiting.`,
        estimated_cost: Number(activityCost.toFixed(2)),
        location: trip.destination,
      })),
    };
  });
  return {
    source: "demo",
    saved: false,
    itinerary_id: null,
    notices: ["LOCAL DEMO: The API could not be reached, so this sample plan was created in your browser. Connect the FastAPI backend and Gemini key for live AI generation."],
    itinerary: {
      destination: trip.destination,
      summary: `A ${daysCount}-day sample itinerary for ${trip.travelers} ${trip.group_type} traveller(s), based on your selected interests: ${interests.join(", ")}.`,
      days,
      total_estimated_cost: budget,
      currency: trip.currency,
      tips: [
        "This is a sample plan, not verified live travel information.",
        "Confirm opening hours, transport, safety guidance, and prices before booking.",
        `Budget target: ${trip.currency} ${perDay.toFixed(2)} per day.`,
      ],
    },
  };
}
