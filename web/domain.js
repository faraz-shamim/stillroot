export const ACTIONS = ['WAIT','CHECK','ASK_FRIEND','VERIFY_SENSOR'];
export function decide(moisture, lower, awayDays, stale=false) {
  if (stale || !Number.isFinite(moisture) || !Number.isFinite(lower)) return 'VERIFY_SENSOR';
  if (moisture > 72) return 'WAIT';
  if (lower < 22 && awayDays > 0) return 'ASK_FRIEND';
  if (moisture < 28 || lower < 22) return 'CHECK';
  return 'WAIT';
}
export function parseCSV(text) {
  if (text.length > 200000) throw new Error('Please use a CSV smaller than 200 KB.');
  const lines=text.trim().replace(/\r/g,'').split('\n');
  const header=lines.shift().split(',').map(x=>x.trim().replace(/^\uFEFF/,''));
  const required=['moisture','temperature','humidity','light_hours','pot_size','days_since_water','next_moisture'];
  if(!required.every(k=>header.includes(k))) throw new Error(`CSV needs these columns: ${required.join(', ')}.`);
  if(lines.length<20 || lines.length>1000) throw new Error('Use between 20 and 1,000 history rows.');
  return lines.map((line,i)=>{
    const values=line.split(',');
    if(values.length!==header.length) throw new Error(`Row ${i+2} has a different number of columns.`);
    const row=Object.fromEntries(header.map((key,j)=>[key,Number(values[j].trim())]));
    if(required.some(k=>values[header.indexOf(k)].trim()==='' || !Number.isFinite(row[k]))) throw new Error(`Row ${i+2} contains an empty or nonnumeric value.`);
    if(row.moisture<0 || row.moisture>100 || row.next_moisture<0 || row.next_moisture>100 || row.pot_size<=0 || row.pot_size>100 || row.humidity<0 || row.humidity>100 || row.temperature<0 || row.temperature>60 || row.light_hours<0 || row.light_hours>24 || row.days_since_water<0 || row.days_since_water>365) throw new Error(`Row ${i+2} contains an out-of-range sensor value.`);
    return row;
  });
}
export function portableForecast(rows, current, environment, days=7) {
  // Explicit baseline for arbitrary uploads in the $0 static deployment.
  // Inverse-distance analogues are NOT labeled as TabPFN.
  const features=['moisture','temperature','humidity','light_hours','pot_size'];
  const scales=[30,10,40,8,16];
  const nearest=rows.map(row=>({row,d:features.reduce((sum,key,j)=>sum+((row[key]-(key==='moisture'?current:environment[key]))/scales[j])**2,0)})).sort((a,b)=>a.d-b.d).slice(0,12);
  const drops=nearest.map(({row})=>row.moisture-row.next_moisture).sort((a,b)=>a-b);
  const drop=Math.max(0,drops[Math.floor(drops.length/2)]);
  const spread=Math.max(1.5,(drops[drops.length-1]-drops[0])/2);
  return Array.from({length:days+1},(_,day)=>({day,mean:Math.max(0,current-drop*day),lower:Math.max(0,current-drop*day-spread*Math.sqrt(day)),upper:Math.min(100,current-drop*day+spread*Math.sqrt(day))}));
}
