from dataclasses import dataclass

class QueryConfig:
    """
    Contains configuration settings for whole project.
    """
    @dataclass(frozen=True)
    class SupabaseQueries:
        """
            Supabase table queries
        """
        checkIfTableExists: str = (
            "SELECT EXISTS ("
            "SELECT FROM information_schema.tables "
            "WHERE table_name = %s"
            ");"
        )

        getCreateTablesSQL: str = (
            """
            -- Helper function to execute SQL from client
            create or replace function execute_sql(query text)
            returns void
            language plpgsql
            security definer
            as $$
            begin
            execute query;
            end;
            $$;

            -- 1. Users Table
            create table if not exists users (
            id uuid default gen_random_uuid() primary key,
            email text unique not null,
            password_hash text not null,
            role text not null default 'user',
            created_at timestamp with time zone default timezone('utc'::text, now()) not null
            );

            -- 2. Account Plans Table
            create table if not exists account_plans (
            id uuid default gen_random_uuid() primary key,
            user_id uuid references users(id),
            company text not null,
            sections jsonb default '{}'::jsonb,
            created_at timestamp with time zone default timezone('utc'::text, now()) not null,
            updated_at timestamp with time zone default timezone('utc'::text, now()) not null
            );

            -- 3. Research Data Table
            create table if not exists research_data (
            id uuid default gen_random_uuid() primary key,
            user_id uuid references users(id),
            company text not null,
            content jsonb default '{}'::jsonb,
            plan_id uuid references account_plans(id),
            created_at timestamp with time zone default timezone('utc'::text, now()) not null
            );

            -- 4. Conversations Table (Chat History)
            create table if not exists conversations (
                id uuid default gen_random_uuid() primary key,
                user_id uuid references users(id) not null,
                title text,
                created_at timestamp with time zone default timezone('utc'::text, now()) not null,
                updated_at timestamp with time zone default timezone('utc'::text, now()) not null
            );

            -- 5. Messages Table
            create table if not exists messages (
                id uuid default gen_random_uuid() primary key,
                conversation_id uuid references conversations(id) on delete cascade not null,
                role text not null, -- 'user' or 'assistant'
                content text not null,
                created_at timestamp with time zone default timezone('utc'::text, now()) not null
            );

            -- Enable RLS (Optional for now, but good practice)
            alter table users enable row level security;
            alter table account_plans enable row level security;
            alter table research_data enable row level security;
            alter table conversations enable row level security;
            alter table messages enable row level security;

            -- Public Access Policies (MVP)
            create policy "Public Access Users" on users for all using (true) with check (true);
            create policy "Public Access Plans" on account_plans for all using (true) with check (true);
            create policy "Public Access Research" on research_data for all using (true) with check (true);
            create policy "Public Access Conversations" on conversations for all using (true) with check (true);
            create policy "Public Access Messages" on messages for all using (true) with check (true);

            """
        )