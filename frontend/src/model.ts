export type Row = Record<string, unknown>;
export interface State {
  environment_id: 'INTERNAL_PAPER'; live_enabled: false;
  instrument: {inst_id:string; source:string; settle_ccy:string; contract_btc:string; expiry:string|null}|null;
  quote: {last:string; bid:string; ask:string; source:string; timestamp:string}|null;
  account: {cash:string; quantity:string; average_price:string; fees:string; funding:string; realized_pnl:string; kill_switch:boolean; strategy_enabled:boolean};
  equity:string|null; unrealized_pnl:string|null; notional:string|null; leverage:string|null; drawdown:string|null;
  feed_age_seconds:number|null; risk_flags:string[]; reason:string;
  orders:Row[]; fills:Row[]; decisions:Row[];
  history:{timestamp:string;price:string;equity:string}[];
  assumptions:Record<string,string>;
  system:{version:string;uptime_seconds:number;database:boolean;reconciled:boolean;feed_message:string;feed:Record<string,unknown>};
}
export const number = (value:unknown, digits=2):string => value === null || value === undefined || !Number.isFinite(Number(value)) ? '—' : Number(value).toLocaleString('en-US',{minimumFractionDigits:digits,maximumFractionDigits:digits});
export function rangeHistory(history:State['history'], range:string):State['history'] {
  const seconds = range==='5M'?300:range==='15M'?900:3600;
  const newest = history.at(-1);
  if(!newest) return [];
  const cutoff = Date.parse(newest.timestamp)-seconds*1000;
  return history.filter(x=>Date.parse(x.timestamp)>=cutoff);
}
export const rowsFor = (state:State, page:string):Row[] => page==='Orders'?state.orders:page==='Positions'?(Number(state.account.quantity)!==0?[{instrument:state.instrument?.inst_id,...state.account,unrealized_pnl:state.unrealized_pnl}]:[]):page==='Analytics'?state.fills:state.decisions;
