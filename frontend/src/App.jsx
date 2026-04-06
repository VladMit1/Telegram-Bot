import { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import './App.css';

const API_URL = 'https://cb96-93-159-3-156.ngrok-free.app/api'; // Не забудь заменить на ngrok URL!

function App() {
   const [name, setName] = useState('');
   const [contacts, setContacts] = useState([]);
   console.log('🚀 ~ App ~ contacts:', contacts);

   // Загрузка списка
   const fetchContacts = async () => {
      try {
         const response = await fetch(`${API_URL}/contacts`);
         if (!response.ok) throw new Error('Ошибка сервера');
         const data = await response.json();
         setContacts(data);
      } catch (e) {
         console.error('Ошибка связи:', e);
      }
   };

   // В начале файла

   // Внутри useEffect
   useEffect(() => {
      // Попробуй этот вариант, если .ready() падает
      if (WebApp && WebApp.ready) {
         WebApp.ready();
      } else {
         console.log(
            'WebApp.ready не найден, возможно он не требуется или SDK загружен иначе'
         );
      }
      fetchContacts();
   }, []);

   // ЛОГИКА ЗВОНКА (БЕЗ ЛИШНИХ ЭФФЕКТОВ)
   const handleCall = async (contact) => {
      // 1. Сначала открываем звонилку (чтобы юзер не ждал ответа сервера)
      window.location.href = `tel:${contact.phone || ''}`;

      // 2. Параллельно шлем инфу на бэкенд для статистики
      try {
         await fetch(`${API_URL}/call/${contact.id}`, { method: 'POST' });
         // 3. Обновляем список, чтобы увидеть +1 в счетчике
         fetchContacts();
      } catch (e) {
         console.error('Счетчик не обновился:', e);
      }
   };

   const handleAdd = () => {
      if (!name.trim()) return;

      const data = {
         name: name,
         time: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
         }),
      };

      // Проверка: мы в телеграме или в браузере?
      if (WebApp.initData) {
         WebApp.sendData(JSON.stringify(data));
      } else {
         console.log('Данные для отправки:', data);
         alert('Данные отправлены (эмуляция)');
      }
      setName(''); // Очищаем поле после добавления
   };
   const importFromTelegram = () => {
      // Проверяем, что скрипт Telegram WebApp загружен
      if (window.Telegram?.WebApp) {
         const tg = window.Telegram.WebApp;

         // Вызываем системное окно выбора контактов
         tg.showContactPicker((result) => {
            // result.users — это массив выбранных контактов
            if (result && result.users && result.users.length > 0) {
               const user = result.users[0]; // Берем первого

               const newContact = {
                  name: `${user.first_name} ${user.last_name || ''}`.trim(),
                  phone: user.phone_number,
                  time: new Date().toLocaleTimeString([], {
                     hour: '2-digit',
                     minute: '2-digit',
                  }),
               };

               // Отправляем данные на твой бэкенд (через адрес ngrok!)
               fetch(`${API_URL}/contacts`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(newContact),
               })
                  .then((res) => res.json())
                  .then(() => {
                     fetchContacts(); // Обновляем список на экране, чтобы увидеть новичка
                     tg.HapticFeedback.notificationOccurred('success'); // Виброотклик
                  })
                  .catch((err) => console.error('Ошибка при сохранении:', err));
            }
         });
      } else {
         alert('Эта функция работает только внутри Telegram!');
      }
   };

   // В return добавь кнопку:
   // <button onClick={importFromTelegram} className="add-btn">Добавить из Telegram</button>
   return (
      <div className="app-container">
         <div className="list-area">
            {contacts.length === 0 ? (
               <p className="empty-msg">История пуста</p>
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
               placeholder="Имя контакта..."
            />
            <button className="add-btn" onClick={handleAdd}>
               ➕ Добавить
            </button>
            <button onClick={importFromTelegram} className="add-btn">
               Добавить из Telegram
            </button>
         </div>
      </div>
   );
}

export default App;
