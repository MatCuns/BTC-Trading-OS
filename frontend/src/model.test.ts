import {describe,it,expect} from 'vitest';
import {number,rangeHistory} from './model';
describe('honest terminal values',()=>{
  it('does not invent missing KPI values',()=>{expect(number(null)).toBe('—');expect(number(undefined)).toBe('—');expect(number('0')).toBe('0.00')});
  it('filters observed history relative to the latest quote',()=>{const h=[{timestamp:'2026-01-01T10:00:00Z',price:'1',equity:'2'},{timestamp:'2026-01-01T10:10:00Z',price:'3',equity:'4'}];expect(rangeHistory(h,'5M')).toHaveLength(1);expect(rangeHistory(h,'15M')).toHaveLength(2)});
});
