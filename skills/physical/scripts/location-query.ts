import { $ } from 'bun';
import { existsSync, readFileSync } from 'fs';
import { homedir } from 'os';

// Usage: bun location-query.ts [username] [mode]
const args = process.argv.slice(2);
const explicitUser = args[0] && !['all', 'current', 'time'].includes(args[0]) ? args[0] : null;
const MODE = args.find(a => ['all', 'current', 'time'].includes(a)) || 'all';

// Resolve username + repo
let USERNAME: string;
let REPO: string;

if (explicitUser) {
  USERNAME = explicitUser;
  REPO = `zirz1911/${USERNAME.charAt(0).toUpperCase() + USERNAME.slice(1)}-Location`;
} else {
  // Read local config first
  const configPath = `${homedir()}/.claude/skills/physical/config.json`;
  if (existsSync(configPath)) {
    const cfg = JSON.parse(readFileSync(configPath, 'utf8'));
    USERNAME = cfg.username;
    REPO = cfg.repo;
  } else {
    // Fallback to paji
    USERNAME = 'paji';
    REPO = 'zirz1911/Paji-Location';
  }
}

async function fetchCsv(filename: string): Promise<string> {
  const response = await $`gh api repos/${REPO}/contents/${filename} --jq '.content' | base64 -d`.text();
  return response;
}

if (MODE === 'current' || MODE === 'all') {
  const current = await fetchCsv('current.csv');
  console.log(current);
}

if (MODE === 'time' || MODE === 'all') {
  console.log('---TIME_AT_LOCATION---');
  const history = await fetchCsv('history.csv');

  const lines = history.trim().split('\n').slice(1);
  const records = lines.map(line => {
    const cols = line.split(',');
    if (cols.length < 4) return null;
    return { timestamp: new Date(cols[3]), device: cols[6] || 'phone' };
  }).filter(r => r && !isNaN(r!.timestamp.getTime()));

  if (records.length > 0) {
    records.sort((a, b) => a!.timestamp.getTime() - b!.timestamp.getTime());
    const firstSeen = records[0]!.timestamp;
    const lastSeen = records[records.length - 1]!.timestamp;
    const hoursHere = ((lastSeen.getTime() - firstSeen.getTime()) / (1000 * 60 * 60)).toFixed(1);
    console.log(`first_seen = ${firstSeen.toISOString().replace('T', ' ').slice(0, 19)}`);
    console.log(`last_seen = ${lastSeen.toISOString().replace('T', ' ').slice(0, 19)}`);
    console.log(`records = ${records.length}`);
    console.log(`hours_here = ${hoursHere}`);
  } else {
    console.log('No records found in history.');
  }
}
