CREATE TABLE IF NOT EXISTS automation_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL UNIQUE,
    target_url VARCHAR(500) NOT NULL,
    cron_expression VARCHAR(50) NOT NULL,
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    description VARCHAR(255) NULL,
    steps_json JSON NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS automation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL,
    status ENUM('RUNNING','SUCCESS','FAILED') NOT NULL DEFAULT 'RUNNING',
    started_at DATETIME NOT NULL,
    finished_at DATETIME NULL,
    message TEXT NULL,
    INDEX idx_task_name (task_name),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Contoh task (nonaktif secara default, silakan edit URL & selector-nya sesuai web target).
-- Alurnya: isi username, isi password, klik tombol login, tunggu 2 detik, ambil screenshot.
INSERT INTO automation_tasks (task_name, target_url, cron_expression, enabled, description, steps_json) VALUES
('contoh_isi_form_login', 'https://example.com/login', '0 7 * * *', 0,
 'Contoh: isi username & password lalu klik tombol login',
 JSON_ARRAY(
   JSON_OBJECT('action','fill','selector_type','css','selector','#username','value','user_contoh'),
   JSON_OBJECT('action','fill','selector_type','css','selector','#password','value','password_contoh'),
   JSON_OBJECT('action','click','selector_type','css','selector','#login-button'),
   JSON_OBJECT('action','wait','seconds',2),
   JSON_OBJECT('action','screenshot')
 )
)
ON DUPLICATE KEY UPDATE task_name = task_name;
