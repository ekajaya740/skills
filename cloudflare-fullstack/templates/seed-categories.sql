-- Seed: Default categories for Money Manager
-- Usage: psql "$DATABASE_URL" -f seed/001_categories.sql
INSERT INTO categories (id, name, type, icon, color, sort_order) VALUES
  -- Income categories
  (gen_random_uuid(), 'Salary', 'income', '💼', '#22c55e', 1),
  (gen_random_uuid(), 'Freelance', 'income', '💻', '#3b82f6', 2),
  (gen_random_uuid(), 'Investment', 'income', '📈', '#8b5cf6', 3),
  (gen_random_uuid(), 'Gift', 'income', '🎁', '#f59e0b', 4),
  -- Expense categories
  (gen_random_uuid(), 'Food', 'expense', '🍔', '#ef4444', 1),
  (gen_random_uuid(), 'Transport', 'expense', '🚗', '#f97316', 2),
  (gen_random_uuid(), 'Entertainment', 'expense', '🎮', '#ec4899', 3),
  (gen_random_uuid(), 'Shopping', 'expense', '🛍️', '#6366f1', 4),
  (gen_random_uuid(), 'Bills', 'expense', '📄', '#14b8a6', 5),
  (gen_random_uuid(), 'Health', 'expense', '🏥', '#06b6d4', 6),
  (gen_random_uuid(), 'Education', 'expense', '📚', '#a855f7', 7),
  -- Transfer category
  (gen_random_uuid(), 'Transfer', 'transfer', '🔄', '#64748b', 1)
ON CONFLICT DO NOTHING;