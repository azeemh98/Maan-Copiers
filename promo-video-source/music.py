import numpy as np, wave
SR=44100; D=56.0; N=int(SR*D); t=np.arange(N)/SR
out=np.zeros(N)
bpm=104; beat=60/bpm; bar=beat*4
f=lambda m:440*2**((m-69)/12)
chords=[[60,64,67],[57,60,64],[53,57,60],[55,59,62]]  # C Am F G
def env(n,a,d):
    e=np.ones(n); A=int(a*SR); e[:A]=np.linspace(0,1,A) if A>0 else 1
    e*=np.exp(-np.arange(n)/SR/d); return e
def add(start,sig):
    i=int(start*SR); j=min(N,i+len(sig)); 
    if i<N: out[i:j]+=sig[:j-i]
# pad
nb=int(D/bar)+1
for b in range(nb):
    ch=chords[b%4]; n=int(bar*SR); tt=np.arange(n)/SR
    s=sum(np.sin(2*np.pi*f(m)*tt)+.3*np.sin(2*np.pi*f(m)*2*tt) for m in ch)/3
    e=np.minimum(1,tt/.4)*np.minimum(1,(bar-tt)/.4)
    add(b*bar,.10*s*e)
    # bass
    bs=np.sin(2*np.pi*f(ch[0]-24)*tt)*np.exp(-tt/1.2)*.22
    add(b*bar,bs); add(b*bar+2*beat,bs[:int(2*beat*SR)]*.8)
    # pluck arpeggio 8ths (start after 0.6s)
    arp=[ch[0]+12,ch[1]+12,ch[2]+12,ch[1]+12+12*0, ch[2]+12, ch[0]+24, ch[2]+12, ch[1]+12]
    for k,m in enumerate(arp):
        st=b*bar+k*beat/2; n2=int(.5*SR); t2=np.arange(n2)/SR
        p=(np.sin(2*np.pi*f(m)*t2)+.4*np.sin(2*np.pi*f(m)*3*t2))*np.exp(-t2/.18)
        add(st,.07*p)
# drums from 4.2s
rng=np.random.default_rng(1)
for k in range(int(D/beat)):
    st=k*beat
    if st<4.0 or st>D-1.5: continue
    if k%2==0:
        n=int(.25*SR); tt=np.arange(n)/SR; fr=50+90*np.exp(-tt/.03)
        add(st,.5*np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-tt/.09))
    else:
        n=int(.2*SR); tt=np.arange(n)/SR
        add(st,.12*rng.standard_normal(n)*np.exp(-tt/.05))  # soft snare/clap
    n=int(.05*SR); hh=rng.standard_normal(n); hh=np.diff(hh,prepend=0)*np.exp(-np.arange(n)/SR/.012)
    add(st+beat/2,.06*hh)
# sfx
def whoosh(st):
    n=int(.45*SR); x=rng.standard_normal(n); x=np.convolve(x,np.ones(8)/8,'same')
    e=np.sin(np.pi*np.arange(n)/n)**2; add(st-.2,.18*x*e)
def ding(st,m=84):
    n=int(1.0*SR); tt=np.arange(n)/SR
    add(st,.22*(np.sin(2*np.pi*f(m)*tt)+.5*np.sin(2*np.pi*f(m+7)*tt))*np.exp(-tt/.35))
def tap(st):
    n=int(.06*SR); tt=np.arange(n)/SR; add(st,.35*np.sin(2*np.pi*1400*tt)*np.exp(-tt/.01))
for s in [4.2,7.8,11.4,14.6,17.6,34.6,38.0,41.6,45.2,48.2,52.0]: whoosh(s)
for s in [19.9,28.6,29.8,31.1]: tap(s+.2)
for s,m in [(9.4,70),(10.6,66),(33.4,84),(38.5,88),(42.6,84),(45.3,79),(45.7,81),(46.1,83),(46.5,84)]: ding(s,m)
# master
out[:int(.8*SR)]*=np.linspace(0,1,int(.8*SR)); out[-int(2*SR):]*=np.linspace(1,0,int(2*SR))
out=out/np.max(np.abs(out))*.85
w=wave.open('music.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out*32767).astype(np.int16).tobytes()); w.close(); print('ok')
