CREATE DATABASE carpooling;

\c carpooling;


CREATE TABLE users (id SERIAL PRIMARY KEY,
                                      username VARCHAR(50) UNIQUE NOT NULL,
                                                                  first_name VARCHAR(50) NOT NULL,
                                                                                         last_name VARCHAR(50) NOT NULL,
                                                                                                               hashed_password VARCHAR(255) NOT NULL,
                                                                                                                                            email VARCHAR(100) UNIQUE NOT NULL);


CREATE TABLE routes
    (id SERIAL PRIMARY KEY,
                       user_id INT REFERENCES users(id) ON DELETE CASCADE,
                                                                  start_point VARCHAR(255) NOT NULL,
                                                                                           end_point VARCHAR(255) NOT NULL);


CREATE TABLE trips
    (id SERIAL PRIMARY KEY,
                       route_id INT REFERENCES routes(id) ON DELETE CASCADE,
                                                                    driver_id INT REFERENCES users(id) ON DELETE CASCADE,
                                                                                                                 passengers INT[] DEFAULT ARRAY[]::INT[], date TIMESTAMP NOT NULL);

-- Индексы

CREATE INDEX idx_users_username ON users(username);


CREATE INDEX idx_users_first_name ON users(first_name);


CREATE INDEX idx_users_last_name ON users(last_name);


CREATE INDEX idx_routes_user_id ON routes(user_id);


CREATE INDEX idx_trips_route_id ON trips(route_id);


CREATE INDEX idx_trips_driver_id ON trips(driver_id);

-- Вставка тестовых данных в таблицу users

INSERT INTO users (username, first_name, last_name, hashed_password, email)
VALUES ('user1',
        'John',
        'Doe',
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
        'john.doe@example.com'), ('user2',
                                  'Jane',
                                  'Smith',
                                  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
                                  'jane.smith@example.com');

-- Вставка тестовых данных в таблицу routes

INSERT INTO routes (user_id, start_point, end_point)
VALUES (1,
        'Point A',
        'Point B'), (2,
                     'Point C',
                     'Point D');

-- Вставка тестовых данных в таблицу trips

INSERT INTO trips (route_id, driver_id, passengers, date)
VALUES (1,
        1, ARRAY[2], '2023-10-01 10:00:00'), (2,
                                              2, ARRAY[1], '2023-10-02 12:00:00');