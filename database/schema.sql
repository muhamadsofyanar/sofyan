CREATE TABLE projects (
 id SERIAL PRIMARY KEY,
 name TEXT NOT NULL,
 status VARCHAR(30) DEFAULT 'active',
 created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tasks (
 id SERIAL PRIMARY KEY,
 title TEXT NOT NULL,
 status VARCHAR(30) DEFAULT 'inbox',
 priority VARCHAR(20),
 due_date DATE,
 project_id INTEGER REFERENCES projects(id),
 created_at TIMESTAMP DEFAULT NOW(),
 completed_at TIMESTAMP
);

CREATE TABLE activity_logs (
 id SERIAL PRIMARY KEY,
 task_id INTEGER REFERENCES tasks(id),
 action TEXT,
 created_at TIMESTAMP DEFAULT NOW()
);
