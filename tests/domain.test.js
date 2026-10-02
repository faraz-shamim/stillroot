import test from 'node:test';
import assert from 'node:assert/strict';
import {decide,parseCSV,portableForecast} from '../web/domain.js';
test('stale and nonfinite readings require sensor verification',()=>{
  assert.equal(decide(80,70,0,true),'VERIFY_SENSOR');
  assert.equal(decide(NaN,30,0),'VERIFY_SENSOR');
});
test('wet soil never asks a friend to water; dry travel forecast asks for a check',()=>{
  assert.equal(decide(80,15,7),'WAIT');
  assert.equal(decide(49,15,7),'ASK_FRIEND');
  assert.equal(decide(49,15,0),'CHECK');
});
test('CSV rejects missing values and accepts zero moisture',()=>{
  const header='moisture,temperature,humidity,light_hours,pot_size,days_since_water,next_moisture';
  const data=[header,...Array(20).fill('0,22,50,4,16,2,0')].join('\n');
  assert.equal(parseCSV(data).length,20);
  assert.throws(()=>parseCSV(data.replace('0,22,',',22,')),/empty/);
});
test('portable estimates stay bounded and never return negative moisture',()=>{
  const rows=Array(20).fill({moisture:40,next_moisture:30,temperature:22,humidity:50,light_hours:4,pot_size:16});
  const p=portableForecast(rows,40,rows[0]);
  assert.equal(p.length,8);
  assert.ok(p.every(v=>v.mean>=0&&v.upper<=100&&v.lower<=v.mean));
});
