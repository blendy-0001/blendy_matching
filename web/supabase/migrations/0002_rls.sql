-- RLS（Row Level Security）ポリシー
-- 方針: 自社データは本人(=その企業のユーザー)が編集可。他社は公開プロフィールのみ閲覧可。
-- 設計: docs/superpowers/specs/2026-06-22-rebuild-v2-design.md §3
--
-- NOTE: これは叩き。E1 で実データを入れながら検証・調整する。

-- 自分の company_id を返すヘルパ
create or replace function current_company_id()
returns uuid language sql stable as $$
  select company_id from users where id = auth.uid()
$$;

alter table companies enable row level security;
alter table users enable row level security;
alter table company_profiles enable row level security;
alter table company_attributes enable row level security;
alter table swipes enable row level security;
alter table matches enable row level security;
alter table meetings enable row level security;
alter table profile_update_proposals enable row level security;
alter table sales_notes enable row level security;
alter table profile_sources enable row level security;

-- companies: 全ログインユーザーが閲覧可（スワイプ候補表示のため）。更新は自社のみ。
create policy companies_select on companies for select to authenticated using (true);
create policy companies_update on companies for update to authenticated
  using (id = current_company_id());

-- users: 自分の行のみ
create policy users_self on users for all to authenticated
  using (id = auth.uid()) with check (id = auth.uid());

-- company_profiles / attributes: 閲覧は全員、更新は自社のみ
create policy profiles_select on company_profiles for select to authenticated using (true);
create policy profiles_write on company_profiles for all to authenticated
  using (company_id = current_company_id()) with check (company_id = current_company_id());

create policy attrs_select on company_attributes for select to authenticated using (true);
create policy attrs_write on company_attributes for all to authenticated
  using (company_id = current_company_id()) with check (company_id = current_company_id());

-- swipes: 自社が行った swipe のみ
create policy swipes_own on swipes for all to authenticated
  using (swiper_company_id = current_company_id())
  with check (swiper_company_id = current_company_id());

-- matches: 自社が当事者のもののみ閲覧
create policy matches_party on matches for select to authenticated
  using (company_a_id = current_company_id() or company_b_id = current_company_id());

-- meetings / proposals / sales_notes / sources: 自社のもののみ
create policy meetings_own on meetings for all to authenticated
  using (uploaded_by_company_id = current_company_id())
  with check (uploaded_by_company_id = current_company_id());

create policy proposals_own on profile_update_proposals for all to authenticated
  using (company_id = current_company_id()) with check (company_id = current_company_id());

create policy sales_notes_own on sales_notes for all to authenticated
  using (company_id = current_company_id()) with check (company_id = current_company_id());

create policy sources_own on profile_sources for all to authenticated
  using (company_id = current_company_id()) with check (company_id = current_company_id());
