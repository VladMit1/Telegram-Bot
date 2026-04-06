import { useState, useEffect, useCallback } from 'react';
import './App.css';

// ВАЖНО: Убедись, что ссылка актуальна!
const API_URL = 'https://cb96-93-159-3-156.ngrok-free.app/api';

function App() {
   const [contacts, setContacts] = useState([]);
   const [debugInfo, setDebugInfo] = useState('Инициализация...');

   // Достаем объект Telegram напрямую из окна браузера
   const tg = window.Telegram?.WebApp;

   // 1. Функция загрузки списка (вынесена в useCallback для стабильности)
   const fetchContacts = useCallback(async () => {
      try {
         const response = await fetch(`${API_URL}/contacts`, {
            headers: { 'ngrok-skip-browser-warning': 'true' },
         });

         if (!response.ok) throw new Error(`Ошибка: ${response.status}`);

         const data = await response.json();
         setContacts(data);

         const version = tg?.version || 'не найдена';
         setDebugInfo(`Версия API: ${version}`);
      } catch (e) {
         setDebugInfo(`Ошибка сети: ${e.message}`);
         console.error(e);
      }
   }, [tg]);

   // 2. Эффект при запуске
   useEffect(() => {
      if (tg) {
         tg.ready();
         tg.expand();
      }

      // Вызываем загрузку данных
      fetchContacts();
   }, [tg, fetchContacts]);

   // 3. Функция выбора контакта из Telegram
   const importFromTelegram = () => {
      const tg = window.Telegram?.WebApp;
      // Проверяем наличие метода напрямую, а не через цифры версии
      if (tg && tg.requestContact) {
         setDebugInfo('Открываю список контактов...');
         setDebugInfo(
            'Открываю список requestContact...',
            typeof tg?.requestContact
         );
         setDebugInfo(
            'Открываю список showContactPicker...',
            typeof tg?.showContactPicker
         );
         setDebugInfo('Открываю список onEvent...', typeof tg?.onEvent);

         tg.requestContact((result) => {
            // Если пользователь закрыл окно или не выбрал контакт
            if (!result || !result.users || result.users.length === 0) {
               setDebugInfo('Контакт не выбран');
               return;
            }

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
               .then((res) => {
                  if (!res.ok) throw new Error('Ошибка сервера');
                  return res.json();
               })
               .then(() => {
                  fetchContacts(); // Обновляем список на экране
                  setDebugInfo('Контакт успешно добавлен!');
                  if (tg.HapticFeedback)
                     tg.HapticFeedback.notificationOccurred('success');
               })
               .catch((err) => {
                  setDebugInfo(`Ошибка сохранения: ${err.message}`);
               });
         });
      } else {
         setDebugInfo(
            'Критическая ошибка: Метод showContactPicker не найден в SDK'
         );
      }
   };

   // 4. Логика звонка
   const handleCall = (contact) => {
      if (contact.phone) {
         window.location.href = `tel:${contact.phone}`;

         // Отправляем статистику на бэкенд
         fetch(`${API_URL}/call/${contact.id}`, {
            method: 'POST',
            headers: { 'ngrok-skip-browser-warning': 'true' },
         }).then(() => fetchContacts());
      }
   };

   return (
      <div className="app-container">
         {/* Отладочная информация сверху */}
         <div
            className="debug-bar"
            style={{
               fontSize: '10px',
               color: '#888',
               textAlign: 'center',
               padding: '5px',
            }}
         >
            {debugInfo}
         </div>

         <div className="list-area">
            {contacts.length === 0 ? (
               <p className="empty-msg">Список контактов пуст</p>
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
            <button className="import-btn" onClick={importFromTelegram}>
               👥 Добавить из Telegram
            </button>
         </div>
      </div>
   );
}

export default App;
