// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,cleanup,fireEvent,waitFor} from '@testing-library/react';
import {RootApp} from './main';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
function backend(completed=false,signedIn=true){
  const fetchMock=vi.fn(async(path:string,options?:RequestInit)=>{
    if(path==='/api/auth/status')return {ok:true,status:200,json:async()=>({setup_required:false})};
    if(path==='/api/session')return {ok:signedIn,status:signedIn?200:401,json:async()=>({token:'test-csrf',user:{id:'test-user',username:'researcher',tour_completed:completed}})};
    if(path==='/api/policy')return {ok:true,status:200,json:async()=>({allowed_tools:[]})};
    if(path==='/api/auth/tour')return {ok:true,status:200,json:async()=>({tour_completed:true})};
    return {ok:true,status:200,json:async()=>[]};
  });vi.stubGlobal('fetch',fetchMock);return fetchMock;
}
it('does not load workspace data before sign-in',async()=>{
  const fetchMock=backend(false,false);render(<RootApp/>);
  expect(await screen.findByRole('heading',{name:'Welcome back'})).toBeDefined();
  expect(screen.queryByRole('heading',{name:/^Overview$/})).toBeNull();
  expect(fetchMock.mock.calls.map(c=>c[0])).toEqual(['/api/auth/status','/api/session']);
});
it('automatically tours a new user, navigates all eight steps and persists completion without executing tools',async()=>{
  const fetchMock=backend();render(<RootApp/>);
  expect((await screen.findByRole('dialog')).textContent).toContain('Welcome to your security workspace');
  for(let i=0;i<7;i++)fireEvent.click(screen.getByRole('button',{name:'Next step'}));
  expect(screen.getByRole('dialog').textContent).toContain('Your guide is always here');
  fireEvent.click(screen.getByRole('button',{name:'Finish tour'}));
  await waitFor(()=>expect(screen.queryByRole('dialog')).toBeNull());
  expect(fetchMock.mock.calls.some(c=>c[0]==='/api/auth/tour'&&c[1]?.method==='POST')).toBe(true);
  expect(fetchMock.mock.calls.some(c=>c[0]==='/api/runs'&&c[1]?.method==='POST')).toBe(false);
  expect(fetchMock.mock.calls.some(c=>c[0]==='/api/policy'&&c[1]?.method==='PUT')).toBe(false);
});
it('returns an onboarded user to the overview without forcing the tour again',async()=>{
  backend(true);render(<RootApp/>);
  expect(await screen.findByRole('heading',{name:'Policy decision breakdown'})).toBeDefined();
  expect(screen.queryByRole('dialog')).toBeNull();
});
