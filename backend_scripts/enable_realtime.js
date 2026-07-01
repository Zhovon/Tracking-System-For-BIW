const { Client } = require('pg');
require('dotenv').config({ path: '../backend/.env' });

async function enableRealtime() {
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) {
    console.error("DATABASE_URL not found in ../backend/.env");
    process.exit(1);
  }

  const client = new Client({
    connectionString,
    ssl: { rejectUnauthorized: false }
  });

  try {
    await client.connect();
    console.log("Connected to database successfully.");

    const tables = ['tickets', 'messages', 'notifications'];
    for (const table of tables) {
      try {
        await client.query(`ALTER PUBLICATION supabase_realtime ADD TABLE ${table};`);
        console.log(`Successfully added ${table} to supabase_realtime publication.`);
      } catch (err) {
        if (err.message.includes('already added') || err.message.includes('already a member')) {
          console.log(`${table} is already in the supabase_realtime publication.`);
        } else if (err.message.includes('does not exist')) {
          console.log(`Publication supabase_realtime might not exist. Creating it...`);
          await client.query(`CREATE PUBLICATION supabase_realtime FOR ALL TABLES;`);
          console.log(`Created supabase_realtime publication.`);
          break; // Since we created it for ALL tables, no need to add individually
        } else {
          console.error(`Warning for ${table}:`, err.message);
        }
      }
    }
  } catch (error) {
    console.error("Error connecting to database:", error.message);
  } finally {
    await client.end();
  }
}

enableRealtime();
