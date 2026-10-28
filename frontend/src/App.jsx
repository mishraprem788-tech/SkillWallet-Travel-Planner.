import { useEffect, useMemo, useState } from "react";
import { fetchStatus, generateItinerary } from "./api";
import { buildLocalDemo } from "./demo";

const INTERESTS = [
  "food",
  "culture",
  "nature",
  "adventure",
  "shopping",
  "nightlife",
  "history",
  "relaxation",
];

function toLocalISODate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isoPlus(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return toLocalISODate(date);
}

function dayCount(start, end) {
  const from = new Date(`${start}T00:00:00`);
  const to = new Date(`${end}T00:00:00`);
  return Math.round((to - from) / 86400000) + 1;
}

const initialForm = {
  destination: "",
  start_date: isoPlus(14),
  end_date: isoPlus(16),
  budget: "30000",
  currency: "INR",
  interests: ["food", "culture"],
  travel_style: "mid-range",
  pace: "moderate",
  group_type: "solo",
  travelers: "1",
};

function validate(form) {
  const errors = {};
  if (form.destination.trim().length < 2) {
    errors.destination = "Enter a destination (at least 2 characters).";
  }
  if (!form.start_date) errors.start_date = "Start date is required.";
  if (!form.end_date) errors.end_date = "End date is required.";
  if (form.start_date && form.end_date && form.end_date < form.start_date) {
    errors.end_date = "End date must be on or after the start date.";
  }
  const today = isoPlus(0);
  if (form.start_date && form.start_date < today) {
    errors.start_date = "Start date cannot be in the past.";
  }
  if (form.start_date && form.end_date && dayCount(form.start_date, form.end_date) > 14) {
    errors.end_date = "Trips can be at most 14 days.";
  }
  const budget = Number(form.budget);
  if (!Number.isFinite(budget) || budget <= 0) {
    errors.budget = "Budget must be greater than 0.";
  }
  if (form.interests.length < 1) {
    errors.interests = "Select at least one interest.";
  }
  const travelers = Number(form.travelers);
  if (!Number.isInteger(travelers) || travelers < 1 || travelers > 12) {
    errors.travelers = "Travelers must be between 1 and 12.";
  }
  return errors;
}

export default function App() {
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState(null);
  const [statusError, setStatusError] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetchStatus()
      .then((data) => {
        setStatus(data);
        setStatusError("");
      })
      .catch(() => {
        setStatusError("Backend is offline. You can still try the planner in local demo mode; live AI and cloud saving need the backend.");
      });
  }, []);

  const field = (name) => (event) => {
    setForm((prev) => ({ ...prev, [name]: event.target.value }));
  };

  const toggleInterest = (interest) => {
    setForm((prev) => {
      const exists = prev.interests.includes(interest);
      return {
        ...prev,
        interests: exists
          ? prev.interests.filter((item) => item !== interest)
          : [...prev.interests, interest],
      };
    });
  };

  async function onSubmit(event) {
    event.preventDefault();
    const nextErrors = validate(form);
    setErrors(nextErrors);
    setSubmitError("");
    if (Object.keys(nextErrors).length) return;

    setLoading(true);
    setResult(null);
    try {
      const payload = {
        ...form,
        destination: form.destination.trim(),
        budget: Number(form.budget),
        travelers: Number(form.travelers),
      };
      const data = await generateItinerary(payload);
      setResult(data);
    } catch (error) {
      if (
        error.message?.includes("Cannot reach the API") ||
        error.message?.includes("request timed out")
      ) {
        setResult(buildLocalDemo({
          ...form,
          destination: form.destination.trim(),
          budget: Number(form.budget),
          travelers: Number(form.travelers),
        }));
        setStatusError("Backend is offline. Showing a local demo plan; it has not been saved and does not use live AI.");
      } else {
        setSubmitError(error.message || "Could not generate itinerary.");
      }
    } finally {
      setLoading(false);
    }
  }

  const itinerary = result?.itinerary;
  const isDemo = result?.source === "demo" || status?.using_demo_fallback;
  const noticeText = useMemo(() => (result?.notices || []).join(" "), [result]);

  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">SkillWallet</p>
        <h1>Personalized Travel Itinerary Planner</h1>
        <p className="lede">
          Enter your destination, dates, budget, and interests. Get a day-by-day plan
          from Gemini, or a clearly labelled demo if no API key is configured.
        </p>
      </header>

      {statusError ? <div className="banner warning">{statusError}</div> : null}
      {status && !status.gemini_configured ? (
        <div className="banner demo">
          DEMO MODE: Gemini is not configured. Generated plans will be sample data until
          you set GEMINI_API_KEY in backend/.env.
        </div>
      ) : null}
      {status && status.gemini_configured ? (
        <div className="banner ok">Gemini is configured. Live AI generation is enabled.</div>
      ) : null}
      {status && !status.supabase_configured ? (
        <div className="banner muted">
          Supabase is not configured. Plans will generate but will not be saved.
        </div>
      ) : null}

      <main className="layout">
        <form className="card form" onSubmit={onSubmit} noValidate>
          <h2>Trip details</h2>

          <label>
            Destination
            <input
              value={form.destination}
              onChange={field("destination")}
              placeholder="Kyoto, Japan"
            />
            {errors.destination ? <span className="error">{errors.destination}</span> : null}
          </label>

          <div className="row">
            <label>
              Start date
              <input
                type="date"
                min={isoPlus(0)}
                value={form.start_date}
                onChange={field("start_date")}
              />
              {errors.start_date ? <span className="error">{errors.start_date}</span> : null}
            </label>
            <label>
              End date
              <input
                type="date"
                min={form.start_date || isoPlus(0)}
                value={form.end_date}
                onChange={field("end_date")}
              />
              {errors.end_date ? <span className="error">{errors.end_date}</span> : null}
            </label>
          </div>

          <div className="row">
            <label>
              Total budget
              <input type="number" min="1" value={form.budget} onChange={field("budget")} />
              {errors.budget ? <span className="error">{errors.budget}</span> : null}
            </label>
            <label>
              Currency
              <select value={form.currency} onChange={field("currency")}>
                <option value="INR">INR</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </label>
          </div>

          <div className="row">
            <label>
              Travel style
              <select value={form.travel_style} onChange={field("travel_style")}>
                <option value="budget">Budget</option>
                <option value="mid-range">Mid-range</option>
                <option value="luxury">Luxury</option>
              </select>
            </label>
            <label>
              Pace
              <select value={form.pace} onChange={field("pace")}>
                <option value="relaxed">Relaxed</option>
                <option value="moderate">Moderate</option>
                <option value="packed">Packed</option>
              </select>
            </label>
          </div>

          <div className="row">
            <label>
              Who is going
              <select value={form.group_type} onChange={field("group_type")}>
                <option value="solo">Solo</option>
                <option value="couple">Couple</option>
                <option value="family">Family</option>
                <option value="friends">Friends</option>
              </select>
            </label>
            <label>
              Travelers
              <input
                type="number"
                min="1"
                max="12"
                value={form.travelers}
                onChange={field("travelers")}
              />
              {errors.travelers ? <span className="error">{errors.travelers}</span> : null}
            </label>
          </div>

          <fieldset>
            <legend>Interests</legend>
            <div className="chips">
              {INTERESTS.map((interest) => (
                <label key={interest} className="chip">
                  <input
                    type="checkbox"
                    checked={form.interests.includes(interest)}
                    onChange={() => toggleInterest(interest)}
                  />
                  {interest}
                </label>
              ))}
            </div>
            {errors.interests ? <span className="error">{errors.interests}</span> : null}
          </fieldset>

          {submitError ? <div className="banner warning">{submitError}</div> : null}

          <button type="submit" disabled={loading}>
            {loading ? "Generating itinerary…" : "Generate itinerary"}
          </button>
        </form>

        <section className="card results">
          {!result && !loading ? (
            <div className="empty">
              Your day-by-day itinerary will appear here after you submit the form.
            </div>
          ) : null}
          {loading ? <div className="empty">Building a plan for your dates and budget…</div> : null}
          {itinerary ? (
            <>
              <div className={`badge ${isDemo ? "demo" : "live"}`}>
                {result.source === "gemini" ? "Live Gemini itinerary" : "DEMO FALLBACK itinerary"}
              </div>
              {noticeText ? <p className="notices">{noticeText}</p> : null}
              <h2>{itinerary.destination}</h2>
              <p>{itinerary.summary}</p>
              <p className="cost">
                Estimated total: {itinerary.currency} {Number(itinerary.total_estimated_cost).toLocaleString()}
                {result.saved ? " · Saved to Supabase" : " · Not saved"}
              </p>
              <button
                type="button"
                className="secondary-button"
                onClick={() => {
                  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
                  const url = URL.createObjectURL(blob);
                  const link = document.createElement("a");
                  link.href = url;
                  link.download = `${itinerary.destination.trim().replace(/[^a-z0-9]+/gi, "-").toLowerCase()}-itinerary.json`;
                  link.click();
                  URL.revokeObjectURL(url);
                }}
              >
                Download itinerary (JSON)
              </button>
              <div className="days">
                {itinerary.days.map((day) => (
                  <article key={`${day.day}-${day.date}`} className="day">
                    <header>
                      <h3>
                        Day {day.day} · {day.date}
                      </h3>
                      <p>{day.theme}</p>
                    </header>
                    <ul>
                      {day.activities.map((activity) => (
                        <li key={`${activity.time_of_day}-${activity.title}`}>
                          <strong>{activity.time_of_day}</strong> · {activity.title}
                          <span>{activity.description}</span>
                          <em>
                            {itinerary.currency} {activity.estimated_cost}
                            {activity.location ? ` · ${activity.location}` : ""}
                          </em>
                        </li>
                      ))}
                    </ul>
                  </article>
                ))}
              </div>
              {itinerary.tips?.length ? (
                <ul className="tips">
                  {itinerary.tips.map((tip) => (
                    <li key={tip}>{tip}</li>
                  ))}
                </ul>
              ) : null}
            </>
          ) : null}
        </section>
      </main>
    </div>
  );
}
