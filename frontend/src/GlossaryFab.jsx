import React, { useState } from 'react';

export default function GlossaryFab(){
  const [open, setOpen] = useState(false);
  const terms = [
    {
      k: 'HTTPS',
      v: 'A safer way websites talk. The lock icon. It scrambles data so others cannot read it while it travels.'
    },
    {
      k: 'HSTS',
      v: 'A rule that says “always use the safe (HTTPS) road”. It stops a browser from using the unsafe road by mistake.'
    },
    {
      k: 'CSP (Content Security Policy)',
      v: 'A list of allowed places for scripts/styles. Like a guest list for code. Helps block bad scripts.'
    },
    {
      k: 'X-Frame-Options',
      v: 'Stops other sites from putting this site inside a frame like a picture-in-picture. Helps prevent click tricks.'
    },
    {
      k: 'X-Content-Type-Options',
      v: 'Says “do not guess file types”. The browser must trust the label. Helps avoid sneaky file tricks.'
    },
    {
      k: 'Referrer-Policy',
      v: 'Controls how much of the previous page’s address is shared when you click a link. Less sharing = more privacy.'
    },
    {
      k: 'Server header',
      v: 'What the website tells about the machine or service behind it (like brand/model). Useful, but can reveal too much.'
    },
    {
      k: 'Status code',
      v: 'A short number message. 200 = OK. 301/302 = moved. 403 = blocked. 404 = not found. 500 = website error.'
    },
    {
      k: 'Content-Length',
      v: 'How big the page is (in bytes). Like weight of a parcel.'
    }
  ];

  return (
    <>
      <button
        className="fab-help"
        aria-label="What do these terms mean?"
        onClick={()=>setOpen(true)}
        title="What do these terms mean?"
      >
        ?
      </button>

      {open && (
        <div className="glossary-backdrop" onClick={()=>setOpen(false)}>
          <div className="glossary-modal" onClick={(e)=>e.stopPropagation()}>
            <div className="glossary-header">
              <h3>Security terms in simple words</h3>
              <button className="close-btn" aria-label="Close" onClick={()=>setOpen(false)}>×</button>
            </div>
            <div className="glossary-body">
              {terms.map((t)=> (
                <div className="glossary-item" key={t.k}>
                  <div className="g-term">{t.k}</div>
                  <div className="g-desc">{t.v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
