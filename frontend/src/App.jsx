import { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import './App.css';

// ВАЖНО: Убедись, что этот адрес совпадает с твоим текущим ngrok!
const API_URL = 'https://cb96-93-159-3-156.ngrok-free.app/api';

function App() {
   const [name, setName] = useState('');
   const [contacts, setContacts] = useState([]);
   const [error, setError] = useState(null); // Для отладки прямо в Телеграме

   // 1. Загрузка списка контактов
   const fetchContacts = async () => {
      try {
         const response = await fetch(`${API_URL}/contacts`, {
            method: 'GET',
            headers: {
               'Content-Type': 'application/json',
               'ngrok-skip-browser-warning': 'true', // Пропускаем заглушку ngrok
            },
         });

         if (!response.ok) {
            throw new Error(`Сервер ответил: ${response.status}`);
         }

         const data = await response.json();
         setContacts(data);
         setError(null); // Ошибок нет
      } catch (e) {
         console.error('Ошибка связи:', e);
         setError(`Ошибка: ${e.message}. Проверь ngrok и сервер!`);
      }
   };

   // Инициализация при запуске
   useEffect(() => {
      if (WebApp && WebApp.ready) {
         WebApp.ready();
         WebApp.expand(); // Развернуть на весь экран
      }
      fetchContacts();
   }, []);

   // 2. Логика звонка
   const handleCall = async (contact) => {
      window.location.href = `tel:${contact.phone || ''}`;

      try {
         await fetch(`${API_URL}/call/${contact.id}`, {
            method: 'POST',
            headers: { 'ngrok-skip-browser-warning': 'true' },
         });
         fetchContacts();
      } catch (e) {
         console.error('Счетчик не обновился:', e);
      }
   };

   // 3. Выбор контакта из Telegram (Тот самый 2-й вариант)
  const importFromTelegram = () => {
      const tg = window.Telegram?.WebApp;

      if (tg && tg.version && parseFloat(tg.version) >= 6.9) {
         tg.showContactPicker((result) => {
            if (!result || !result.users || result.users.length === 0) return;

            const user = result.users[0];
            const newContact = {
               name: `${user.first_name || ''} ${user.last_name || ''}`.trim(),
               phone: user.phone_number || '',
               time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            };

            fetch(`${API_URL}/contacts`, {
               method: 'POST',
               headers: {
                  'Content-Type': 'application/json',
                  'ngrok-skip-browser-warning': 'true',
               },
               body: JSON.stringify(newContact),
            })
            .then(() => fetchContacts())
            .catch((err) => setError(`Ошибка: ${err.message}`));
         });
      } else {
         setError(`Версия ${tg?.version || '?'}: метод не поддерживается. Используйте кнопку в боте!`);
      }
   };
   // 4. Ручное добавление (для тестов)
   const handleAdd = async () => {
      if (!name.trim()) return;

      const data = {
         name: name,
         time: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
         }),
         phone: '',
      };

      try {
         await fetch(`${API_URL}/contacts`, {
            method: 'POST',
            headers: {
               'Content-Type': 'application/json',
               'ngrok-skip-browser-warning': 'true',
            },
            body: JSON.stringify(data),
         });
         setName('');
         fetchContacts();
      } catch (e) {
         setError(`Не удалось добавить: ${e.message}`);
      }
   };
   useEffect(() => {
      if (WebApp && WebApp.ready) {
         WebApp.ready();
         // Выведи версию API в консоль или в ошибку для проверки
         console.log('Версия API:', WebApp.version);
         if (parseFloat(WebApp.version) < 6.9) {
            setError(`Версия API ${WebApp.version} слишком стара. Нужно 6.9+`);
         }
      }
      fetchContacts();
   }, []);
   return (
      <div className="app-container">
         {/* Плашка ошибки (видна только если что-то не так) */}
         {error && (
            <div
               style={{
                  background: '#ff4d4f',
                  color: 'white',
                  padding: '10px',
                  fontSize: '12px',
                  textAlign: 'center',
               }}
            >
               {error}
            </div>
         )}

         <div className="list-area">
            {contacts.length === 0 ? (
               <p className="empty-msg">
                  Контактов пока нет. Добавьте первого!
               </p>
            ) : (
               contacts.map((c) => (
                  <div key={c.id} className="contact-card">
                     <div className="contact-info">
                        <strong>{c.name}</strong>
                        <span>Звонков: {c.calls || 0}</span>
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
               placeholder="Имя вручную..."
            />
            <div className="button-group">
               <button className="add-btn" onClick={handleAdd}>
                  ➕
               </button>
               <button className="tg-btn" onClick={importFromTelegram}>
                  👥 Из Telegram
               </button>
            </div>
         </div>
      </div>
   );
}

export default App;
