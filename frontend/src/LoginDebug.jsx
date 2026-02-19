import React, { useState } from 'react';
import api from './api';

export default function LoginDebug() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [logs, setLogs] = useState([]);

    const addLog = (msg) => {
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
    };

    const testSignup = async () => {
        addLog(`=== SIGNUP TEST ===`);
        addLog(`Email: "${email}"`);
        addLog(`Email length: ${email.length}`);
        addLog(`Email bytes: ${Array.from(new TextEncoder().encode(email)).join(',')}`);
        addLog(`Password: "${password}"`);
        addLog(`Password length: ${password.length}`);
        addLog(`Password bytes: ${Array.from(new TextEncoder().encode(password)).join(',')}`);
        
        try {
            const result = await api.post('/auth/signup', { email, password });
            addLog(`✅ Signup SUCCESS: ${JSON.stringify(result)}`);
        } catch (e) {
            addLog(`❌ Signup FAILED: ${e.message}`);
        }
    };

    const testLogin = async () => {
        addLog(`=== LOGIN TEST ===`);
        addLog(`Email: "${email}"`);
        addLog(`Email length: ${email.length}`);
        addLog(`Email bytes: ${Array.from(new TextEncoder().encode(email)).join(',')}`);
        addLog(`Password: "${password}"`);
        addLog(`Password length: ${password.length}`);
        addLog(`Password bytes: ${Array.from(new TextEncoder().encode(password)).join(',')}`);
        
        try {
            const result = await api.login(email, password);
            addLog(`✅ Login SUCCESS: ${JSON.stringify(result)}`);
        } catch (e) {
            addLog(`❌ Login FAILED: ${e.message}`);
        }
    };

    const testBoth = async () => {
        setLogs([]);
        await testSignup();
        await new Promise(resolve => setTimeout(resolve, 500));
        await testLogin();
    };

    return (
        <div style={{ maxWidth: '800px', margin: '50px auto', padding: '20px', fontFamily: 'monospace' }}>
            <h1>Login Debug Tool</h1>
            
            <div style={{ marginBottom: '20px' }}>
                <div style={{ marginBottom: '10px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Email:</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => {
                            const val = e.target.value;
                            setEmail(val);
                            console.log('Email onChange:', val, 'Length:', val.length, 'Bytes:', Array.from(new TextEncoder().encode(val)));
                        }}
                        onPaste={(e) => {
                            console.log('Email PASTE event:', e.clipboardData.getData('text'));
                        }}
                        style={{ width: '100%', padding: '8px', fontSize: '14px' }}
                        autoComplete="off"
                    />
                </div>
                
                <div style={{ marginBottom: '10px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Password:</label>
                    <input
                        type="text"
                        value={password}
                        onChange={(e) => {
                            const val = e.target.value;
                            setPassword(val);
                            console.log('Password onChange:', val, 'Length:', val.length, 'Bytes:', Array.from(new TextEncoder().encode(val)));
                        }}
                        onPaste={(e) => {
                            console.log('Password PASTE event:', e.clipboardData.getData('text'));
                        }}
                        style={{ width: '100%', padding: '8px', fontSize: '14px' }}
                        autoComplete="off"
                    />
                    <small>Using type="text" to see actual password value</small>
                </div>
            </div>
            
            <div style={{ marginBottom: '20px' }}>
                <button onClick={testBoth} style={{ padding: '10px 20px', marginRight: '10px' }}>
                    Test Signup + Login
                </button>
                <button onClick={testSignup} style={{ padding: '10px 20px', marginRight: '10px' }}>
                    Test Signup Only
                </button>
                <button onClick={testLogin} style={{ padding: '10px 20px', marginRight: '10px' }}>
                    Test Login Only
                </button>
                <button onClick={() => setLogs([])} style={{ padding: '10px 20px' }}>
                    Clear Logs
                </button>
            </div>
            
            <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '5px', maxHeight: '400px', overflow: 'auto' }}>
                <h3>Debug Logs:</h3>
                {logs.length === 0 && <div>No logs yet. Enter credentials and click a test button.</div>}
                {logs.map((log, i) => (
                    <div key={i} style={{ marginBottom: '5px', fontSize: '12px' }}>
                        {log}
                    </div>
                ))}
            </div>
            
            <div style={{ marginTop: '20px', background: '#fff3cd', padding: '15px', borderRadius: '5px' }}>
                <h4>Instructions:</h4>
                <ol>
                    <li>Use a fresh email like: testdebug{Math.floor(Math.random()*10000)}@example.com</li>
                    <li>Use a simple password like: Password123</li>
                    <li>Click "Test Signup + Login"</li>
                    <li>Check the debug logs below</li>
                    <li>Also check the browser Console (F12) for detailed byte-level logging</li>
                </ol>
            </div>
        </div>
    );
}
