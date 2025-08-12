import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_API;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Supabase URL and API Key are required. Please check your .env file.");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
