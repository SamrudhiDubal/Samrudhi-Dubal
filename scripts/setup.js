// One-time project setup: installs backend + frontend dependencies and
// creates .env files from the examples if they don't exist yet.
// Run from the project root with: npm run setup
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');

for (const app of ['backend', 'frontend']) {
  const dir = path.join(root, app);
  const env = path.join(dir, '.env');
  const example = path.join(dir, '.env.example');
  if (!fs.existsSync(env) && fs.existsSync(example)) {
    fs.copyFileSync(example, env);
    console.log(`Created ${app}/.env from ${app}/.env.example`);
  }
  console.log(`\nInstalling ${app} dependencies...`);
  execSync('npm install', { cwd: dir, stdio: 'inherit' });
}

console.log('\nSetup complete. Make sure MongoDB is running (or set MONGO_URI in');
console.log('backend/.env to a MongoDB Atlas URL), then run:');
console.log('  npm run seed   # load demo data (optional)');
console.log('  npm run dev    # start backend + frontend');
