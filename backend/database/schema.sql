-- Create database if not exists (Only for MySQL)
-- CREATE DATABASE IF NOT EXISTS traveller_db;
-- USE traveller_db;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'User'
);

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50),
    details TEXT
);

-- Destinations Table
CREATE TABLE IF NOT EXISTS destinations (
    destination_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    city_name VARCHAR(100) UNIQUE NOT NULL,
    country VARCHAR(100) NOT NULL,
    rating FLOAT DEFAULT 4.0,
    description TEXT
);

-- Tourist Places Table
CREATE TABLE IF NOT EXISTS tourist_places (
    place_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    destination_id INT,
    place_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    rating FLOAT DEFAULT 4.0,
    latitude DOUBLE,
    longitude DOUBLE,
    address VARCHAR(255),
    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE CASCADE
);

-- Flights Table
CREATE TABLE IF NOT EXISTS flights (
    flight_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    airline VARCHAR(100) NOT NULL,
    source_city VARCHAR(100) NOT NULL,
    destination_city VARCHAR(100) NOT NULL,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

-- Bookings Table
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    flight_id INT NOT NULL,
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Confirmed',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id) ON DELETE CASCADE
);
