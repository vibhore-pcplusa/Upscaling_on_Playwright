import fs from 'fs';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

// Read BASE_URL from process.env or parse from .env file
let baseUrl = process.env.BASE_URL;
if (!baseUrl && fs.existsSync('.env')) {
  const envContent = fs.readFileSync('.env', 'utf8');
  const match = envContent.match(/^BASE_URL=(.+)$/m);
  if (match) baseUrl = match[1].trim();
}
baseUrl = (baseUrl || 'https://dev23.cornerstone2.net').replace(/\/$/, '');
const loginUrl = `${baseUrl}/login`;

async function main() {
  const transport = new StdioClientTransport({
    command: 'npx',
    args: ['-y', '@playwright/mcp@latest']
  });

  const client = new Client(
    { name: 'antigravity-client', version: '1.0.0' },
    { capabilities: {} }
  );

  await client.connect(transport);

  console.log(`Navigating to login (${loginUrl})...`);
  await client.callTool({
    name: 'browser_navigate',
    arguments: { url: loginUrl }
  });


  console.log('Evaluating DOM...');
  const result = await client.callTool({
    name: 'browser_evaluate',
    arguments: { function: '() => { const inputs = Array.from(document.querySelectorAll("input")).map(i => ({id: i.id, name: i.name, type: i.type, class: i.className})); const buttons = Array.from(document.querySelectorAll("button")).map(b => ({id: b.id, type: b.type, text: b.textContent.trim(), class: b.className})); return JSON.stringify({inputs, buttons}); }' }
  });

  console.log(result.content[0].text);

  await client.callTool({
    name: 'browser_close',
    arguments: {}
  });

  process.exit(0);
}

main().catch(console.error);
