import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./e2e',use:{baseURL:'http://127.0.0.1:8765'},webServer:{command:'../.venv/bin/python -m btc_os',url:'http://127.0.0.1:8765/api/health',reuseExistingServer:!process.env.CI},projects:[{name:'desktop',use:{viewport:{width:1920,height:1080}}},{name:'mobile',use:{viewport:{width:390,height:844}}}]});
