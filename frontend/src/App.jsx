import { useState } from 'react';
import WebApp from '@twa-dev/sdk';
import './App.css';

function App() {
   const [name, setName] = useState('');

   const handleAdd = () => {
      if (!name.trim()) return;

      const data = {
         name: name,
         time: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
         }),
      };

      // Отправка данных боту
      WebApp.sendData(JSON.stringify(data));
      WebApp.close();
   };

   return (
      <div className="app-container">
         <div className="list-area">
            <p style={{ opacity: 0.5 }}>История будет в чате бота</p>
         </div>

         <div className="footer">
            <button onClick={handleAdd}>➕ Добавить контакт</button>
            <input
               type="text"
               value={name}
               onChange={(e) => setName(e.target.value)}
               placeholder="Введите имя..."
            />
         </div>
      </div>
   );
}

export default App;
