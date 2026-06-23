-- Blendy v2 初期スキーマ（Supabase Postgres）
-- 設計: docs/superpowers/specs/2026-06-22-rebuild-v2-design.md §3
--
-- 適用方法（例）:
--   supabase db push          （Supabase CLI）
--   または Supabase ダッシュボードの SQL Editor に貼り付け

-- ── companies ─────────────────────────────────
create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  industry text not null,
  officer_count int,
  employee_count int,
  revenue_scale text,           -- 任意
  website_url text,
  created_at timestamptz not null default now()
);

-- ── users（Supabase Auth と 1:1。1アカウント=1企業）──
create table if not exists users (
  id uuid primary key references auth.users(id) on delete cascade,
  company_id uuid not null unique references companies(id) on delete cascade,
  full_name text not null,
  role_title text not null,
  email text not null,
  created_at timestamptz not null default now()
);

-- ── company_profiles（編集可能な叩き）──────────
create table if not exists company_profiles (
  company_id uuid primary key references companies(id) on delete cascade,
  summary text default '',
  value_prop text default '',
  strengths text default '',
  challenges text default '',
  target_market text default '',
  is_edited boolean not null default false,
  updated_at timestamptz not null default now()
);

-- ── profile_sources（プロフィール生成の入力素材）──
create table if not exists profile_sources (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  type text not null check (type in ('website','pdf')),
  url text,
  storage_path text,
  extracted_text text,
  created_at timestamptz not null default now()
);

-- ── company_attributes（L2/L3・ランキング用）────
create table if not exists company_attributes (
  company_id uuid primary key references companies(id) on delete cascade,
  activities text[] not null default '{}',
  decision_style text check (decision_style in ('即決派','バランス型','慎重派')),
  time_horizon text check (time_horizon in ('長期','中期','短期')),
  commitment_level int check (commitment_level between 1 and 5),
  collaboration_style text check (collaboration_style in ('個人主義','バランス','協調志向')),
  past_collaboration text check (past_collaboration in ('なし','1-2回','3回以上'))
);

-- ── swipes ────────────────────────────────────
create table if not exists swipes (
  id uuid primary key default gen_random_uuid(),
  swiper_company_id uuid not null references companies(id) on delete cascade,
  target_company_id uuid not null references companies(id) on delete cascade,
  direction text not null check (direction in ('like','pass')),
  created_at timestamptz not null default now(),
  unique (swiper_company_id, target_company_id)
);

-- ── matches（相互Likeで生成。a<b で正規化）──────
create table if not exists matches (
  id uuid primary key default gen_random_uuid(),
  company_a_id uuid not null references companies(id) on delete cascade,
  company_b_id uuid not null references companies(id) on delete cascade,
  created_at timestamptz not null default now(),
  check (company_a_id < company_b_id),
  unique (company_a_id, company_b_id)
);

-- ── meetings（商談議事録）─────────────────────
create table if not exists meetings (
  id uuid primary key default gen_random_uuid(),
  match_id uuid references matches(id) on delete set null,
  minutes_text text not null,
  uploaded_by_company_id uuid not null references companies(id) on delete cascade,
  created_at timestamptz not null default now()
);

-- ── profile_update_proposals（提案→承認）───────
create table if not exists profile_update_proposals (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid references meetings(id) on delete cascade,
  company_id uuid not null references companies(id) on delete cascade,
  changes jsonb not null,         -- FieldChange[] / salesInfo
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  prompt_version text,
  created_at timestamptz not null default now(),
  applied_at timestamptz
);

-- ── sales_notes（議事録で育つ営業情報）──────────
create table if not exists sales_notes (
  company_id uuid primary key references companies(id) on delete cascade,
  content text default '',
  updated_at timestamptz not null default now()
);

-- インデックス
create index if not exists idx_swipes_target on swipes(target_company_id);
create index if not exists idx_proposals_company on profile_update_proposals(company_id, status);
