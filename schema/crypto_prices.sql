create table crypto_prices (
    id uuid default gen_random_uuid() primary key,
    created_at timestamp not null default now(),
    coin varchar(255) not null,
    open double precision not null,
    high double precision not null,
    low double precision not null,
    close double precision not null,
    date timestamp not null,
    vol_fiat double precision not null,
    volume double precision not null
);