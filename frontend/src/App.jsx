import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Phone, RefreshCw, Calendar } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL;

function App() {
   const [contacts, setContacts] = useState([]);
   const [loading, setLoading] = useState(true);

   const fetchContacts = useCallback(async () => {
      setLoading(true);
      try {
         const res = await axios.get(`${API_URL}/contacts?t=${Date.now()}`);
         setContacts(res.data);
      } catch (err) {
         console.error('Ошибка загрузки:', err);
      } finally {
         setLoading(false);
      }
   }, []);

   useEffect(() => {
      const twa = window.Telegram?.WebApp;
      if (twa) {
         twa.ready();
         twa.expand();
      }

      // Это должно работать всегда:
      fetchContacts();
   }, [fetchContacts]);

   return (
      <motion.div className="app-container">
         <header className="header">
            <h1>Мои Ученики</h1>
            <button
               className={`refresh-btn ${loading ? 'spinning' : ''}`}
               onClick={fetchContacts}
            >
               <RefreshCw size={20} />
            </button>
         </header>

         <main className="content">
            <AnimatePresence mode="wait">
               {loading ? (
                  <motion.div
                     initial={{ opacity: 0 }}
                     animate={{ opacity: 1 }}
                     exit={{ opacity: 0 }}
                     className="loader"
                  >
                     Загрузка данных...
                  </motion.div>
               ) : (
                  <motion.div
                     className="list"
                     initial={{ y: 20, opacity: 0 }}
                     animate={{ y: 0, opacity: 1 }}
                  >
                     {contacts.length === 0 ? (
                        <p className="empty">Список пуст</p>
                     ) : (
                        contacts.map((c) => (
                           <motion.div key={c.id} className="student-card">
                              <motion.div className="avatar">
                                 <User size={24} />
                              </motion.div>
                              <motion.div className="info">
                                 <h3>{c.name}</h3>
                                 <p>
                                    <Phone size={14} /> {c.phone}
                                 </p>
                              </motion.div>
                              {/* Место для будущей даты занятия */}
                              <motion.div className="next-lesson">
                                 <Calendar size={16} />
                                 <span>--.--</span>
                              </motion.div>
                           </motion.div>
                        ))
                     )}
                  </motion.div>
               )}
            </AnimatePresence>
         </main>
      </motion.div>
   );
}

export default App;
