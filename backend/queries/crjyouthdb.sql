CREATE DATABASE crjyouthdb;
CREATE USER crjyouthuser WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE crjyouthdb TO crjyouthuser;

-- Login to database
-- psql -U crjyouthuser -d crjyouthdb -h 127.0.0.1


-- Library roles table
CREATE TABLE user_roles (
    rank INT PRIMARY KEY,              -- Rank of the role, serves as unique identifier
    role VARCHAR(50) NOT NULL,         -- Role name (e.g., Admin, Moderator, Member)
    permissions TEXT[] NOT NULL        -- Permissions stored as an array of strings
);

INSERT INTO user_roles (rank, role, permissions)
VALUES 
(1, 'Admin', ARRAY['add_book', 'edit_book', 'delete_book', 'approve_lending', 'manage_users']),
(2, 'Moderator', ARRAY['approve_lending', 'manage_threads', 'resolve_issues']),
(3, 'Member', ARRAY['borrow_book', 'return_book', 'suggest_book', 'participate_threads']);



-- Library users table
CREATE TABLE users (
    user_id VARCHAR(10) PRIMARY KEY,          -- Unique user ID
    first_name VARCHAR(100) NOT NULL,         -- User's first name
    last_name VARCHAR(100) NOT NULL,          -- User's last name
    email VARCHAR(150) UNIQUE NOT NULL,       -- User's email (must be unique)
    phone_number VARCHAR(10) UNIQUE,          -- User's phone number (must be unique)
    registration_date TIMESTAMP NOT NULL,     -- Date of registration
    role INT NOT NULL DEFAULT 3,              -- User role (e.g., "Admin":1, "Moderator":2, "User":3)
    max_books_allowed INT NOT NULL,           -- Max number of books user can borrow
    borrowed_books JSONB DEFAULT '[]',        -- List of borrowed books (stored as JSON)
    fines_due NUMERIC(10, 2) DEFAULT 0.0,     -- Fines due, with 2 decimal precision
    is_active BOOLEAN DEFAULT TRUE,           -- Active status of the user
    password VARCHAR(255) NOT NULL            -- Hashed password
);

INSERT INTO users (
    user_id, first_name, last_name, email, phone_number, 
    registration_date, role, max_books_allowed, borrowed_books, fines_due, 
    is_active, password
) VALUES (
    'U001', 'John', 'Doe', 'john.doe@example.com', '1234567890', 
    NOW(), 3, 5, '[]', 0.0, 
    TRUE, 'fjfyrdgvvhgv45354cfgfcg'
);

