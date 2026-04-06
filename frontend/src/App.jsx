import { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import './App.css';

// URL твоего бэкенда (пока локально, потом заменим на домен)
const API_URL = 'http://localhost:8000/api';

function App() {
   const [name, setName] = useState('');
   const [contacts, setContacts] = useState([]);
   const [callTarget, setCallTarget] = useState(null);

   // 1. Загрузка контактов с бэкенда
   const fetchContacts = async () => {
      try {
         const response = await fetch(`${API_URL}/contacts`);
         const data = await response.json();
         setContacts(data);
      } catch (e) {
         console.error('Ошибка связи с бэкендом:', e);
      }
   };

   useEffect(() => {
      fetchContacts();
      WebApp.ready();
   }, []);

   // 2. Логика звонка и счетчика
   const handleCall = (contact) => {
      setCallTarget(contact);
   };

   useEffect(() => {
      if (!callTarget) return;

      const doCall = async () => {
         try {
            await fetch(`${API_URL}/call/${callTarget.id}`, { method: 'POST' });
            fetchContacts();
         } catch (e) {
            console.error('Не удалось обновить счетчик', e);
         } finally {
            window.location.href = `tel:${callTarget.phone || ''}`;
            setCallTarget(null);
         }
      };

      doCall();
   }, [callTarget]);

   const handleAdd = () => {
      if (!name.trim()) return;
      const data = {
         name,
         time: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
         }),
      };
      WebApp.sendData(JSON.stringify(data));
   };

   return (
      <div className="app-container">
         <div className="list-area">
            {contacts.length === 0 ? (
               <p className="empty-msg">История пуста</p>
            ) : (
               contacts.map((c, i) => (
                  <div key={i} className="contact-card">
                     <div className="contact-info">
                        <strong>{c.name}</strong>
                        <span>Звонков: {c.calls}</span>
                     </div>
                     <button className="call-btn" onClick={() => handleCall(c)}>
                        📞
                     </button>
                  </div>
               ))
            )}
         </div>

         <div className="footer">
            <input
               type="text"
               value={name}
               onChange={(e) => setName(e.target.value)}
               placeholder="Имя контакта..."
            />
            <button className="add-btn" onClick={handleAdd}>
               ➕ Добавить
            </button>
         </div>
      </div>
   );
}

export default App;
