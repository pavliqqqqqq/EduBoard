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
    teacher text default ''
);

alter table grades enable row level security;
alter table profiles enable row level security;

create policy student_sees_own_grades on grades for select
    using (student_id = auth.uid());

create policy teacher_inserts_grades on grades for insert
    with check (
        exists (select 1 from profiles p
                where p.id = auth.uid() and p.role = 'teacher'
                and p.class_id = (select class_id from profiles where id = student_id))
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