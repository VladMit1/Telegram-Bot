import { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import './App.css';

const API_URL = 'http://localhost:8000/api'; // Не забудь заменить на ngrok URL!

function App() {
   const [name, setName] = useState('');
   const [contacts, setContacts] = useState([]);

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

   useEffect(() => {
      WebApp.ready();
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
         </div>
      </div>
   );
}

export default App;
