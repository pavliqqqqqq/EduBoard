create table profiles (
    id uuid primary key references auth.users(id),
    full_name text not null,
    role text not null check (role in ('teacher', 'student')),
    class_id text
);

create table grades (
    id uuid primary key default gen_random_uuid(),
    student_id uuid references profiles(id),
    subject text not null,
    value int not null check (value between 1 and 5),
    weight int not null default 1,
    note text default '',
    created_by uuid references profiles(id)
);

create table schedule (
    id uuid primary key default gen_random_uuid(),
    class_id text not null,
    day int not null,
    period int not null,
    subject text not null,
    room text default '',
    teacher text default '',
    unique (class_id, day, period)  -- nutné pro upsert při úpravě rozvrhu
);

create table subjects (
    id uuid primary key default gen_random_uuid(),
    class_id text not null,
    name text not null,
    unique (class_id, name)  -- nutné pro upsert při přidání nového předmětu
);

create table messages (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references profiles(id),   -- identifikuje vlákno (žák <-> jeho učitel)
    sender_id uuid not null references profiles(id),
    sender_name text not null,
    content text not null,   -- ŠIFROVANÝ obsah (Fernet, viz crypto.py) - server nikdy nevidí čitelný text
    created_at timestamptz not null default now()
);

alter table grades enable row level security;
alter table profiles enable row level security;
alter table schedule enable row level security;
alter table subjects enable row level security;
alter table messages enable row level security;

create policy student_sees_own_grades on grades for select
    using (student_id = auth.uid());

create policy teacher_inserts_grades on grades for insert
    with check (
        exists (select 1 from profiles p
                where p.id = auth.uid() and p.role = 'teacher'
                and p.class_id = (select class_id from profiles where id = student_id))
    );

-- rozvrh a seznam předmětů vidí všichni přihlášení žáci/učitelé dané třídy
create policy class_sees_schedule on schedule for select
    using (exists (select 1 from profiles p where p.id = auth.uid() and p.class_id = schedule.class_id));

create policy class_sees_subjects on subjects for select
    using (exists (select 1 from profiles p where p.id = auth.uid() and p.class_id = subjects.class_id));

-- upravovat rozvrh a přidávat předměty může jen učitel dané třídy
create policy teacher_manages_schedule on schedule for all
    using (exists (select 1 from profiles p
                   where p.id = auth.uid() and p.role = 'teacher' and p.class_id = schedule.class_id))
    with check (exists (select 1 from profiles p
                        where p.id = auth.uid() and p.role = 'teacher' and p.class_id = schedule.class_id));

create policy teacher_manages_subjects on subjects for all
    using (exists (select 1 from profiles p
                   where p.id = auth.uid() and p.role = 'teacher' and p.class_id = subjects.class_id))
    with check (exists (select 1 from profiles p
                        where p.id = auth.uid() and p.role = 'teacher' and p.class_id = subjects.class_id));

-- zprávy vidí žák (svoje vlákno) a učitel dané třídy (vlákna svých žáků)
create policy sees_own_thread_messages on messages for select
    using (
        student_id = auth.uid()
        or exists (
            select 1 from profiles p
            where p.id = auth.uid() and p.role = 'teacher'
            and p.class_id = (select class_id from profiles where id = messages.student_id)
        )
    );

-- posílat smí jen sám za sebe (sender_id = auth.uid()), a to buď žák do
-- svého vlákna, nebo učitel dané třídy do vlákna svého žáka
create policy sends_own_thread_messages on messages for insert
    with check (
        sender_id = auth.uid()
        and (
            student_id = auth.uid()
            or exists (
                select 1 from profiles p
                where p.id = auth.uid() and p.role = 'teacher'
                and p.class_id = (select class_id from profiles where id = messages.student_id)
            )
        )
    );

create or replace function get_student_grades_with_average(p_student_id uuid)
returns table(id uuid, subject text, value int, weight int, note text, weighted_average numeric)
language plpgsql security definer as $$
begin
    return query
    select g.id, g.subject, g.value, g.weight, g.note,
        (select round(sum(g2.value::numeric * g2.weight) / nullif(sum(g2.weight), 0), 2)
         from grades g2 where g2.student_id = p_student_id)
    from grades g
    where g.student_id = p_student_id
    order by g.subject;
end;
$$;