import {test,expect} from '@playwright/test';
import {randomUUID} from 'node:crypto';

test.beforeEach(async({request})=>{
  const headers={'X-BTC-OS':'paper-terminal'};
  await request.post('/api/paper/controls',{headers,data:{kill_switch:true,strategy_enabled:false}});
  await request.post('/api/paper/target',{headers,data:{client_id:randomUUID().replaceAll('-',''),target:0}});
  await expect.poll(async()=>Number((await (await request.get('/api/state')).json()).account.quantity),{timeout:10000}).toBe(0);
});

test('real backend state, navigation and accessible controls',async({page},info)=>{
  await page.goto('/');
  await expect(page.getByText('SYNTHETIC FIXTURE · Offline simulation.',{exact:false})).toBeVisible();
  await expect(page.getByRole('button',{name:'Unlock PAPER execution'})).toBeVisible();
  await page.getByRole('button',{name:'Unlock PAPER execution'}).click();
  await expect(page.getByRole('button',{name:'Engage kill switch'})).toBeVisible();
  await page.getByRole('button',{name:'Submit PAPER target'}).click();
  await expect(page.getByText('Target 0.25x; PAPER simulation').first()).toBeVisible();
  await page.getByRole('button',{name:'Orders',exact:true}).click();
  await expect(page.getByRole('columnheader',{name:/client id/i})).toBeVisible();
  await expect(page.getByRole('cell',{name:/FIXTURE-BTC-LINEAR/}).first()).toBeVisible();
  await page.getByRole('button',{name:'Settings',exact:true}).click();
  await expect(page.getByText('Runtime assumptions')).toBeVisible();
  await page.getByRole('button',{name:'Overview',exact:true}).click();
  await page.getByRole('button',{name:'Engage kill switch'}).click();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  await page.screenshot({path:`test-results/terminal-${info.project.name}.png`,fullPage:true});
});
