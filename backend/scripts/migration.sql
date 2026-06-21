-- 1. Add new enum value for 'universal' room (Already completed successfully)
-- ALTER TYPE roomtype ADD VALUE IF NOT EXISTS 'universal';

-- 2. Insert new rooms with generated UUIDs and default values
INSERT INTO rooms (id, name, type, is_active, created_at)
SELECT gen_random_uuid(), 'Owners', 'founder'::roomtype, true, now()
WHERE NOT EXISTS (SELECT 1 FROM rooms WHERE name = 'Owners');

INSERT INTO rooms (id, name, type, is_active, created_at)
SELECT gen_random_uuid(), 'IT Team', 'department'::roomtype, true, now()
WHERE NOT EXISTS (SELECT 1 FROM rooms WHERE name = 'IT Team');

INSERT INTO rooms (id, name, type, is_active, created_at)
SELECT gen_random_uuid(), 'Universal', 'universal'::roomtype, true, now()
WHERE NOT EXISTS (SELECT 1 FROM rooms WHERE name = 'Universal');
