import {describe,it,expect} from 'vitest';
import {percent,millis} from './format';
describe('Honest metric formatting',()=>{it('preserves missing values rather than inventing zero',()=>{expect(percent(null)).toBe('—');expect(millis(undefined)).toBe('—');});it('formats observed values',()=>{expect(percent(.25)).toBe('25.0%');expect(millis(1.234)).toBe('1.23 ms');});});
