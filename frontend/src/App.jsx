import { useState, useEffect, useCallback } from 'react';
import './App.css';

const API_URL = 'https://cb96-93-159-3-156.ngrok-free.app/api'; // ПРОВЕРЬ URL!

function App() {
   const [contacts, setContacts] = useState([]);
   const [debug, setDebug] = useState('Загрузка...');

   const fetchContacts = useCallback(async () => {
      try {
         // Добавляем timestamp (?t=), чтобы браузер не отдавал старые данные
         const response = await fetch(`${API_URL}/contacts?t=${Date.now()}`, {
            headers: { 'ngrok-skip-browser-warning': 'true' },
         });
         const data = await response.json();
         setContacts(data);
         setDebug(data.length > 0 ? `Всего: ${data.length}` : 'Список пуст');
      } catch (error) {
         setDebug('Ошибка API: проверьте ngrok');
         console.error(error);
      }
   }, []);

   useEffect(() => {
      const tg = window.Telegram?.WebApp;
      if (tg) {
         tg.ready();
         tg.expand();
      }

      // Обертываем вызов в асинхронную функцию внутри эффекта,
      // чтобы React не ругался на синхронное изменение стейта
      const init = async () => {
         await fetchContacts();
      };

      init();
   }, [fetchContacts]); // Теперь линтер будет доволен

   return (
      <div className="app">
         <div className="header">
            <span>{debug}</span>
            <button onClick={fetchContacts}>🔄</button>
         </div>

         <div className="list">
            {contacts.map((c) => (
               <div key={c.id} className="card">
                  <div className="info">
                     <strong>{c.name}</strong>
                     <small>{c.phone}</small>
                  </div>
                  <div className="stats">📞 {c.calls}</div>
                  <a href={`tel:${c.phone}`} className="call-link">
                     Позвонить
                  </a>
               </div>
            ))}
         </div>
      </div>
   );
}

export default App;
