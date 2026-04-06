import { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import './App.css';

const API_URL = 'https://cb96-93-159-3-156.ngrok-free.app/api';

function App() {
   const [contacts, setContacts] = useState([]);
   const [debugInfo, setDebugInfo] = useState('Загрузка...');

   // === ФУНКЦИЯ ЗАГРУЗКИ (ОНА ТУТ) ===
   const fetchContacts = async () => {
      try {
         const response = await fetch(`${API_URL}/contacts`, {
            headers: { 'ngrok-skip-browser-warning': 'true' },
         });
         const data = await response.json();
         setContacts(data);

         // Показываем версию API Телеграма, чтобы понять, почему кнопка может не работать
         const version = window.Telegram?.WebApp?.version || 'не определена';
         setDebugInfo(`Версия API Telegram: ${version}`);
      } catch (e) {
         setDebugInfo(`Ошибка сети: ${e.message}`);
      }
   };

   // Выполняется один раз при запуске приложения
   // Инициализация при запуске
   useEffect(() => {
      // 1. Сообщаем Телеграму, что приложение готово
      WebApp.ready();
      WebApp.expand();

      // 2. Вызываем загрузку контактов
      const loadInitialData = async () => {
         await fetchContacts();
      };

      loadInitialData();

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, []);

   // Функция выбора контакта
   const importFromTelegram = () => {
      const tg = window.Telegram?.WebApp;

      if (!tg || !tg.showContactPicker) {
         setDebugInfo(
            `Метод showContactPicker недоступен (Версия: ${tg?.version})`
         );
         return;
      }

      tg.showContactPicker((result) => {
         if (!result?.users?.[0]) return;

         const user = result.users[0];
         const newContact = {
            name: `${user.first_name || ''} ${user.last_name || ''}`.trim(),
            phone: user.phone_number || '',
            time: new Date().toLocaleTimeString([], {
               hour: '2-digit',
               minute: '2-digit',
            }),
         };

         // Отправка на бэкенд
         fetch(`${API_URL}/contacts`, {
            method: 'POST',
            headers: {
               'Content-Type': 'application/json',
               'ngrok-skip-browser-warning': 'true',
            },
            body: JSON.stringify(newContact),
         })
            .then(() => {
               fetchContacts(); // <--- Перезагружаем список после добавления!
               tg.HapticFeedback?.notificationOccurred('success');
            })
            .catch((err) => setDebugInfo(`Ошибка сохранения: ${err.message}`));
      });
   };

   return (
      <div className="app-container">
         {/* Плашка с версией API сверху */}
         <div
            className="debug-header"
            style={{ padding: '5px', fontSize: '11px', color: '#666' }}
         >
            {debugInfo}
         </div>

         <div className="list-area">
            {contacts.length === 0 ? (
               <p className="empty-msg">Список пуст</p>
            ) : (
               contacts.map((c) => (
                  <div key={c.id} className="contact-card">
                     <div className="contact-info">
                        <strong>{c.name}</strong>
                        <span>Звонков: {c.calls || 0}</span>
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

         <div className="footer">
            <button className="import-btn" onClick={importFromTelegram}>
               👥 Добавить из Telegram
            </button>
         </div>
      </div>
   );
}

export default App;
