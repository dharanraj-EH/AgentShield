// @vitest-environment jsdom
import {afterEach,describe,it,expect,vi} from 'vitest';
import {render,screen,cleanup,fireEvent,waitFor} from '@testing-library/react';
import {Login} from './Login';
import {Tour} from './Tour';
import {UserGuide,TOUR_STEPS} from './UserGuide';

afterEach(()=>{cleanup();vi.unstubAllGlobals();});
describe('Account access',()=>{
  it('refuses mismatched confirmation without submitting credentials',async()=>{
    const fetchMock=vi.fn();vi.stubGlobal('fetch',fetchMock);
    render(<Login setup onLogin={vi.fn()}/>);
    fireEvent.change(screen.getByLabelText('Username'),{target:{value:'researcher'}});
    fireEvent.change(screen.getByLabelText('Password',{exact:true}),{target:{value:'Test-passphrase-1234'}});
    fireEvent.change(screen.getByLabelText('Confirm password'),{target:{value:'different-value'}});
    fireEvent.click(screen.getByRole('button',{name:/Create account/}));
    expect((await screen.findByRole('alert')).textContent).toContain('do not match');
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it('shows an invalid-login error and does not enter the dashboard',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,json:async()=>({detail:'Username or password is incorrect'})}));
    const onLogin=vi.fn();render(<Login setup={false} onLogin={onLogin}/>);
    fireEvent.change(screen.getByLabelText('Username'),{target:{value:'researcher'}});
    fireEvent.change(screen.getByLabelText('Password',{exact:true}),{target:{value:'wrong-password'}});
    fireEvent.click(screen.getByRole('button',{name:/Sign in to workspace/}));
    expect((await screen.findByRole('alert')).textContent).toContain('incorrect');expect(onLogin).not.toHaveBeenCalled();
  });
  it('passes only a successful server-authenticated session to the app',async()=>{
    const user={id:'test',username:'researcher',tour_completed:false};
    const fetchMock=vi.fn().mockResolvedValue({ok:true,json:async()=>({user,token:'test-csrf'})});vi.stubGlobal('fetch',fetchMock);
    const onLogin=vi.fn();render(<Login setup={false} onLogin={onLogin}/>);
    fireEvent.change(screen.getByLabelText('Username'),{target:{value:'researcher'}});
    fireEvent.change(screen.getByLabelText('Password',{exact:true}),{target:{value:'Test-only-passphrase'}});
    fireEvent.click(screen.getByRole('button',{name:/Sign in to workspace/}));
    await waitFor(()=>expect(onLogin).toHaveBeenCalledWith(user,'test-csrf'));
    expect(fetchMock.mock.calls[0][0]).toBe('/api/auth/login');
  });
});
describe('Guided learning',()=>{
  it('has eight contextual steps and never executes a tool itself',()=>{
    const fetchMock=vi.fn();vi.stubGlobal('fetch',fetchMock);const next=vi.fn();
    const {rerender}=render(<Tour step={0} onNext={next} onBack={vi.fn()} onLater={vi.fn()}/>);
    expect(screen.getByRole('dialog').getAttribute('aria-labelledby')).toBe('tour-title');
    expect(screen.getByRole('button',{name:'Back'}).hasAttribute('disabled')).toBe(true);
    fireEvent.click(screen.getByRole('button',{name:'Next step'}));expect(next).toHaveBeenCalledOnce();
    rerender(<Tour step={TOUR_STEPS.length-1} onNext={next} onBack={vi.fn()} onLater={vi.fn()}/>);
    expect(screen.getByRole('button',{name:'Finish tour'})).toBeDefined();expect(TOUR_STEPS).toHaveLength(8);expect(fetchMock).not.toHaveBeenCalled();
  });
  it('can defer a tour using Escape without marking it complete',()=>{
    const later=vi.fn();render(<Tour step={1} onNext={vi.fn()} onBack={vi.fn()} onLater={later}/>);
    fireEvent.keyDown(screen.getByRole('dialog'),{key:'Escape'});expect(later).toHaveBeenCalledOnce();
  });
  it('guide opens the correct safe scenario and can replay the tour',()=>{
    const navigate=vi.fn(),replay=vi.fn();render(<UserGuide navigate={navigate} replay={replay}/>);
    fireEvent.click(screen.getAllByRole('button',{name:'Open agent laboratory'})[0]);expect(navigate).toHaveBeenCalledWith('Agent laboratory','summary');
    fireEvent.click(screen.getByRole('button',{name:'Take the guided tour'}));expect(replay).toHaveBeenCalledOnce();
    expect(screen.getByText(/Passwords are case-sensitive/)).toBeDefined();
  });
});
