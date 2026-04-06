import { useState, useEffect, useCallback } from 'react';
import './App.css';

const API_URL = 'https://cb96-93-159-3-156.ngrok-free.app/api';

function App() {
   const [contacts, setContacts] = useState([]);
   const [debug, setDebug] = useState('Готов к работе');

   const fetchContacts = useCallback(async () => {
      try {
         const response = await fetch(`${API_URL}/contacts`, {
            headers: { 'ngrok-skip-browser-warning': 'true' },
         });
         const data = await response.json();
         setContacts(data);
      } catch (e) {
         setDebug(`Ошибка связи: ${e.message}`);
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

   // ТОТ САМЫЙ МЕТОД ВЫБОРА
   const handleImport = () => {
      const tg = window.Telegram?.WebApp;

      if (!tg) {
         setDebug('Ошибка: Запустите в Telegram!');
         return;
      }

      setDebug('Открываю контакты...');

      // Используем встроенный метод выбора
      tg.showContactPicker((result) => {
         // Если пользователь отменил или список пуст
         if (!result || !result.users || result.users.length === 0) {
            setDebug('Выбор отменен');
            return;
         }

         const user = result.users[0];
         const newContact = {
            name:
               `${user.first_name || ''} ${user.last_name || ''}`.trim() ||
               'Без имени',
            phone: user.phone_number || '000',
            time: new Date().toLocaleTimeString([], {
               hour: '2-digit',
               minute: '2-digit',
            }),
         };

         // Сразу отправляем в базу
         fetch(`${API_URL}/contacts`, {
            method: 'POST',
            headers: {
               'Content-Type': 'application/json',
               'ngrok-skip-browser-warning': 'true',
            },
            body: JSON.stringify(newContact),
         })
            .then(() => {
               setDebug(`Добавлен: ${newContact.name}`);
               fetchContacts(); // Обновляем список на экране
               tg.HapticFeedback?.notificationOccurred('success');
            })
            .catch((err) => setDebug(`Ошибка сохранения: ${err.message}`));
      });
   };

   return (
      <div className="app-container">
         <div className="status-bar">{debug}</div>

         <div className="list-area">
            {contacts.length === 0 ? (
               <div className="empty-state">
                  <p>У вас еще нет контактов для прозвона</p>
                  <p style={{ fontSize: '12px', color: '#888' }}>
                     Нажмите кнопку ниже, чтобы выбрать из телефонной книги
                  </p>
               </div>
            ) : (
               contacts.map((c) => (
                  <div key={c.id} className="contact-card">
                     <div className="contact-info">
                        <strong>{c.name}</strong>
                        <span className="phone">{c.phone}</span>
                        <span className="stats">Звонков: {c.calls || 0}</span>
                     </div>
                     <button
                        className="call-btn"
                        onClick={() =>
                           (window.location.href = `tel:${c.phone}`)
                        }
                     >
                        📞
                     </button>
                  </div>
               ))
            )}
         </div>

         <div className="footer-fixed">
            <button className="main-import-btn" onClick={handleImport}>
               👥 ВЫБРАТЬ ИЗ КОНТАКТОВ TELEGRAM
            </button>
         </div>
      </div>
   );
}

export default App;
