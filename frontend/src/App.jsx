import { useState, useEffect, useCallback } from 'react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL;

console.log("🚀 ~ API_URL:", API_URL)

function App() {
   const [contacts, setContacts] = useState([]);

   const fetchContacts = useCallback(async () => {
      const res = await fetch(`${API_URL}/contacts?t=${Date.now()}`, {
         headers: { 'ngrok-skip-browser-warning': 'true' },
      });
      const data = await res.json();
      setContacts(data);
   }, []);

   const deleteContact = async (id) => {
      await fetch(`${API_URL}/contacts/${id}`, {
         method: 'DELETE',
         headers: { 'ngrok-skip-browser-warning': 'true' },
      });
      setContacts((prev) => prev.filter((c) => c.id !== id));
   };

   useEffect(() => {
      if (window.Telegram?.WebApp) {
         window.Telegram.WebApp.ready();
         window.Telegram.WebApp.expand();
      }
      const initialize = async () => {
         if (window.Telegram?.WebApp) {
            fetchContacts();
         }
      };
      initialize();
   }, [fetchContacts]);

   return (
      <div className="container">
         <div className="header">
            <h3>Ученики ({contacts.length})</h3>
            <button onClick={fetchContacts}>🔄</button>
         </div>
         <div className="list">
            {contacts.map((c) => (
               <div key={c.id} className="card">
                  <div className="info">
                     <strong>{c.name}</strong>
                     <span>{c.phone}</span>
                  </div>
                  <div className="actions">
                     <button
                        className="del-btn"
                        onClick={() => deleteContact(c.id)}
                     >
                        🗑️
                     </button>
                     <a href={`tel:${c.phone}`} className="call-btn">
                        📞
                     </a>
                  </div>
               </div>
            ))}
         </div>
      </div>
   );
}
export default App;
