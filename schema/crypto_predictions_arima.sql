create table crypto_predictions_arima (
    id int not null primary key generated always as identity,
    created_at timestamp not null default now(),
    last_close double precision not null,
    next_day_price double precision not null,
    seven_day_price double precision not null,
    coin varchar(255) not null,
    last_timestamp_reported timestamp not null,
    p int,
    d int,
    q int
);