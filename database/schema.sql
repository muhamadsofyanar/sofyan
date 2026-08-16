CREATE TABLE IF NOT EXISTS projects (
 id SERIAL PRIMARY KEY,
 name TEXT NOT NULL,
 status TEXT DEFAULT 'active',
 created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
 id SERIAL PRIMARY KEY,
 title TEXT NOT NULL,
 status TEXT DEFAULT 'inbox',
 task_type TEXT,
 priority TEXT DEFAULT 'medium',
 due_date DATE,
 project_id INTEGER REFERENCES projects(id),
 created_at TIMESTAMP DEFAULT NOW(),
 completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
 id SERIAL PRIMARY KEY,
 task_id INTEGER REFERENCES tasks(id),
 action TEXT,
 created_at TIMESTAMP DEFAULT NOW()
);
