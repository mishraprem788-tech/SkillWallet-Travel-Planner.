-- Run this in the Supabase SQL editor once.

create extension if not exists "pgcrypto";

create table if not exists public.itineraries (
  id uuid primary key default gen_random_uuid(),
  destination text not null,
  start_date date not null,
  end_date date not null,
  budget numeric not null,
  currency text not null default 'INR',
  interests text[] not null default '{}',
  travel_style text not null,
  pace text not null,
  group_type text not null,
  travelers integer not null default 1,
  source text not null,
  itinerary jsonb not null,
  created_at timestamptz not null default now()
);

alter table public.itineraries enable row level security;
