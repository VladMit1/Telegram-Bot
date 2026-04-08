import { useState, useEffect, useCallback } from 'react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL;

function App() {
   const [contacts, setContacts] = useState([]);

   const fetchContacts = useCallback(async () => {
      try {
         const res = await fetch(`${API_URL}/contacts?t=${Date.now()}`);
         const data = await res.json();
         setContacts(data);
      } catch (err) {
         console.error('Ошибка загрузки:', err);
      }
   }, []);

   const deleteContact = async (id) => {
      try {
         await fetch(`${API_URL}/contacts/${id}`, {
            method: 'DELETE',
         });
         setContacts((prev) => prev.filter((c) => c.id !== id));
      } catch (err) {
         console.error('Ошибка удаления:', err);
      }
   };

   useEffect(() => {
      if (window.Telegram?.WebApp) {
         const twa = window.Telegram.WebApp;
         twa.ready();
         twa.expand();
      }
      const initialize = async () => {
         if (window.Telegram?.WebApp) {
            await fetchContacts();
         }
      };

      initialize();
   }, [fetchContacts]);

   return (
      <div className="container">
         <div className="header">
            <h3>Список учеников ({contacts.length})</h3>
            <button className="refresh-btn" onClick={fetchContacts}>
               🔄
            </button>
         </div>

         <div className="list">
            {contacts.length === 0 ? (
               <p className="empty-msg">Учеников пока нет</p>
            ) : (
               contacts.map((c) => (
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
                           🗑️ Удалить
                        </button>
                     </div>
                  </div>
               ))
            )}
         </div>
      </div>
   );
}
export default App;
